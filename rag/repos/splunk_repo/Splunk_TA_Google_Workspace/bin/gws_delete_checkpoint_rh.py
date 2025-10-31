#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import logging
import traceback

import import_declare_test  # noqa: 401
from solnlib import log
from splunktaucclib.rest_handler import admin_external

import gws_utils
from gws_utils import APP_NAME
from solnlib import conf_manager, log
from solnlib.modular_input import checkpointer
from splunklib import binding
from splunklib import client


class GwsDeleteCheckpointExternalHandler(admin_external.AdminExternalHandler):
    """
    This class extends the functionality of the basic rest handler available in
    the add-on by including deletion of the checkpoints (file-based for
    activity_report and KVStore-based for gws_gmail_logs).
    """

    def __init__(self, *args, **kwargs):
        admin_external.AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, conf_info):
        admin_external.AdminExternalHandler.handleList(self, conf_info)

    def handleEdit(self, conf_info):
        admin_external.AdminExternalHandler.handleEdit(self, conf_info)

    def handleCreate(self, conf_info):
        admin_external.AdminExternalHandler.handleCreate(self, conf_info)

    def handleRemove(self, conf_info):
        self.delete_checkpoint()
        admin_external.AdminExternalHandler.handleRemove(self, conf_info)

    def _delete_collection(
        self, logger: logging.Logger, service: client.Service, collection_name: str
    ):
        try:
            service.kvstore.delete(collection_name)
            logger.info(f"Removed KVStore collection '{collection_name}'")
        except binding.HTTPError as e:
            log.log_exception(
                logger,
                e,
                "Checkpoint Error",
                msg_before=f"Could not delete the KVStore collection '{collection_name}'",
            )

    def _delete_checkpoint_for_activity_report(
        self, logger: logging.Logger, session_key: str, input_name: str
    ):
        try:
            cf_manager = conf_manager.ConfManager(session_key, APP_NAME)
            checkpoint_conf = cf_manager.get_conf("gws_checkpoints")
            checkpoint_conf.delete(f"activity_report:__{input_name}")
            logger.info(
                f"Removed file-based checkpoint for activity_report:{input_name} input"
            )
        except conf_manager.ConfManagerException as e:
            log.log_exception(
                logger,
                e,
                "Checkpoint Error",
                msg_before="No gws_checkpoints file found",
            )
        except conf_manager.ConfStanzaNotExistException as e:
            log.log_exception(
                logger,
                e,
                "Checkpoint Error",
                msg_before=f"No stanza activity_report:__{input_name} in gws_checkpoint file",
            )
        checkpoint_collection_name = (
            gws_utils.get_activity_report_checkpoint_collection_name_from_input_name(
                input_name
            )
        )
        service = client.connect(app=APP_NAME, token=session_key)
        self._delete_collection(
            logger,
            service,
            checkpoint_collection_name,
        )

        unsuccessful_runs_collection_name = gws_utils.get_activity_report_unsuccessful_runs_collection_name_from_input_name(
            input_name
        )
        service = client.connect(app=APP_NAME, token=session_key)
        self._delete_collection(
            logger,
            service,
            unsuccessful_runs_collection_name,
        )

    def _delete_checkpoint_for_gmail_logs(
        self, logger: logging.Logger, session_key: str, input_name: str
    ):
        normalized_input_name = input_name.split("/")[-1]
        collection_name = f"splunk_ta_google_workspace_gmail_{normalized_input_name}"
        try:
            checkpointer_service = checkpointer.KVStoreCheckpointer(
                collection_name,
                session_key,
                APP_NAME,
            )
            checkpointer_service.delete("gmail_headers_modular_input")
            logger.info(f"Removed KVStore checkpoint for {collection_name}")
        except binding.HTTPError as e:
            log.log_exception(
                logger,
                e,
                "Checkpoint Error",
                msg_before=f'Could not delete the checkpoint "splunk_ta_google_workspace_gmail_{normalized_input_name}"',
            )

    def _delete_checkpoint_for_alert_center(
        self, logger: logging.Logger, session_key: str, input_name: str
    ):
        normalized_input_name = input_name.split("/")[-1]
        collection_name = f"splunk_ta_google_workspace_alerts_{normalized_input_name}"
        try:
            checkpointer_service = checkpointer.KVStoreCheckpointer(
                collection_name,
                session_key,
                APP_NAME,
            )
            checkpointer_service.delete("gws_alerts_modular_input")
            logger.info(f"Removed KVStore checkpoint for {collection_name}")
        except binding.HTTPError as e:
            log.log_exception(
                logger,
                e,
                "Checkpoint Error",
                msg_before=f'Could not delete the checkpoint "splunk_ta_google_workspace_alerts_{normalized_input_name}"',
            )

    def delete_checkpoint(self):
        """
        Delete the checkpoint when user deletes input.
        """
        log_filename = "splunk_ta_google_workspace_delete_checkpoint"
        logger = log.Logs().get_logger(log_filename)
        input_name = str(self.callerArgs.id)
        input_type = self.handler.get_endpoint().input_type
        session_key = self.getSessionKey()
        try:
            if input_type == "activity_report":
                self._delete_checkpoint_for_activity_report(
                    logger,
                    session_key,
                    input_name,
                )
            if input_type == "gws_gmail_logs":
                self._delete_checkpoint_for_gmail_logs(
                    logger,
                    session_key,
                    input_name,
                )
            if input_type == "gws_alert_center":
                self._delete_checkpoint_for_alert_center(
                    logger,
                    session_key,
                    input_name,
                )
        except Exception as e:
            log.log_exception(
                logger,
                e,
                "Checkpoint Error",
                msg_before=f"Error while deleting checkpoint for {input_name} input. {traceback.format_exc()}",
            )
