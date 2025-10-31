#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import errno
import time
import traceback
import platform
import json

import solnlib

from gzip import GzipFile
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from .abort_signal import AbortSignalException
from .filtering import event_based_sourcetype, get_sourcetype_based_time_extractors
from .constants import DEFAULT_EVENT_ENCODING, SERVER_HOST
from .utils import saxescape
from .logger_adapter import CSLoggerAdapter

from typing import Generator, Optional, Union, Tuple, Callable, Dict, Any, List, IO
from splunklib import modularinput as smi

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("ingest_methods")
)
MAX_EW_SEND_WORKERS = 1
MAX_EW_EVENT_CHUNK_SIZE = 1000


EVENT_CHUNK_TEMPLATE = (
    '<event unbroken="1" {stanza}>'
    "<source>{source}</source>"
    "<sourcetype>{sourcetype}</sourcetype>"
    "<host>{host}</host>"
    "<index>{index}</index>"
    "<data>{data}</data>"
    "<done/>"
    "</event>"
)


class EventWriterBrokenPipe(Exception):
    pass


def log_ingest_error(msg: str, e: Exception) -> None:
    tb = " ---> ".join(traceback.format_exc().split("\n"))
    solnlib.log.log_exception(logger, e, "", msg_before=f"{msg} {tb}")


def raw_events(
    file_obj: IO[bytes], encoding: str
) -> Generator[Tuple[str, int], None, None]:
    with GzipFile(mode="r", fileobj=file_obj) as f:
        for line in f:
            yield line.decode(encoding), len(line)


def send_to_pipeline(event_writer: smi.EventWriter, event_chunk: str) -> None:
    event_writer._out.write(event_chunk)
    event_writer._out.flush()


def build_chunk_xml(
    collected: Dict[str, Any], meta: Dict[str, Any], sourcetype_indexes: Dict[str, Any]
) -> str:
    chunk = ""
    event_data = meta.copy()
    for sourcetype, sourcetype_events in collected.items():
        if sourcetype_events:
            event_data["sourcetype"] = saxescape(sourcetype)
            event_data["index"] = saxescape(sourcetype_indexes[sourcetype])
            event_data["data"] = saxescape("".join(sourcetype_events))
            chunk += EVENT_CHUNK_TEMPLATE.format(**event_data)

    return chunk


