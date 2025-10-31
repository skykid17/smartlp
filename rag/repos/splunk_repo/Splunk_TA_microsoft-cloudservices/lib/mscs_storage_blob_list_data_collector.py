#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import queue
import threading
import time

import mscs_consts
import mscs_data_writer as mdw
import mscs_logger as logger
import mscs_storage_blob_dispatcher as msbd
import mscs_util

from modular_inputs.storage.blob.mscs_file_to_kv_checkpoint_migrator import (
    FileToKvCheckpointMigrator,
    MigrationStoppedError,
    MigrationInProgressError,
)
from mscs_checkpointer import KVCheckpointer, FileCheckpointer
from mscs_storage_service import BlobStorageService
from mscs_util import get_conf_file_info


class StorageBlobListDataCollector:
    TIMEOUT = 3
    BATCH_FLUSH_TIMEOUT = 120
    WAIT_FOR_MIGRATION_TO_FINISH = 10

    def __init__(
        self,
        all_conf_contents: dict,
        meta_config: dict,
        task_config: dict,
        stop_event: threading.Event,
    ):
        self._all_conf_contents = all_conf_contents
        self._meta_config = meta_config
        self._task_config = task_config
        self._stop_event = stop_event
        self._data_writer = mdw.DataWriter()
        self._logger = logger.logger_for(self._get_logger_prefix())

        self._storage_dispatcher = msbd.StorageBlobDispatcher(
            all_conf_contents, meta_config, task_config, self._data_writer, self._logger
        )
        self._checkpointer = self._storage_dispatcher.get_checkpointer()
        limits_conf = get_conf_file_info(self._meta_config.get("session_key"), "limits")
        self._batch_limit = int(
            limits_conf.get("kvstore", {}).get("max_documents_per_batch_save", 1000)
        )

        self._logger.debug(f"{task_config['stanza_name']} settings: {task_config}")

    def _do_batch_checkpoint(self, batch_checkpoint: dict):
        """
        Do batch call to update the checkpoint
        :param batch_checkpoint: dict of various checkpoint with key and value
        """
        if not batch_checkpoint:
            return
        ckpt_list = list(batch_checkpoint.values())
        self._checkpointer.batch_save(ckpt_list)
        batch_checkpoint.clear()

    def collect_data(self):
        batch_checkpoint = {}
        try:
            self._perform_checkpoint_migration()
            self._logger.info("Starting to collect data.")
            self._storage_dispatcher.start()

            self._logger.debug("Starting to get data from data_writer.")

            need_get_data = False
            # When we received the stop signal or the table_dispatcher thread is terminated,
            # we will break the loop.
            self.flush_time = time.time() + self.BATCH_FLUSH_TIMEOUT
            while True:
                try:
                    events, key, ckpt = self._data_writer.get_data(timeout=self.TIMEOUT)
                    stop = yield events, None
                    if not stop and key:
                        batch_checkpoint[key] = self._checkpointer.get_formatted_record(
                            key, ckpt
                        )

                        if (
                            len(batch_checkpoint) >= self._batch_limit
                            or self.flush_time < time.time()
                        ):
                            self._do_batch_checkpoint(batch_checkpoint)
                            self.flush_time = time.time() + self.BATCH_FLUSH_TIMEOUT
                    if stop:
                        self._storage_dispatcher.cancel()
                        break

                    if not self._storage_dispatcher.is_alive():
                        need_get_data = True
                        break
                except queue.Empty:
                    if not self._storage_dispatcher.is_alive():
                        need_get_data = True
                        break
                    else:
                        self._do_batch_checkpoint(batch_checkpoint)
                        continue

            self._do_batch_checkpoint(batch_checkpoint)

            if not need_get_data:
                self._checkpointer.close()
                return

            self._logger.debug("Retrieve the remaining data from data_writer.")

            while True:
                try:
                    events, key, ckpt = self._data_writer.get_data(block=False)
                    yield events, None
                    if key:
                        batch_checkpoint[key] = self._checkpointer.get_formatted_record(
                            key, ckpt
                        )

                        if len(batch_checkpoint) >= self._batch_limit:
                            self._do_batch_checkpoint(batch_checkpoint)
                except queue.Empty:
                    break

            self._do_batch_checkpoint(batch_checkpoint)

            self._checkpointer.close()
        except Exception:
            self._do_batch_checkpoint(batch_checkpoint)
            self._logger.exception("Error occurred in collecting data.")
            try:
                self._checkpointer.close()
            except Exception:
                self._logger.exception("Closing checkpointer failed")
            self._storage_dispatcher.cancel()

    def _perform_checkpoint_migration(self):
        self._logger.debug(
            "Starting a process of checkpoint migration from File checkpointer to KV Store checkpointer."
        )
        kv_checkpointer = KVCheckpointer(
            meta_configs=self._meta_config,
            input_id=self._storage_dispatcher.get_checkpoint_input_id(),
        )
        file_checkpointer = FileCheckpointer(
            checkpoint_dir=self._storage_dispatcher.get_checkpoint_dir()
        )
        blob_storage_service = BlobStorageService(
            all_conf_contents=self._all_conf_contents,
            meta_config=self._meta_config,
            task_config=self._task_config,
            proxy_config=self._storage_dispatcher.get_proxy_config(),
            storage_account_config=self._storage_dispatcher.get_storage_account_from_all_confs(),
        )
        container_client = blob_storage_service.get_container_client()
        # Adjust migration batch size to avoid exceeding KV Store limits
        migration_batch_size = self._batch_limit - 1
        file_to_kv_checkpoint_migrator = FileToKvCheckpointMigrator(
            kv_checkpointer=kv_checkpointer,
            file_checkpointer=file_checkpointer,
            container_client=container_client,
            batch_size=migration_batch_size,
            session_key=self._meta_config.get(mscs_consts.SESSION_KEY),
            server_uri=self._meta_config.get(mscs_consts.SERVER_URI),
            modinput_name=self._task_config.get(mscs_consts.STANZA_NAME),
            is_migrated_in_task_config=self._task_config.get(mscs_consts.IS_MIGRATED),
            logger=self._logger,
            stop_event=self._stop_event,
        )
        try:
            file_to_kv_checkpoint_migrator.migrate()
            self._logger.debug(
                "Checkpoint migration process completed. Starting the data collection process."
            )
        except MigrationStoppedError as e:
            self._logger.info("Checkpoint migration was stopped.")
            raise e
        except MigrationInProgressError as e:
            self._logger.info(
                "Checkpoint migration is already in progress by different process."
            )
            raise e

    def _init_from_task_config(self):
        self._table_list = self._task_config.get(mscs_consts.TABLE_LIST)

    def _get_logger_prefix(self):
        account_stanza_name = self._task_config[mscs_consts.ACCOUNT]
        account_info = self._all_conf_contents[mscs_consts.ACCOUNTS][
            account_stanza_name
        ]
        account_name = account_info.get(mscs_consts.ACCOUNT_NAME)
        pairs = [
            '{}="{}"'.format(k, v)
            for k, v in [
                (mscs_consts.STANZA_NAME, self._task_config[mscs_consts.STANZA_NAME]),
                (mscs_consts.ACCOUNT_NAME, account_name),
                (
                    mscs_consts.CONTAINER_NAME,
                    self._task_config[mscs_consts.CONTAINER_NAME],
                ),
                (mscs_consts.BLOB_LIST, self._task_config.get(mscs_consts.BLOB_LIST)),
                (mscs_consts.BLOB_MODE, self._task_config.get(mscs_consts.BLOB_MODE)),
            ]
        ]
        return "[{}]".format(" ".join(pairs))
