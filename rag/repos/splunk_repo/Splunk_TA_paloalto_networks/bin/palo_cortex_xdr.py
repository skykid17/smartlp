#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test

import sys
import json

import os
import logging
import traceback
import datetime
from typing import Dict, Optional, List, Any
from splunklib import modularinput as smi
from solnlib import conf_manager, log
from palo_checkpointer import Checkpoint
from pyxdr.pyxdr import PyXDRClient
from splunklib.modularinput import event
from palo_utils import (
    logger_instance,
    APP_NAME,
    get_proxy_settings,
    get_account_credentials,
)

bin_dir = os.path.basename(__file__)
DEFAULT_FIRST_FETCH = 7


class CortexXDRScript(smi.Script):
    def __init__(self) -> None:
        super().__init__()

    def get_scheme(self) -> smi.Scheme:
        scheme = smi.Scheme("cortex_xdr")
        scheme.description = "Cortex XDR"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        scheme.add_argument(
            smi.Argument(
                "name", title="Name", description="Name", required_on_create=True
            )
        )
        scheme.add_argument(
            smi.Argument(
                "xdr_get_details",
                title="Detailed event",
                description="Detailed event",
                required_on_create=False,
            )
        )
        scheme.add_argument(
            smi.Argument(
                "xdr_account",
                required_on_create=True,
            )
        )

        return scheme

    def validate_input(self, definition) -> None:
        pass

    def ts_to_string(self, timestamp: int) -> str:
        """
        Used for debugging, converts a timestamp in ms to an ISO string

        :param timestamp: Timestamp.
        :returns: Time formatted according to ISO.
        """
        return datetime.datetime.fromtimestamp(
            int(timestamp / 1000), datetime.timezone.utc
        ).isoformat()

    def get_mod_time(
        self, checkpoint: Checkpoint, logger: logging.Logger, start_time: str
    ) -> int:
        """
        Gets last modification time from KVstore lookup
        or calculates it if KVstore lookup doesn't exist

        :param checkpoint: KVstore checkpointer object.
        :param logger: Logger object instance.
        :param start_time: Start time for the first fetch.
        :returns: Timestamp.
        """
        latest_modification_time = checkpoint.get("latest_incident_modified")

        if latest_modification_time:
            mod_time = latest_modification_time + 1
        else:
            parsed_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            mod_time = int(parsed_dt.timestamp() * 1000)
            logger.debug(f"First fetch timestamp Cortex XDR: {mod_time}")
        return mod_time

    def fetch_xdr_incidents(
        self, client: PyXDRClient, mod_time: int, logger: logging.Logger
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Calls XDR API to fecth incidents

        :param client: KVstore checkpointer object.
        :param mod_time: Last modification time.
        :param logger: Logger object instance.
        :returns: Incidents fetched from XDR API.
        """
        logger.debug(f"modification_time filter set to: {self.ts_to_string(mod_time)}")
        try:
            incidents = client.get_incidents(
                limit=50,
                sort_field="modification_time",
                sort_order="asc",
                filters=[
                    {
                        "field": "modification_time",
                        "operator": "gte",
                        "value": mod_time,
                    }
                ],
            )
            logger.info("Message: XDR API Returned Successfully")
            return incidents
        except Exception as e:
            log.log_exception(
                logger,
                e,
                "Cortex XDR Error",
                msg_before=f"Error while fetching XDR incidents: {e}",
            )

    def fetch_incident_details(
        self, client: PyXDRClient, incident: Dict[str, Any], logger: logging.Logger
    ) -> Optional[Dict[str, Any]]:
        """
        Calls XDR API to get extra details for incidents.

        :param client: Cortex XDR API client.
        :param incident: Incident returned from cortex XDR API.
        :param logger: Logger object instance.
        :returns: Inreached incident with details.
        """
        try:
            incident_details = client.get_incident_extra_data(
                incident_id=int(incident["incident_id"])
            )
            return incident_details
        except KeyError as ex:
            log.log_exception(
                logger,
                ex,
                "Cortex XDR Error",
                msg_before=f"Skipping incident as incident_id is not found: {str(ex)}",
            )

    def handle_incidents(
        self,
        client: PyXDRClient,
        incidents: List[Dict[str, Any]],
        get_details: bool,
        base_url: str,
        logger: logging.Logger,
        checkpoint: Checkpoint,
        event_writer: smi.EventWriter,
        input_item: Dict[str, Any],
        input_name: str,
    ) -> None:
        """
        Method writes data to Splunk and gets event details if required

        :param client: Cortex XDR API client.
        :param incidents: Incidents returned from cortex XDR API.
        :param get_details: Parameter from user input defined in modular input.
        :param base_url: Url for API requests.
        :param logger: Logger object instance.
        :param checkpoint: KVstore checkpointer object.
        :param event_writer: Object of class EventWriter to write Splunk modular input events.
        :param input_item: Configuration of modular input defined by user.
        :param input_name: Input name defined by user in modular input configuration.
        """
        try:
            latest_modification_time = int(incidents[-1].get("modification_time"))
            latest_incident_id = int(incidents[-1].get("incident_id"))
            checkpoint.update("latest_incident_modified", latest_modification_time)
            for incident in incidents:
                incident_event = (
                    self.fetch_incident_details(client, incident, logger)
                    if get_details
                    else incident
                )
                event_writer.write_event(
                    event.Event(
                        data=json.dumps(incident_event),
                        host=base_url,
                        index=input_item["index"],
                        source=input_name.split("/")[-1],
                        sourcetype="pan:xdr_incident",
                    )
                )
            logger.info(f"Got {len(incidents)} results")
            logger.debug(
                "Got the following incident IDs: "
                + " ".join([str(y) for y in incidents])
            )
            logger.debug(
                f"latest_modification_time: {self.ts_to_string(latest_modification_time)}"
            )
            logger.debug(f"latest_incident_id: {latest_incident_id}")
            log.events_ingested(
                logger,
                input_name,
                "pan:xdr_incident",
                len(incidents),
                input_item["index"],
            )
        except Exception as e:
            log.log_exception(
                logger,
                e,
                "Cortex XDR Error",
                msg_before=f"Can't ingest Cortex XDR incidents. Error: {e}",
            )

    def stream_events(
        self, inputs: smi.InputDefinition, event_writer: smi.EventWriter
    ) -> None:
        for input_name, input_item in inputs.inputs.items():
            logger = logger_instance(input_name)
            try:
                session_key = self._input_definition.metadata["session_key"]
                log_level = conf_manager.get_log_level(
                    logger=logger,
                    session_key=session_key,
                    app_name=APP_NAME,
                    conf_name="splunk_ta_paloalto_networks_settings",
                )
                logger.setLevel(log_level)
                proxies = get_proxy_settings(logger, session_key)
                get_details = True if input_item.get("xdr_get_details") else False
                tenant_name = input_item.get("xdr_account")
                account_creds = get_account_credentials(
                    session_key, tenant_name, "xdr_account", logger
                )
                region = account_creds.get("region")
                api_key_id = account_creds.get("api_key_id")
                api_key = account_creds.get("api_key")
                checkpoint = Checkpoint(
                    logger=logger,
                    input_name=input_name,
                    session_key=self._input_definition.metadata["session_key"],
                )

                base_url = (
                    f"https://api-{tenant_name}.xdr.{region}.paloaltonetworks.com"
                )

                client = PyXDRClient(
                    api_key_id=api_key_id,
                    api_key=api_key,
                    base_url=base_url,
                    logger=logger,
                    proxy=proxies,
                )

                mod_time = self.get_mod_time(
                    checkpoint, logger, input_item.get("start_time")
                )

                incidents = self.fetch_xdr_incidents(client, mod_time, logger)
                logger.debug(f"Incidents: {incidents}")
                if incidents:
                    self.handle_incidents(
                        client,
                        incidents,
                        get_details,
                        base_url,
                        logger,
                        checkpoint,
                        event_writer,
                        input_item,
                        input_name,
                    )
                else:
                    logger.info("No Incidents")

            except Exception as e:
                log.log_exception(
                    logger,
                    e,
                    "Cortex XDR Error",
                    msg_before=f"Exception raised while ingesting data for Cortex XDR modular input: {e}. "
                    f"Traceback: {traceback.format_exc()}",
                )


if __name__ == "__main__":
    exit_code = CortexXDRScript().run(sys.argv)
    sys.exit(exit_code)
