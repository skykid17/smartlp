#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
from time import time
from datetime import datetime
from typing import List, Dict, Any

import solnlib

from .aws_helpers import (
    aws_check_success,
    aws_delete_sqs_message,
    aws_receive_sqs_messages,
)
from .constants import APP_NAME, JOURNAL_RESTART_FAILED_TASKS_INTERVAL
from .filtering import prefix_based_sourcetype
from .journal import RECORD_FIELDS, TASK_STATUS, ManagerJournal
from .logger_adapter import CSLoggerAdapter
from typing import Tuple, Callable, Dict, Any

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("managed_consumer")
)


class SqsManager(ManagerJournal):
    def __init__(
        self,
        server_uri: str,
        token: str,
        input_config: Dict[str, Any],
        aws_config: Dict[str, Any],
        stopper_fn: Callable,
    ) -> None:
        self.input_config = input_config
        self.aws_config = aws_config

        input_name = self.input_config["input_stanza"]
        # manager_id = f"[{input_name}]@{platform.node()}"
        super(SqsManager, self).__init__(
            server_uri, APP_NAME, token, input_name, input_name, stopper_fn
        )

    def split_by_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_batch = {}
        for task in tasks:
            task_info = json.loads(task[RECORD_FIELDS.data])

            receipt_handle = task_info["receipt_handle"]
            if receipt_handle not in by_batch:
                by_batch[receipt_handle] = {"done": [], "todo": []}

            task_status = task[RECORD_FIELDS.status]
            if task_status in (TASK_STATUS.done, TASK_STATUS.fatal):
                # tasks with 'failed' status will be retried later
                # so they are not fully done yet
                by_batch[receipt_handle]["done"].append(task)
            else:
                by_batch[receipt_handle]["todo"].append(task)

        return by_batch

    def split_by_status(
        self, tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Any], List[Any]]:
        done, todo = [], []
        for task in tasks:
            task_status = task[RECORD_FIELDS.status]
            if task_status in (
                TASK_STATUS.done,
                TASK_STATUS.fatal,
                TASK_STATUS.failed,
            ):
                # tasks with 'failed' status will be retried later
                # and do not need a spare worker immediately
                # so to decide whether to request next bacth or not
                # we treat failed tasks as done 'for now'
                done.append(task)
            else:
                todo.append(task)

        return done, todo

    def split_by_source(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_source = {}
        for task in tasks:
            task_info = json.loads(task[RECORD_FIELDS.data])
            source = f"s3://{task_info['bucket']}/{task_info['path']}"
            by_source[source] = task

        return by_source

    def analyse_done_tasks(
        self, done: List[Dict[str, Any]]
    ) -> Tuple[List[Any], set, float, int]:
        task_data = []
        checkpoint_types = set()
        batch_start = time()
        failedCount = 0
        for tsk in done:
            data = json.loads(tsk["data"])
            task_data.append(data)
            checkpoint_types.add(data["checkpoint_type"])
            received = data.get("received")
            if received is None:
                logger.warning(
                    f"{self.owner} task data has no 'received' property: {tsk['data']}"
                )
            elif batch_start is None or batch_start > received:
                batch_start = received
            if tsk[RECORD_FIELDS.status] != TASK_STATUS.done:
                failedCount += 1

        return task_data, checkpoint_types, batch_start, failedCount

    def delete_batch_sqs_message(self, receipt_handle: str, task_data: list) -> bool:
        prefix = "/".join(task_data[0]["path"].split("/")[:-1])
        bucket = task_data[0]["bucket"]

        fileCount = len(task_data)
        fileList = ",".join([data["path"] for data in task_data])
        msg = (
            f"{self.owner} is processing SQS messages: sqs_msg_bucket={bucket}, sqs_msg_pathPrefix={prefix}, "
            + f'sqs_msg_fileCount={fileCount}, sqs_msg_fileList="{fileList}", sqs_msg_action=delete'
        )
        try:
            sqs_cfg = self.aws_config["sqs_creds"]
            sqs_url = self.aws_config["sqs_url"]
            aws_delete_sqs_message(sqs_cfg, sqs_url, receipt_handle)
            logger.info(msg)

        except Exception as e:
            err_msg = f'{msg}, sqs_msg_action_note="{e}"'
            if "is not a valid receipt handle." in str(e):
                logger.warning(err_msg)
                return True
            if "Reason: The receipt handle has expired." not in str(e):
                solnlib.log.log_exception(
                    logger, e, "AWS SQS Error", msg_before=err_msg
                )
                return False

            logger.warning(err_msg)

        return True

    def finalize_batch_process(
        self, receipt_handle: str, done: List[Any], todo: List[Any]
    ) -> bool:
        if len(todo) == 0 and len(done) > 0:
            logger.info(f"{self.owner} Finalizing ingested event batches")

            (
                task_data,
                checkpoint_types,
                batch_start,
                failedCount,
            ) = self.analyse_done_tasks(done)

            if "sqs" in checkpoint_types:
                if not self.delete_batch_sqs_message(receipt_handle, task_data):
                    return False

            batch_time_taken = time() - batch_start
            prefix = "/".join(task_data[0]["path"].split("/")[:-1])
            bucket = task_data[0]["bucket"]
            logger.info(
                f"BATCH processing summary: cs_input_stanza={self.owner}, "
                + f"cs_batch_time_taken={batch_time_taken:.3f}, "
                + f"cs_batch_bucket={bucket}, cs_batch_path={prefix}, "
                + f"cs_batch_exceptions_count={failedCount}"
            )

            try:
                self.delete_tasks(done)
            except Exception as e:
                solnlib.log.log_exception(
                    logger,
                    e,
                    "Task Journal",
                    msg_before=f"{self.owner} Failed to delete tasks from journal: {done}, "
                    + f"receipt_handle: {receipt_handle}, error: {e}",
                )
                return False
        return True

    def finalize_ingested_batches(self, tasks: List[Dict[str, Any]]) -> None:
        logger.debug(
            f"{self.owner} Checking finalizing of ingested event batches is required"
        )
        by_batch = self.split_by_batch(tasks)
        for receipt_handle, tasks_by_action in by_batch.items():
            self.finalize_batch_process(receipt_handle, **tasks_by_action)

    def request_next_resource_batch(self) -> List[Dict[str, Any]]:
        sqs_url = self.aws_config["sqs_url"]
        sqs_cfg = self.aws_config["sqs_creds"]
        s3_cfg = self.aws_config["s3_creds"]
        visibility_timeout = self.aws_config["visibility_timeout"]
        max_number_of_messages = self.aws_config["max_number_of_messages"]
        aws_sqs_ignore_before = self.input_config.get("aws_sqs_ignore_before")
        checkpoint_type = self.input_config.get("checkpoint_type") or "sqs"

        resources = []
        while not resources:
            logger.debug(
                f"{self.owner} is processing SQS messages: sqs_url={sqs_url}, "
                + f"sqs_msg_action=requesting, visibility_timeout={visibility_timeout}, "
                + f"max_number_of_messages={max_number_of_messages}"
            )
            messages = aws_receive_sqs_messages(
                sqs_cfg, sqs_url, visibility_timeout, max_number_of_messages
            )

            logger.info(
                f"{self.owner} is processing SQS messages: sqs_msg_action=received sqs_msg_count={len(messages)}"
            )

            if not messages:
                logger.debug(
                    f"{self.owner} is processing SQS messages: sqs_msg_action=summary sqs_msg_resources={resources}"
                )
                return resources

            for msg_info in messages:
                logger.info(
                    f"{self.owner} is processing SQS messages: sqs_msg_raw={json.dumps(msg_info)}"
                )

                receipt_handle = msg_info["receipt_handle"]
                bucket = msg_info["bucket"]
                prefix = msg_info["pathPrefix"]
                fileCount = msg_info["fileCount"]
                sqs_msg_timestamp = float(msg_info["timestamp"]) / 1000
                sqs_msg_timestamp_iso = datetime.fromtimestamp(
                    sqs_msg_timestamp
                ).isoformat()
                fileList = ",".join([f["path"] for f in msg_info["files"]])
                msg_prefix = (
                    f"{self.owner} is processing SQS messages: sqs_msg_bucket={bucket}, sqs_msg_pathPrefix={prefix}, "
                    + f'sqs_msg_timestamp={sqs_msg_timestamp_iso}, sqs_msg_fileCount={fileCount}, sqs_msg_fileList="{fileList}"'
                )
                ingest, sourcetype = prefix_based_sourcetype(prefix, self.input_config)
                if not ingest:
                    logger.info(
                        f"{msg_prefix}, sqs_msg_action=skip, "
                        'sqs_msg_action_note="this kind of events is not selected for ingestion or unknown"'
                    )
                    continue

                if aws_sqs_ignore_before:
                    aws_sqs_ignore_before_iso = datetime.fromtimestamp(
                        aws_sqs_ignore_before
                    ).isoformat()
                else:
                    aws_sqs_ignore_before_iso = None

                logger.debug(
                    f"{self.owner}, batch {prefix}, SQS message timestamp: {sqs_msg_timestamp_iso}, "
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

                for file_info in msg_info.get("files", []):
                    file_info["bucket"] = bucket
                    file_info["sourcetype"] = sourcetype
                    file_info["received"] = msg_info["received"]
                    file_info["vt_expire"] = msg_info["received"] + visibility_timeout
                    file_info["receipt_handle"] = receipt_handle
                    file_info["checkpoint_type"] = checkpoint_type

                    resources.append(file_info)

                if checkpoint_type != "sqs":
                    try:
                        aws_delete_sqs_message(sqs_cfg, sqs_url, receipt_handle)
                        logger.info(f"{msg_prefix}, sqs_msg_action=delete")
                    except Exception as e:
                        solnlib.log.log_exception(
                            logger,
                            e,
                            "AWS SQS Error",
                            msg_before=f'{msg_prefix}, sqs_msg_action=delete, sqs_msg_action_note="{e}"',
                        )

        logger.debug(
            f"{self.owner} is processing SQS messages: sqs_msg_action=summary, sqs_msg_resources={resources}"
        )
        return resources

    def consider_next_batch(
        self, workers: Dict[str, Any], tasks: List[Dict[str, Any]]
    ) -> None:
        logger.debug(f"{self.owner} Next batch, checking if it's required")
        _, todo = self.split_by_status(tasks)
        logger.debug(
            f"{self.owner} Next batch, next_batch_check__workers_running={len(workers)}, "
            + f'next_batch_check__tasks_left={len(todo)}, next_batch_check__task_list="{todo}"'
        )
        if len(todo) >= len(workers):
            logger.debug(
                f"{self.owner} Next batch, next_batch_check__status=not_needed"
            )
            return

        logger.debug(f"{self.owner} Next batch, next_batch_check__status=needed")
        resources = self.request_next_resource_batch()
        if resources:
            by_source = self.split_by_source(tasks)
            for new_task_data in resources:
                new_task_source = (
                    f"s3://{new_task_data['bucket']}/{new_task_data['path']}"
                )
                existing_task = by_source.get(new_task_source)
                if existing_task:
                    if existing_task[RECORD_FIELDS.status] == TASK_STATUS.failed:
                        logger.info(
                            f"{self.owner} Next batch resource, batch_source_file={new_task_source}, "
                            + "batch_source_status=RESTART_FAILED_TASK"
                        )
                        self.update_task(
                            existing_task,
                            data=json.dumps(new_task_data),
                            status=TASK_STATUS.retry,
                            error="",
                        )
                    else:
                        logger.info(
                            f"{self.owner} Next batch resource, batch_source_file={new_task_source}, "
                            + "batch_source_status=ALREADY_INGESTED"
                        )
                else:
                    logger.info(
                        f"{self.owner} Next batch resource, batch_source_file={new_task_source}, "
                        + "batch_source_status=CREATE_NEW_TASK"
                    )
                    self.create_task(json.dumps(new_task_data))
        else:
            logger.info(f"{self.owner} Next batch is not available")

    def review_failed_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        logger.debug(f"{self.owner} reviews failed ingest tasks")
        for t in tasks:
            if t[RECORD_FIELDS.status] != TASK_STATUS.failed:
                continue

            if time() - float(t["time"]) < JOURNAL_RESTART_FAILED_TASKS_INTERVAL:
                continue

            failed_task_data = json.loads(t["data"])
            if failed_task_data["checkpoint_type"] == "sqs":
                continue

            failed_task_source = (
                f"s3://{failed_task_data['bucket']}/{failed_task_data['path']}"
            )
            logger.info(
                f"{self.owner} reviews failed ingest tasks, batch_source_file={failed_task_source}, "
                + "batch_source_status=RESTART_FAILED_TASK"
            )
            self.update_task(t, status=TASK_STATUS.retry, error="")

    def on_journal_monitor(
        self, workers: Dict[str, Any], tasks: List[Dict[str, Any]]
    ) -> None:
        self.review_failed_tasks(tasks)
        self.finalize_ingested_batches(tasks)
        self.consider_next_batch(workers, tasks)
