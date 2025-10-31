#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test

import sys
import json

import os
import time
import logging
import traceback
import datetime
from typing import Dict, Union, Optional, List, Any
from splunklib import modularinput as smi
from solnlib import conf_manager, log
from palo_checkpointer import Checkpoint
from palo_utils import (
    logger_instance,
    APP_NAME,
    make_get_request,
    get_proxy_settings,
    get_account_credentials,
)
from splunklib.modularinput import event

bin_dir = os.path.basename(__file__)


class IotSecurityScript(smi.Script):
    def __init__(self) -> None:
        super().__init__()

    def get_scheme(self) -> smi.Scheme:
        scheme = smi.Scheme("iot_security")
        scheme.description = "IoT Security"
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
                "iot_account",
                required_on_create=True,
            )
        )

        return scheme

    def validate_input(self, definition) -> None:
        pass

    def write_data(
        self,
        event_writer: smi.EventWriter,
        events: List[Dict[str, Any]],
        url: str,
        input_item: Dict[str, Any],
        input_name: str,
        sourcetype: str,
        logger: logging.Logger,
        opt_customer_id: Optional[str] = None,
    ):
        """
        Writing events from modular input to Splunk

        :param event_writer: Object of class EventWriter to write Splunk modular input events.
        :param events: Events received from API response.
        :param url: Params used in request if provided.
        :param input_item: Configuration of modular input defined by user.
        :param input_name: Input name defined by user in modular input configuration.
        :param sourcetype: Sourcetype to be assigned for event.
        :param logger: Logger object instance.
        :param opt_customer_id: customer id from user input in TA configuration.
        """
        for data in events:
            if opt_customer_id:
                data["customerId"] = opt_customer_id
            try:
                event_writer.write_event(
                    event.Event(
                        data=json.dumps(data),
                        host=url,
                        index=input_item["index"],
                        source=input_name.split("/")[-1],
                        sourcetype=sourcetype,
                    )
                )
            except Exception as e:
                log.log_exception(
                    logger,
                    e,
                    "IoT Security Error",
                    msg_before=f"Exception during ingesting IoT Security events. Error: {e}",
                )
        log.events_ingested(
            logger, input_name, sourcetype, len(events), input_item["index"]
        )
        logger.debug("IoT Security events ingested successfully.")

    def query_api(
        self,
        logger: logging.Logger,
        url: str,
        parameters: Dict[str, Union[str, int]],
        api_type: str,
        headers: Dict[str, str],
        checkpoint: Checkpoint,
        proxies: Optional[Dict[str, str]] = None,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Queries IoT API

        :param logger: Logger object instance.
        :param url: Url that will be called.
        :param parameters: Params used in API request.
        :param api_type: Type of API used in request.
        :param headers: Headers used in API request.
        :param checkpoint: KVstore checkpointer object.
        :returns: Retrieved events from API.
        """
        global_page_length = 1000
        total = 1000
        results = []
        start_time = time.time()
        page_offset = 0
        try:
            if api_type == "devices":
                items = "devices"
                page_offset = checkpoint.get(parameter="offset")
                if not page_offset:
                    page_offset = 1000
                page = 0
                max_pages = 20

                while page < max_pages:
                    response = make_get_request(
                        url, params=parameters, headers=headers, proxies=proxies
                    )
                    if response.ok:
                        entries = response.json()[items]
                        results += entries
                        total = len(entries)
                        page_offset += global_page_length
                        parameters.update({"offset": page_offset})
                        page += 1
                        logger.debug(
                            f"Current Offset: {page_offset}, Total Entries: {total}, Next Page: {page}"
                        )
                        if total < global_page_length:
                            checkpoint.delete(parameter="offset")
                            checkpoint.delete(parameter="last_run_end")
                            logger.debug("End of device list. Cleared checkpoint data.")
                            break
                    else:
                        raise Exception(
                            f"IOT device response code:{response.status_code}"
                        )
                else:
                    now = datetime.datetime.now()
                    checkpoint.update(parameter="offset", value=page_offset)
                    checkpoint.update(
                        parameter="last_run_timestamp",
                        value=datetime.datetime.strftime(now, "%Y-%m-%d %H:%M:%S"),
                    )
                    logger.debug(
                        f"We have reached max_page. Saved offset: {page_offset} last_run_end: {now}"
                    )
            else:
                items = "items"
                while total == global_page_length:
                    response = make_get_request(
                        url, params=parameters, headers=headers, proxies=proxies
                    )
                    if response.ok:
                        entries = response.json()[items]
                        results += entries
                        total = len(entries)
                        page_offset += global_page_length
                        logger.debug(
                            f"Current Offset: {page_offset}, Total Entries: {total}"
                        )
                        parameters.update({"offset": page_offset})
                    else:
                        raise Exception(
                            f"IOT device response code:{response.status_code}"
                        )
        except Exception as e:
            log.log_exception(
                logger,
                e,
                "IoT Security Error",
                msg_before=str(e),
            )
        run_time = time.time() - start_time
        logger.debug(f"End of {api_type} results. Function took {run_time} to run")
        return results

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
                opt_customer_id = input_item.get("iot_account")
                account_creds = get_account_credentials(
                    session_key, opt_customer_id, "iot_account", logger
                )
                opt_access_key_id = account_creds.get("access_key_id")
                opt_secret_access_key = account_creds.get("secret_access_key")
                checkpoint = Checkpoint(
                    logger=logger,
                    input_name=input_name,
                    session_key=self._input_definition.metadata["session_key"],
                )
                global_url = (
                    f"https://{opt_customer_id}.iot.paloaltonetworks.com/pub/v4.0"
                )
                global_url_params = {
                    "customerid": opt_customer_id,
                    "pagelength": 1000,
                    "offset": 0,
                }
                headers = {
                    "X-Key-Id": opt_access_key_id,
                    "X-Access-Key": opt_secret_access_key,
                }
                last_device_pull = checkpoint.get(parameter="last_run_timestamp")
                if not last_device_pull:
                    checkpoint.update(
                        parameter="last_run_timestamp",
                        value=input_item.get("start_time"),
                    )
                    last_device_pull = input_item.get("start_time")
                # Device inventory takes a long time to fetch because there can be tens of
                # thousands of devices. It can take longer than the poll interval to get all
                # the devices. So at each poll interval, we fetch maximum 20,000 devices
                # (20 pages of 1000 devices each). We also wait 5 minutes between each fetch
                # just in case a crazy pull interval like 5 seconds was used.
                if datetime.datetime.strptime(
                    last_device_pull, "%Y-%m-%d %H:%M:%S"
                ) < datetime.datetime.now() - datetime.timedelta(minutes=5):
                    device_url = f"{global_url}/device/list"
                    params = {
                        "filter_monitored": "yes",
                        "detail": "true",
                    }
                    params.update(global_url_params)
                    devices = self.query_api(
                        logger,
                        device_url,
                        params,
                        "devices",
                        headers,
                        checkpoint,
                        proxies,
                    )
                    self.write_data(
                        event_writer,
                        devices,
                        global_url,
                        input_item,
                        input_name,
                        "pan:iot_device",
                        logger,
                    )
                else:
                    logger.debug(
                        f"Skipping device inventory pull. Last pulled: {last_device_pull}"
                    )
                # Lets get Alerts
                alerts_url = f"{global_url}/alert/list"
                params = {
                    "type": "policy_alert",
                }
                params.update(global_url_params)
                alerts = self.query_api(
                    logger, alerts_url, params, "alerts", headers, checkpoint, proxies
                )
                self.write_data(
                    event_writer,
                    alerts,
                    global_url,
                    input_item,
                    input_name,
                    "pan:iot_alert",
                    logger,
                )
                # Vulnerabilities
                vuln_url = f"{global_url}/vulnerability/list"
                params = {
                    "groupby": "device",
                }
                params.update(global_url_params)
                vulnerabilities = self.query_api(
                    logger,
                    vuln_url,
                    params,
                    "vulnerabilities",
                    headers,
                    checkpoint,
                    proxies,
                )
                self.write_data(
                    event_writer,
                    vulnerabilities,
                    global_url,
                    input_item,
                    input_name,
                    "pan:iot_vulnerability",
                    logger,
                    opt_customer_id,
                )
            except Exception as e:
                log.log_exception(
                    logger,
                    e,
                    "IoT Security Error",
                    msg_before=f"Exception raised while ingesting data for IoT Secuity modular input: {e}. "
                    f"Traceback: {traceback.format_exc()}",
                )


if __name__ == "__main__":
    exit_code = IotSecurityScript().run(sys.argv)
    sys.exit(exit_code)
