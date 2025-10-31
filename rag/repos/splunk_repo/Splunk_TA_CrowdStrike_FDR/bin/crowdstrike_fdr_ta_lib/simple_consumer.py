#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
from random import randint
from time import time, sleep
from datetime import datetime

import solnlib

from .abort_signal import (
    AbortSignalException,
)
from .aws_helpers import (
    AwsOpsException,
    aws_check_success,
    aws_delete_sqs_message,
    aws_download_file,
    aws_receive_sqs_messages,
)
from .constants import (
    MAX_MESSAGE_REQUEST_RETRIES,
    MESSAGE_REQUEST_RETRY_INTERVAL_RANGE,
    VISIBILITY_TIMEOUT_EXCESS_ALERT,
)
from .filtering import prefix_based_sourcetype
from .ingest_methods import EventWriterBrokenPipe, ingest_file
from .logger_adapter import CSLoggerAdapter

from typing import Optional, Callable, Dict, Any, List

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("simple_consumer")
)


def receive_sqs_messages(
    aws_config: Dict[str, Any], stopper_fn: Optional[Callable], check_interval: int = 3
) -> List[Dict[str, Any]]:
    sqs_url = aws_config["sqs_url"]
    sqs_cfg = aws_config["sqs_creds"]
    visibility_timeout = aws_config["visibility_timeout"]
    max_number_of_messages = aws_config["max_number_of_messages"]

    messages = []
    for _ in range(MAX_MESSAGE_REQUEST_RETRIES):
        messages = aws_receive_sqs_messages(
            sqs_cfg, sqs_url, visibility_timeout, max_number_of_messages
        )
        if messages:
            break

        next_attempt = time() + randint(*MESSAGE_REQUEST_RETRY_INTERVAL_RANGE)
        while True:
            if stopper_fn is not None and stopper_fn():
                return messages

            to_wait = next_attempt - time()
            if to_wait <= 0:
                break
            if to_wait > check_interval:
                to_wait = check_interval
            sleep(to_wait)

    return messages


