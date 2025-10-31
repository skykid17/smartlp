#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
from time import time

import solnlib

from .abort_signal import AbortSignalException
from .aws_helpers import AwsOpsException, aws_download_file
from .constants import APP_NAME, VISIBILITY_TIMEOUT_EXCESS_ALERT
from .ingest_methods import EventWriterBrokenPipe, ingest_file
from .journal import RECORD_FIELDS, WorkerJournal
from .logger_adapter import CSLoggerAdapter
from typing import Optional, Dict, Any, List, Union

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("managed_consumer")
)


class ManagedConsumer(WorkerJournal):
    def __init__(self, server_uri, token, manager, stanza, owner, stopper_fn):
        super(ManagedConsumer, self).__init__(
            server_uri, APP_NAME, token, manager, manager, owner, stopper_fn
        )
        self.stanza = stanza
        self.aws_config = None
        self.input_config = None

    def apply_configs(
        self, aws_config=Optional[Dict[str, Any]], input_config=Optional[Dict[str, Any]]
    ) -> None:
        self.aws_config = aws_config
        self.input_config = input_config

    def register(
        self, can_create_journal: bool = False, **opt: str
    ) -> Optional[Dict[str, Any]]:
        if not super(ManagedConsumer, self).register(can_create_journal, **opt):
            return None

        manager_reg = self.find_manager(attempts=5) or {}
        return json.loads(manager_reg.get(RECORD_FIELDS.data) or "{}")

    def handle_task_execute(
        self, task=Optional[Dict[str, Any]]
    ) -> Union[AwsOpsException, List[str]]:
        assert self.aws_config
        assert self.input_config

        file_obj = None
        file_start = time()
        try:
            file_info = json.loads(task[RECORD_FIELDS.data])
            file_path = file_info["path"]
            bucket = file_info["bucket"]
            file_obj = aws_download_file(self.aws_config, bucket, file_path)

            source = f"s3://{bucket}/{file_path}"
            sourcetype = file_info["sourcetype"]

            logger.info(
                f"{self.owner} has started ingestion: events_source_file={source}, events_sourcetype={sourcetype}"
            )

            error = ingest_file(
                file_obj, self.input_config, source, sourcetype, self.stopper_fn
            )

            msg = (
                "FILE processing summary: cs_input_stanza={}, cs_file_time_taken={:.3f}, "
                "cs_file_path={}, cs_file_size_bytes={}, cs_file_exceptions_count={}"
            )
            logger.info(
                msg.format(
                    self.owner,
                    time() - file_start,
                    file_info["path"],
                    file_info["size"],
                    1 if error else 0,
                )
            )

            vt_excess = time() - float(file_info["vt_expire"])
            if vt_excess > 0:
                logger.warning(
                    VISIBILITY_TIMEOUT_EXCESS_ALERT.format(
                        self.owner, file_path, vt_excess
                    )
                )

            return error

        except AwsOpsException as e:
            return e
        except AbortSignalException as e:
            logger.warning(
                f"{self.owner}, Stopping input as abort signal has been received. "
                "Manager will reassign interrupted events to other available consumer modinputs"
            )
            raise StopIteration() from e
        except EventWriterBrokenPipe as e:
            solnlib.log.log_exception(
                logger,
                e,
                "Event Writer Error",
                msg_before=f"{self.owner}, Stopping input as EVENT WRITER PIPE IS BROKEN. "
                "Manager will reassign interrupted events to other available consumer modinputs",
            )
            raise StopIteration() from e
        finally:
            if file_obj is not None:
                file_obj.close()
