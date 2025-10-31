#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import json
import os
import re
import signal
import sys
import traceback
import urllib
import datetime
from typing import Tuple, Dict, Union, Generator, List, NoReturn, Optional, Any
from solnlib import utils, log
from solnlib.modular_input import event_writer
import sfdc_checkpoint
import sfdc_consts as sc
import sfdc_utility as su
from data_collector.sfdc_base_data_collector import BaseSfdcDataCollector


class SfdcObjectDataCollector(BaseSfdcDataCollector):
    def __init__(self, sfdc_util_ob: su.SFDCUtil):
        super().__init__(
            sfdc_util_ob,
            checkpoint_collection_name=sc.SFDC_OBJECT_CHECKPOINT_COLLECTION_NAME,
        )
        self.events_ingested = False
        self.ckpt_updated = False

    def exit_gracefully(self, signum, frame) -> None:
        try:
            if self.events_ingested and not self.ckpt_updated:
                self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)
                self.logger.info(
                    f"Checkpoint for input '{self.sfdc_util_ob.input_items['name']}' saved before termination due to SIGTERM, "
                    f"with value = {self.ckpt_data}"
                )
        except Exception as e:
            log.log_exception(
                self.logger,
                e,
                "Exit gratefully Error",
                msg_before=f"SIGTERM termination error: {e}",
            )
        sys.exit(0)

    def regenerate_nextRecordsUrl(
        self, end_date: str, input_items: Dict[str, Any], account_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Method to regenerate the expired query locator (nextRecordsUrl)

        :param end_date:     End date for the data collection
        :param input_items:  Dict containing the input's information
        :param account_info: Dict containing the account's information
        :return:             Tuple containing the regenerated nextRecordsUrl and API response
        """
        return self.do_request(
            end_date,
            "",
            input_items,
            account_info,
            is_nextRecordsUrl_expired=True,
        )

    def do_request(
        self,
        end_date: str,
        nextRecordsUrl: Optional[str],
        input_items: Dict[str, Any],
        account_info: Dict[str, Any],
        is_nextRecordsUrl_expired: bool = False,
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Method to prepare SOQL query and do the API request

        :param end_date:                  End date for the data collection
        :param nextRecordsUrl:            String containing query locator
        :param input_items:               Dict containing the input's information
        :param account_info:              Dict containing the account's information
        :param is_nextRecordsUrl_expired: Boolean value to denote the need of regenerating nextRecordsUrl
        :return:                          Tuple containing the nextRecordsUrl and API response
        """
        if nextRecordsUrl:
            basic_url = f"{account_info['sfdc_server_url']}"
        else:
            basic_url = f"{account_info['sfdc_server_url']}/services/data/v{account_info['sfdc_api_version']}/query?q="
        header = self.sfdc_util_ob.get_basic_header()
        soql_or_query_path = self.build_soql_query(
            input_items,
            self.ckpt_data["data"]["start_date"],
            end_date,
            self.ckpt_data["data"].get("is_greater_than", "True"),
            self.ckpt_data["data"]["sorting_order"],
            nextRecordsUrl,
        )
        url = basic_url + soql_or_query_path
        self.logger.debug(
            f"Invoking the data collection request for input '{input_items['name']}', URL: {url}"
        )
        _, raw_response = self.sfdc_util_ob.make_rest_api(url, header)
        if not raw_response:
            sys.exit(1)

        content: Union[list, dict] = json.loads(raw_response)

        if isinstance(content, list):
            if is_nextRecordsUrl_expired:
                sys.exit(1)
            if content[0]["errorCode"] == "INVALID_QUERY_LOCATOR":
                self.logger.debug(
                    f"Regenerating the expired nextRecordsUrl for input: '{input_items['name']}'"
                )
                _, nextRecordsUrl, content = self.regenerate_nextRecordsUrl(
                    end_date, input_items, account_info
                )
                exising_nextRecordsUrl = self.ckpt_data["data"]["nextRecordsUrl"]
                nextRecordsUrl = (
                    f"{nextRecordsUrl[:nextRecordsUrl.rindex('-')]}-"  # type: ignore
                    f"{exising_nextRecordsUrl[exising_nextRecordsUrl.rindex('-') + 1:]}"
                )
                self.logger.debug(
                    f"successfully regenerated the nextRecordsUrl to be used for input: '{input_items['name']}'"
                )
                return True, nextRecordsUrl, content
            sys.exit(1)

        return False, content.get("nextRecordsUrl"), content

    def data_collector(self) -> Union[Generator[List[Dict], None, None], NoReturn]:
        """Generator method to perform the data collection"""
        input_items = self.sfdc_util_ob.input_items
        account_info = self.sfdc_util_ob.account_info

        datetime_now = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=int(input_items["delay"])
        )
        now = datetime_now.strftime("%Y-%m-%dT%H:%M:%S.000z")
        end_date = self.ckpt_data["data"]["end_date"]
        if not end_date or not self.ckpt_data["data"]["nextRecordsUrl"]:
            self.ckpt_data["data"]["end_date"] = end_date = now
        # end_date will hold the end date of the previous invocation's time_window or current time
        # if data collection of previous invocation's time_window completed successfully.

        if "sorting_order" not in self.ckpt_data["data"]:
            sorting_order = self.identify_sorting_order(end_date)
            self.ckpt_data["data"]["sorting_order"] = sorting_order

        nextRecordsUrl = self.ckpt_data["data"].get("nextRecordsUrl")
        while True:
            is_nextRecordsUrl_expired, nextRecordsUrl, content = self.do_request(
                end_date, nextRecordsUrl, input_items, account_info
            )
            if is_nextRecordsUrl_expired:
                # Skipping the current execution of the loop as we need to do the data collection
                # with the newly regenerated nextRecordsUrl
                continue
            records: List[Dict] = content.get("records", [])
            if (
                not self.ckpt_data["data"].get("nextRecordsUrl")
                and self.ckpt_data["data"].get("is_greater_than", "True").lower()
                == "true"
            ):
                self.logger.debug(
                    "Total number of record(s) present in the timeframe "
                    f"({self.ckpt_data['data']['start_date']}, {end_date}] for input "
                    f"'{input_items['name']}' are '{content.get('totalSize')}'"
                )
            if len(records) == 0:
                self.ckpt_data["data"]["start_date"] = end_date
                self.ckpt_data["data"]["end_date"] = ""
                self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)
                self.logger.info(
                    f"Found 0 events, Checkpoint for input '{input_items['name']}' saved "
                    f"with value = {self.ckpt_data}"
                )
                self.logger.info(
                    f"Completed the invocation of input '{input_items['name']}'"
                )
                break

            if self.ckpt_data["data"].get("is_greater_than", "True").lower() == "true":
                if nextRecordsUrl:
                    self.ckpt_data["data"]["nextRecordsUrl"] = nextRecordsUrl
                else:
                    self.ckpt_data["data"]["start_date"] = end_date
                    self.ckpt_data["data"]["end_date"] = end_date = now
                    # end_date has been updated with the end_date of current
                    # invocation's time_window. This is useful, when data collection has been happening
                    # for the remaining previous invocation's time_window
                    if self.ckpt_data["data"]["start_date"] == now:
                        # Clearing the end_date in the checkpoint as we are completed with the data
                        # collection till the current time and there is no need to hold the end_date of the time_window
                        self.ckpt_data["data"]["end_date"] = ""
                    # Cleaning the nextRecordsUrl in the checkpoint as we are completed with the data collection
                    # of specific time_window
                    self.ckpt_data["data"]["nextRecordsUrl"] = ""

            if "is_greater_than" in self.ckpt_data["data"]:
                del self.ckpt_data["data"]["is_greater_than"]

            self.logger.info(
                f"Number of events to be ingested for input '{input_items['name']}' are: {len(records)}"
            )

            self.ckpt_updated = False
            yield records
            self.events_ingested = True
            self.logger.info(
                f"Successfully ingested '{len(records)}' event(s) for the input '{input_items['name']}'"
            )
            self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)
            self.ckpt_updated = True
            self.events_ingested = False
            self.logger.info(
                f"Checkpoint for input '{input_items['name']}' saved "
                f"with value = {self.ckpt_data}"
            )
            if self.ckpt_data["data"]["start_date"] == now:
                # Breaking the execution as the data collection is completed till the current time
                self.logger.info(
                    f"Completed the invocation of input '{input_items['name']}'"
                )
                break

    def build_soql_query(
        self,
        input_items: Dict,
        start_date: str,
        end_date: str,
        is_greater_than: str,
        sorting_order: str,
        nextRecordsUrl: Optional[str],
    ) -> str:
        """Method to build soql query

        :param input_items:     Dict containing the input's information
        :param start_date:      Start date to be used with 'order_by' field
        :param end_date:        End date for the data collection
        :param is_greater_than: String containing value "True" or "False"
        :param sorting_order:   String containing value "ASC" or "DESC"
        :param nextRecordsUrl:  String containing query locator
        :param sfdc_util_ob:    Utility object
        :return:                Urlencoded string of soql query
        """
        if nextRecordsUrl:
            self.logger.info(
                f"nextRecordsUrl query for input '{self.sfdc_util_ob.input_items['name']}': {nextRecordsUrl}"
            )
            return nextRecordsUrl
        soql = f"SELECT {input_items['object_fields']} FROM {input_items['object']} WHERE {input_items['order_by']}"
        if utils.is_true(is_greater_than):
            soql += (
                f">{start_date} AND {input_items['order_by']}<={end_date} ORDER BY "
                f"{input_items['order_by']} {sorting_order}"
            )
        else:
            soql += f"={start_date}"
        self.logger.info(
            f"SOQL query for input '{self.sfdc_util_ob.input_items['name']}': {soql}"
        )
        soql = urllib.parse.quote(soql)

        return soql

    def identify_sorting_order(self, end_date: str) -> Union[str, NoReturn]:
        """Method to identify the sorting order when checkpoint of input does not contain sorting order information

        :param end_date:     End date for the data collection
        :return:             String containing value "ASC" or "DESC"
        """
        self.logger.debug(
            f"Identifying the sorting order to be used in SOQL query for input '{self.sfdc_util_ob.input_items['name']}'"
        )
        basic_url = (
            f"{self.sfdc_util_ob.account_info['sfdc_server_url']}/services/data/"
            f"v{self.sfdc_util_ob.account_info['sfdc_api_version']}/query?q="
        )
        soql = self.build_soql_query(
            self.sfdc_util_ob.input_items,
            self.ckpt_data["data"]["start_date"],
            end_date,
            self.ckpt_data["data"].get("is_greater_than", "True"),
            "ASC",
            "",
        )
        url = basic_url + soql
        header = self.sfdc_util_ob.get_basic_header()
        _, content = self.sfdc_util_ob.make_rest_api(url, header)
        if not content:
            sys.exit(1)
        content = json.loads(content)
        if isinstance(content, list):
            error_code = content[0]["errorCode"]
            error_message = content[0]["message"]
            if error_code == "BIG_OBJECT_UNSUPPORTED_OPERATION" and re.search(
                pattern="^Unsupported order direction on filter column.*ASCENDING.*",
                string=error_message,
            ):
                self.logger.warning(
                    f"The salesforce object '{self.sfdc_util_ob.input_items['object']}' does not support "
                    "ASCENDING order sorting, proceeding with DESCENDING order"
                )
                return "DESC"
        return "ASC"

    def _timestamp_to_float(self, timestamp: Optional[str]) -> Optional[float]:
        """Method to convert the 'order_by' field timestamp value to epoch time

        :param sfdc_util_ob: Utility object
        :param timestamp:    Timestamp to be converted to epoch
        :return:             Epoch time
        """
        if not timestamp:
            return None
        try:
            utc_time = datetime.datetime.strptime(
                timestamp[:-5], "%Y-%m-%dT%H:%M:%S.%f"
            )
            return (utc_time - datetime.datetime(1970, 1, 1)).total_seconds()
        except Exception:
            self.logger.warning(
                f"Cannot convert timestamp {timestamp} to epoch time.\nTraceback: {traceback.format_exc()}"
            )
            return None

    def start(self) -> None:
        self.ckpt_data = self.ckpt_handler.get_kv_checkpoint() or {}
        if not self.ckpt_data:
            if not self.ckpt_handler.migrate_file_to_kv_checkpoint():
                self.logger.warning(
                    f"Skipping the data collection for input: '{self.sfdc_util_ob.input_items['name']}' "
                    "as file checkpoint migration to KV Store failed. "
                    "Please restart the input to retry the checkpoint migration instantly. "
                    "Migration will be retried automatically on next invocation of the input."
                )
                return
            self.ckpt_data = self.ckpt_handler.get_kv_checkpoint() or {}

        if self.ckpt_data:
            self.logger.debug(
                f"Found existing checkpoint for input '{self.sfdc_util_ob.input_items['name']}', "
                f"checkpoint value: {self.ckpt_data}"
            )

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        # for windows machine
        if os.name == "nt":
            signal.signal(signal.SIGBREAK, self.exit_gracefully)  # type: ignore

        if not self.ckpt_data:
            self.ckpt_data = {
                "data": {
                    "start_date": self.sfdc_util_ob.input_items["start_date"],
                    "nextRecordsUrl": "",
                    "end_date": "",
                },
            }
        elif "is_greater_than" in self.ckpt_data["data"]:
            self.ckpt_data["data"]["nextRecordsUrl"] = ""
            self.ckpt_data["data"]["end_date"] = ""

        collector = self.data_collector()

        ew = event_writer.ClassicEventWriter()
        for records in collector:
            for record in records:
                record.update(
                    {"UserAccountId": self.sfdc_util_ob.account_info["user_account_id"]}
                )

            ew.write_events(
                [
                    ew.create_event(
                        data=json.dumps(record, ensure_ascii=False),
                        time=self._timestamp_to_float(
                            record.get(self.sfdc_util_ob.input_items["order_by"]),
                        ),
                        index=self.sfdc_util_ob.input_items["index"],
                        host=self.sfdc_util_ob.input_items["host"],
                        source=(
                            "sfdc_object://"
                            f"{self.sfdc_util_ob.input_items['object']}_"
                            f"{self.sfdc_util_ob.account_info['name']}_"
                            f"{self.sfdc_util_ob.input_items['name']}"
                        ),
                        sourcetype=f"sfdc:{self.sfdc_util_ob.input_items['object']}".lower(),
                    )
                    for record in records
                ]
            )
            log.events_ingested(
                self.logger,
                f"{self.sfdc_util_ob.input_items['input_type']}://{self.sfdc_util_ob.account_info['name']}",
                f"sfdc:{self.sfdc_util_ob.input_items['object']}".lower(),
                len(records),
                self.sfdc_util_ob.input_items["index"],
            )