def event_writer_ingest(
    file_obj: IO[bytes],
    event_writer: smi.EventWriter,
    meta: Dict[str, Any],
    sourcetype_indexes: Dict[str, Any],
    filter_fn: Callable,
    max_chunk_size: int = MAX_EW_EVENT_CHUNK_SIZE,
    stopper_fn: Optional[Callable] = None,
    enrichers: Dict[str, Any] = {},
    raw_event_encoding=DEFAULT_EVENT_ENCODING,
    input_server_host: str = platform.node(),
    logger_prefix: str = "",
) -> Tuple[Union[int, str], Union[int, str], int, List[str], str]:
    input_name = meta["stanza"]
    event_file = meta["source"]
    errors = []
    meta = {k: saxescape(v) for k, v in meta.items()}
    collected = {}
    total, matching, bytes_to_ingest, enriched, sourcetype = 0, 0, 0, 0, None

    def preprocess_and_append(sourcetype: str, raw_event: str) -> int:
        nonlocal collected, enriched

        enricher = enrichers.get(sourcetype) if enrichers else None
        if enricher:
            raw_event_enriched = enricher.enrich(raw_event)
            if raw_event_enriched is not raw_event:
                enriched += 1
                raw_event = raw_event_enriched

        if sourcetype not in collected:
            collected[sourcetype] = []
        collected[sourcetype].append(raw_event)

        return len(bytes(raw_event, "utf-8"))

    def send_collected_chunk_if_ready(
        writer_tasks: ThreadPoolExecutor, threshold: int = 1
    ) -> bool:
        nonlocal collected
        chunk_size = sum([len(el) for el in collected.values()])
        if chunk_size < threshold:
            return False

        nonlocal meta, sourcetype_indexes
        chunk = build_chunk_xml(collected, meta, sourcetype_indexes)
        collected.clear()

        nonlocal matching, event_writer
        matching += chunk_size
        submitted.append(writer_tasks.submit(send_to_pipeline, event_writer, chunk))
        return True

    try:
        send_to_pipeline(event_writer, "<stream>")

        submitted = []
        with ThreadPoolExecutor(max_workers=1) as writer_tasks:
            for raw_event, _ in raw_events(file_obj, raw_event_encoding):
                total += 1

                if stopper_fn and stopper_fn():
                    raise AbortSignalException()

                ingest, sourcetype = filter_fn(raw_event)
                if ingest:
                    if sourcetype is not None:
                        enriched_size = preprocess_and_append(sourcetype, raw_event)
                        bytes_to_ingest += enriched_size
                    else:
                        error_message = f"{logger_prefix} cs_input_stanza={input_name}, attempted to ingest None sourcetype"
                        errors.append(error_message)
                        log_ingest_error(error_message, ValueError("None sourcetype"))

                send_collected_chunk_if_ready(writer_tasks, max_chunk_size)

            send_collected_chunk_if_ready(writer_tasks)

            logger.info(
                f'Sent to pipeline: cs_input_stanza="[{input_name}]@{input_server_host}", '
                f"cs_bytes_sent={bytes_to_ingest}, cs_file_path={event_file}"
            )

            done, _ = wait(submitted, return_when=ALL_COMPLETED)
            for f in done:
                try:
                    f.result()
                except IOError as ioe:
                    errors.append(str(ioe))
                    log_ingest_error(
                        f"{logger_prefix} cs_input_stanza={input_name}, chunk write error: {ioe}",
                        ioe,
                    )
                    if ioe.errno == errno.EPIPE:
                        raise EventWriterBrokenPipe() from ioe
                except Exception as e:
                    errors.append(str(e))
                    log_ingest_error(
                        f"{logger_prefix} cs_input_stanza={input_name}, chunk write error: {e}",
                        e,
                    )
            send_to_pipeline(event_writer, "</stream>")
            if stopper_fn and stopper_fn():
                raise AbortSignalException()

    except AbortSignalException as ase:
        logger.warning(f"INGEST |< cs_input_stanza={input_name}, {ase}")
        raise
    except EventWriterBrokenPipe:
        raise
    except IOError as ioe:
        errors.append(str(ioe))
        log_ingest_error(
            f"{logger_prefix} cs_input_stanza={input_name}, pipeline write error: {ioe}",
            ioe,
        )
        if ioe.errno == errno.EPIPE:
            raise EventWriterBrokenPipe() from ioe
    except Exception as e:
        errors.append(str(e))
        log_ingest_error(f"{logger_prefix} cs_input_stanza={input_name}, error: {e}", e)

    return matching, total, enriched, errors, sourcetype


def ingest_file(
    file_obj: IO[bytes],
    input_config: Dict[str, Any],
    source: str,
    sourcetype: str,
    stopper_fn: Callable,
) -> List[str]:
    def sensor_fn(e) -> Optional[Tuple[bool, Optional[str]]]:
        return event_based_sourcetype(e, input_config)

    def inventory_fn(_):
        return True, sourcetype

    input_name = input_config["input_stanza"]

    meta = dict(
        stanza=input_name,
        host=input_config.get("host"),
        source=source,
    )

    tm_start = time.time()
    logger.debug(f"INGEST |> cs_input_stanza={input_name}, source_file_path={source}")

    enrichers = input_config.get("enrichers") or {}
    for enricher in enrichers.values():
        enricher.load()

    matching, total, enriched, err, sourcetype_ingested = event_writer_ingest(
        file_obj,
        input_config["event_writer"],
        meta,
        input_config["sourcetype_indexes"],
        filter_fn=sensor_fn if sourcetype is None else inventory_fn,
        stopper_fn=stopper_fn,
        enrichers=enrichers,
        raw_event_encoding=input_config.get("cs_event_encoding")
        or DEFAULT_EVENT_ENCODING,
        input_server_host=input_config[SERVER_HOST],
    )
    if not err and total > 0 and sourcetype_ingested is not None:
        solnlib.log.events_ingested(
            logger,
            meta["stanza"],
            sourcetype_ingested,
            total,
            input_config["sourcetype_indexes"][sourcetype_ingested],
        )
    msg = (
        "INGEST |< cs_input_stanza={}, cs_ingest_time_taken={:.3f}, "
        "cs_ingest_file_path={}, cs_ingest_total_events={}, "
        "cs_ingest_filter_matches={}, cs_ingest_enriched_events={}, cs_ingest_traceback_count={}"
    )
    logger.info(
        msg.format(
            input_name,
            time.time() - tm_start,
            source,
            total,
            matching,
            enriched,
            1 if err else 0,
        )
    )

    return err
