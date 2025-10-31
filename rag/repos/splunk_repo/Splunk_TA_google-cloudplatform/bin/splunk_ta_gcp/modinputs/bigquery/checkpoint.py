#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import os
import traceback
import requests
from splunksdc import logging
from datetime import datetime

logger = logging.get_module_logger()


class CheckpointMigration:
    def __init__(self, collection, app, config) -> None:
        """
        Checkpoint Migration old
        Args:
            collection (_type_): collection object
            app (_type_): app object
            config (_type_): config object
            input_name (str): input name
        """
        self._collection = collection
        self._app = app
        self._config = config
        self._ckpt_data = []

    @staticmethod
    def remove_file(filename: str) -> None:
        """
        Used to remove the checkpoint file
        :param filename: checkpoint file path.
        :type filename: ``string``
        """
        try:
            os.remove(filename)
            logger.info("Successfully removed the checkpoint file: {}".format(filename))
        except:
            logger.error(
                "Failed to remove the checkpoint file: {}. Error: {}".format(
                    filename, traceback.format_exc()
                )
            )

    # Custom function to serialize datetime objects with microsecond precision
    @staticmethod
    def serialize_datetime_with_microseconds(export_time):
        if type(export_time) is datetime:
            return export_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return export_time

    def load_checkpoint(self, filename: str) -> None:
        """
        This method used to load the file-based checkpoint
        Args:
            filename (str): filename or input name
        """
        with self._app.open_checkpoint(filename) as fp_checkpoint:
            fp_checkpoint.sweep()
            self.ckpt_keys = list(fp_checkpoint._indexes)

            for key in self.ckpt_keys:
                pair = fp_checkpoint.find(key)
                split_values = pair.value.split(",")

                # Extracting the key, export_time, and the offset
                ckpt_key = key.split("/")[-1]
                export_time = split_values[0].strip()
                offset = split_values[1].strip('"\n')

                export_time = CheckpointMigration.serialize_datetime_with_microseconds(
                    export_time
                )
                # Creating the dictionary
                result_dict = {
                    "_key": ckpt_key,
                    "export_time": export_time,
                    "offset": int(offset),
                    "is_migrated": 1,
                }
                self._ckpt_data.append(result_dict)

        logger.info("Successfully loaded the checkpoint for input: {}".format(filename))

    def migrate(self):
        """
        This method used the migrate the checkpoint to KV
        """
        if self._ckpt_data:
            self._collection.batch_save(self._ckpt_data)
        logger.info(
            "Successfully migrated the checkpoints in the kv-store, collection: {}".format(
                self._collection._collection_name
            )
        )

    def send_notification(self, name: str, message: str) -> None:
        """
        Used to send the notification splunk UI.
        :param name: message name or key.
        :type input_name: ``string``
        :param message: message value.
        :type input_name: ``string``
        """
        url: str = "{}://{}:{}/services/messages".format(
            self._app._context._server_scheme,
            self._app._context._server_host,
            self._app._context._server_port,
        )
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Bearer {}".format(self._config._service.token),
        }
        payload = {
            "name": name,
            "value": message,
            "severity": "info",
        }
        # semgrep ignore reason: not require verify is true
        response = requests.post(
            url, data=payload, headers=headers, verify=False
        )  # nosemgrep
        if response.status_code == 201:
            logger.info("Successfully sent the migration notification.")
        else:
            logger.warn("Failed to send the migration notification.")