def run(
    input_config: Dict[str, Any],
    aws_config: Dict[str, Any],
    stopper_fn: Optional[Callable],
) -> None:
    sqs_url = aws_config["sqs_url"]
    visibility_timeout = aws_config["visibility_timeout"]
    max_number_of_messages = aws_config["max_number_of_messages"]
    sqs_cfg, s3_cfg = aws_config["sqs_creds"], aws_config["s3_creds"]
    input_name = input_config["input_stanza"]
    aws_sqs_ignore_before = input_config.get("aws_sqs_ignore_before")

    while True:
        if stopper_fn is not None and stopper_fn():
            break

        logger.debug(
            f"{input_name} is processing SQS messages: sqs_url={sqs_url}, sqs_msg_action=requesting "
            + f"visibility_timeout={visibility_timeout}, max_number_of_messages={max_number_of_messages}"
        )
        messages = receive_sqs_messages(aws_config, stopper_fn)
        if not messages:
            return

        batch_start = time()
        batch_error_count = 0
        for msg_info in messages:
            logger.info(
                f"{input_name} is processing SQS messages: sqs_msg_raw={json.dumps(msg_info)}"
            )
            if stopper_fn is not None and stopper_fn():
                raise AbortSignalException()

            file_obj = None
            try:
                logger.info(
                    f"{input_name} is processing SQS messages: sqs_msg_action=received sqs_msg_count={len(messages)}"
                )

                prefix = msg_info["pathPrefix"]
                bucket = msg_info["bucket"]
                fileCount = msg_info["fileCount"]
                sqs_msg_timestamp = float(msg_info["timestamp"]) / 1000
                sqs_msg_timestamp_iso = datetime.fromtimestamp(
                    sqs_msg_timestamp
                ).isoformat()
                fileList = ",".join([f["path"] for f in msg_info["files"]])
                msg_prefix = (
                    f"{input_name} is processing SQS messages: sqs_msg_bucket={bucket}, sqs_msg_pathPrefix={prefix}, "
                    + f'sqs_msg_timestamp={sqs_msg_timestamp_iso}, sqs_msg_fileCount={fileCount}, sqs_msg_fileList="{fileList}"'
                )

                ingest, sourcetype = prefix_based_sourcetype(prefix, input_config)
                if not ingest:
                    logger.info(
                        f"{msg_prefix}, sqs_msg_action=skip, "
                        'sqs_msg_action_note="this kind of events is not selected for ingestion or unknown"'
                    )
                    continue

                received = msg_info["received"]
                if aws_sqs_ignore_before:
                    aws_sqs_ignore_before_iso = datetime.fromtimestamp(
                        aws_sqs_ignore_before
                    ).isoformat()
                else:
                    aws_sqs_ignore_before_iso = None

                logger.debug(
                    f"{input_name}, batch {prefix}, SQS message timestamp: {sqs_msg_timestamp_iso}, "
                    + f"threshold: {aws_sqs_ignore_before_iso}"
                )
                if aws_sqs_ignore_before and aws_sqs_ignore_before > sqs_msg_timestamp:
                    logger.info(
                        f"{msg_prefix}, sqs_msg_action=skip, "
                        'sqs_msg_action_note="SQS message is older than threshold" '
                        f'sqs_message_timestamp="{sqs_msg_timestamp_iso}", '
                        f'sqs_message_threshold="{aws_sqs_ignore_before_iso}"'
                    )
                    continue

                if not aws_check_success(s3_cfg, bucket, prefix):
                    logger.info(
                        f"{msg_prefix}, sqs_msg_action=skip, "
                        'sqs_msg_action_note="No _SUCCESS file found"'
                    )
                    continue

                logger.info(f"{msg_prefix}, sqs_msg_action=ingest")

                vt_end_time = received + visibility_timeout
                for file_info in msg_info.get("files", []):
                    if stopper_fn is not None and stopper_fn():
                        raise AbortSignalException()

                    file_start = time()

                    file_path = file_info["path"]
                    file_obj = aws_download_file(s3_cfg, bucket, file_path)

                    source = f"s3://{bucket}/{file_path}"
                    logger.info(
                        f"{input_name} has started ingestion: events_source_file={source}, events_sourcetype={sourcetype}"
                    )
                    error = ingest_file(
                        file_obj, input_config, source, sourcetype, stopper_fn
                    )
                    if error:
                        batch_error_count += 1

                    msg = (
                        "FILE processing summary: cs_input_stanza={}, cs_file_time_taken={:.3f}, "
                        "cs_file_path={}, cs_file_size_bytes={}, cs_file_error_count={}"
                    )
                    logger.info(
                        msg.format(
                            input_name,
                            time() - file_start,
                            file_info["path"],
                            file_info["size"],
                            1 if error else 0,
                        )
                    )

                    vt_excess = time() - vt_end_time
                    if vt_excess > 0:
                        logger.warning(
                            VISIBILITY_TIMEOUT_EXCESS_ALERT.format(
                                input_name, file_info["path"], vt_excess
                            )
                        )

                aws_delete_sqs_message(sqs_cfg, sqs_url, msg_info["receipt_handle"])
            except AwsOpsException:
                batch_error_count += 1
            except AbortSignalException:
                logger.info(
                    f"{input_name}, Stopping input as abort signal has been received. "
                    "TA will re-try to ingest interrupted events after AWS SQS visibility_timeout expires"
                )
                return
            except EventWriterBrokenPipe:
                logger.info(
                    f"{input_name}, Stopping input as EVENT WRITER PIPE IS BROKEN. "
                    "TA will re-try to ingest interrupted events after AWS SQS visibility_timeout expires"
                )
                return
            finally:
                if file_obj is not None:
                    file_obj.close()

        msg = (
            "BATCH processing summary: cs_input_stanza={}, cs_batch_time_taken={:.3f}, "
            "cs_batch_bucket={}, cs_batch_path={}, cs_batch_exceptions_count={}"
        )
        logger.info(
            msg.format(
                input_name,
                time() - batch_start,
                msg_info["bucket"],
                msg_info["pathPrefix"],
                batch_error_count,
            )
        )
