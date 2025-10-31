#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import csv
import json
import os
import re
import signal
import sys
import traceback
import urllib
import requests
from functools import partial
from typing import Dict, List

import sfdc_checkpoint
import sfdc_consts as sc
import sfdc_utility as su
from solnlib.modular_input import event_writer
from solnlib.modular_input.event import XMLEvent
from solnlib import log

from data_collector.sfdc_base_data_collector import BaseSfdcDataCollector


class SfdcEventLogDataCollector(BaseSfdcDataCollector):
    def __init__(self, sfdc_util_ob: su.SFDCUtil):
        super().__init__(
            sfdc_util_ob,
            checkpoint_collection_name=sc.SFDC_EVENTLOG_CHECKPOINT_COLLECTION_NAME,
        )

    def exit_gracefully(
        self,
        signum,
        frame,
    ) -> None:
        """Handle sigterm gracefully and update the checkpoint
        if events are ingested and checkpoint is not updated to restrict data duplication
        """
        try:
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

    def data_collector(self) -> None:
        """Method to perform data collection"""

        input_items = self.sfdc_util_ob.input_items
        account_info = self.sfdc_util_ob.account_info
        is_ckpt_migrated = self.ckpt_handler.is_checkpoint_migrated_to_kv()
        hashed_input_name = su.get_hashed_value(input_items["name"])
        basic_url = f"{account_info['sfdc_server_url']}/services/data/v{account_info['sfdc_api_version']}/query?q="
        header = self.sfdc_util_ob.get_basic_header()
        self.logger.debug(f"Data collection started for: {input_items['name']}")
        remaining_records = []
        records_on_start_date = []
        start_date = input_items["start_date"]
        monitoring_interval = input_items["monitoring_interval"]
        file_checkpoint_handler = None

        if is_ckpt_migrated:
            self.ckpt_data = self.ckpt_handler.get_kv_checkpoint() or {}
        else:
            file_checkpoint_handler = self.ckpt_handler.get_file_checkpoint_manager()
            file_checkpoint_value = self.ckpt_handler.get_file_checkpoint(
                file_checkpoint_handler
            )
            self.ckpt_data = (
                file_checkpoint_value.get(hashed_input_name, {})
                if file_checkpoint_value
                else {}
            )

        if self.ckpt_data:
            self.logger.info(
                f"Existing checkpoint is present for: {input_items['name']}"
            )
            start_date = self.ckpt_data["data"]["start_date"]
            records = self.ckpt_data["data"]["records"][:]
            records_on_start_date = self.ckpt_data["data"]["records_on_start_date"][:]
            if records and not is_ckpt_migrated and file_checkpoint_handler:
                remaining_records = self.remove_ingested_records_from_checkpoint(
                    records, file_checkpoint_handler
                )
                file_checkpoint_handler.update(
                    su.get_hashed_value(self.sfdc_util_ob.input_items["name"]),
                    self.ckpt_data,
                )
                self.logger.debug(
                    f"File checkpoint updated while migration to {self.ckpt_data}"
                )
            elif is_ckpt_migrated:
                remaining_records = records

        else:
            self.logger.info(
                f"Existing checkpoint not present for: {input_items['name']} \n Creating new Checkpoint"
            )
            self.ckpt_data = {
                "data": {
                    "start_date": start_date,
                    "records": [],
                    "records_on_start_date": [],
                },
            }

        if not is_ckpt_migrated:
            self.ckpt_handler.migrate_file_to_kv_checkpoint()

        soql = self.build_soql_query_for_logfile_id(monitoring_interval, start_date)
        url = basic_url + soql
        self.logger.debug(
            f"Invoking the request to fetch EventLogFiles for input '{input_items['name']}', URL: {url}"
        )
        try:
            _, raw_response = self.sfdc_util_ob.make_rest_api(url, header)
            if not raw_response:
                self.logger.info(
                    f"Empty content returned for {url},  Please verify if all the required credentials are valid."
                )
                return
            content = json.loads(raw_response)
            newly_fetched_records = content.get("records")
        except AttributeError as aE:
            log.log_exception(
                self.logger,
                aE,
                "Data collector Attribute Error",
                msg_before=f"Monitoring Interval 'Hourly' is not Supported in your Salesforce Package, Please update the monitoring interval of the input: {input_items['name']} to 'Daily'",
            )
            return
        if len(newly_fetched_records) == 0:
            self.logger.debug(f"0 records returned for {url}")
        new_records = self.filter_records(
            records_on_start_date[:], newly_fetched_records
        )
        all_records = remaining_records + new_records
        if all_records:
            start_date = self.get_last_event_time(monitoring_interval, all_records)
            records_on_start_date = self.update_record_on_start_date_value(
                monitoring_interval, start_date, newly_fetched_records
            )
            self.ckpt_data["data"]["records_on_start_date"] = records_on_start_date[:]
            self.ckpt_data["data"]["records"] = all_records[:]
            self.ckpt_data["data"]["start_date"] = start_date
            self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)

            # Data collection is placed after ckpt update, as individual record id will be deleted from records in data_collection_of_individual_logfile.
            # record-id present in ckpt["data"]["records"] will be collected as part of remaining data in next invocation.
            self.data_collection_of_individual_logfile(all_records, header)

        else:
            self.logger.debug(
                "No records to process, quitting data colloction process."
            )
            self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)
        self.logger.debug(
            f"Checkpoint updated, Data collection completed till {start_date}"
        )

    def remove_ingested_records_from_checkpoint(
        self,
        records: List,
        file_checkpoint_handler: sfdc_checkpoint.SFDCFileCheckpointer,
    ) -> List[Dict]:
        """Remove ingested record from the checkppoint directory, of specific input.

        Args:
            records (list): list of all the records present in the existing checkpoint file.
            file_checkpoint_handler (SFDCFileCheckpointer): file checkpoint manager
        Returns:
            list: list of records which were not collected in previous iteration
        """
        try:
            self.logger.debug("Removing ingested_records from checkpoint data")
            for record in records:
                record_ckpt = file_checkpoint_handler.get(
                    su.get_hashed_value(record["Id"])
                )
                if record_ckpt:
                    file_checkpoint_handler.delete(su.get_hashed_value(record["Id"]))
                    self.ckpt_data["data"]["records"].remove(record)
        except Exception as e:
            log.log_exception(
                self.logger,
                e,
                "Remove ingested record Error",
                msg_before=f"Exception occured while removing checkpoint files of ingested events: {e}.\nTraceback: {traceback.format_exc()}",
            )

        return self.ckpt_data["data"]["records"]

    def data_collection_of_individual_logfile(
        self, all_records: List, header: Dict
    ) -> None:
        """Method to collect data for individual record Id.

        Args:
            all_records (list): list of newly fetched and remaining records
            header (dict): header to be passed in the api request.
        """
        try:
            header = dict(header)
            header["Accept-encoding"] = "gzip"
            header["X-PrettyPrint"] = "1"

            ew = event_writer.ClassicEventWriter()
            for record in all_records:
                url = f"{self.sfdc_util_ob.account_info['sfdc_server_url']}/services/data/v{self.sfdc_util_ob.account_info['sfdc_api_version']}/sobjects/EventLogFile/{record['Id']}/LogFile"
                content = None
                status_code, content = self.sfdc_util_ob.make_rest_api(url, header)
                # Handling for empty content
                if not content or status_code == 400:
                    log.log_connection_error(
                        self.logger,
                        Exception("No content or status code 400"),
                        msg_before=f"No EventlogFile data received for Record Id: {record['Id']}",
                    )
                    return

                if status_code == 404:
                    self.ckpt_data["data"]["records"].remove(record)
                    self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)
                    log.log_connection_error(
                        self.logger,
                        requests.exceptions.HTTPError("404"),
                        msg_before=f"{record['Id']} Record ID does not exist anymore. Therefore, deleting the entry for {record['Id']} Record ID from the checkpoint of input: {self.sfdc_util_ob.input_items['name']}",
                    )
                    continue

                if "\x00" in content:
                    self.logger.info(
                        "Removed NULL bytes encountered in event log file ID {}".format(
                            record["Id"]
                        )
                    )
                    content = content.replace("\x00", "")
                events = []
                csv_reader = csv.DictReader(content.splitlines())
                if not csv_reader:
                    self.logger.info("No record found in csv file %s", record["Id"])
                    continue
                general_setting = self.sfdc_util_ob.get_conf_data(
                    sc.SETTINGS_CONF_FILE, "general"
                )
                try:
                    csv_limit = int(
                        general_setting.get("csv_limit", sc.DEFAULT_CSV_LIMIT)
                    )
                    if csv_limit < 0:
                        self.logger.warning(
                            "Provided CSV limit: {} is a negative integer. Using the default CSV limit {}".format(
                                csv_limit, sc.DEFAULT_CSV_LIMIT
                            )
                        )
                        csv_limit = sc.DEFAULT_CSV_LIMIT

                    if csv_limit > sc.MAX_CSV_LIMIT:
                        self.logger.warning(
                            "Provided CSV limit {} exceeded the maximum permissible limit {}. Using the maximum limit {}".format(
                                csv_limit, sc.MAX_CSV_LIMIT, sc.MAX_CSV_LIMIT
                            )
                        )
                        csv_limit = sc.MAX_CSV_LIMIT
                except ValueError:
                    self.logger.warning(
                        "Provided CSV limit: {} in splunk_ta_salesforce_settings conf file is not a valid number. "
                        "Using the default CSV limit {}.".format(
                            general_setting.get("csv_limit"), sc.DEFAULT_CSV_LIMIT
                        )
                    )
                    csv_limit = sc.DEFAULT_CSV_LIMIT

                log_info = 'SFDCLogType="{}" SFDCLogId="{}" SFDCLogDate="{}"'.format(
                    record["EventType"], record["Id"], record["LogDate"]
                )

                csv.field_size_limit(csv_limit)
                total_records = 0

                index = self.sfdc_util_ob.input_items["index"]
                host = self.sfdc_util_ob.input_items["host"]
                source = (
                    "sfdc_event_log://EventLog_"
                    f"{self.sfdc_util_ob.account_info['name']}_"
                    f"{self.sfdc_util_ob.input_items['name']}"
                )
                sourcetype = "sfdc:logfile"
                hashed_record_id = su.get_hashed_value(record["Id"])
                for row in csv_reader:
                    total_records += 1
                    regex = "(\\d{4})(\\d{2})(\\d{2})(\\d{2})(\\d{2})(\\d{2})\\.(\\d+)"
                    m = re.match(regex, row["TIMESTAMP"])
                    event_time = "{}-{}-{}T{}:{}:{}.{}+0000".format(
                        m.group(1),
                        m.group(2),
                        m.group(3),
                        m.group(4),
                        m.group(5),
                        m.group(6),
                        m.group(7),
                    )

                    event = [event_time, log_info]
                    event.extend('{}="{}"'.format(k, v) for k, v in row.items())
                    # Appending user account id information to each eventlog
                    event.append(
                        'UserAccountId="'
                        + self.sfdc_util_ob.account_info["user_account_id"]
                        + '"'
                    )
                    event.append(
                        'SplunkRetrievedServer="'
                        + self.sfdc_util_ob.account_info["sfdc_server_url"]
                        + '"'
                    )
                    events.append(" ".join(event))
                    # Check if the batch size reached if yes then format records to event and index them
                    if len(events) > sc.EVENTS_BATCH_SIZE:
                        ew.write_events(
                            XMLEvent(
                                data,
                                index=index,
                                host=host,
                                source=source,
                                sourcetype=sourcetype,
                            )
                            for data in events
                        )
                        log.events_ingested(
                            self.logger,
                            f"{self.sfdc_util_ob.input_items['input_type']}://{self.sfdc_util_ob.account_info['name']}",
                            sourcetype,
                            len(events),
                            index,
                        )
                        events = []
                        self.logger.debug(
                            "Batch process collected %s events from csv file id=%s",
                            str(total_records),
                            record["Id"],
                        )
                # This code block is to index left over events which are not formatted/indexed when the batch size is less than 50k
                if len(events) > 0:
                    ew.write_events(
                        XMLEvent(
                            data,
                            index=index,
                            host=host,
                            source=source,
                            sourcetype=sourcetype,
                        )
                        for data in events
                    )
                    log.events_ingested(
                        self.logger,
                        f"{self.sfdc_util_ob.input_items['input_type']}://{self.sfdc_util_ob.account_info['name']}",
                        sourcetype,
                        len(events),
                        index,
                    )
                    del events
                self.logger.info(
                    "Read %s events collected from csv file id=%s",
                    str(total_records),
                    record["Id"],
                )
                # Remove ingested records from self.ckpt_data records
                self.ckpt_data["data"]["records"].remove(record)
                self.ckpt_handler.update_kv_checkpoint(self.ckpt_data)
                self.logger.debug(
                    f"Data collection completed for EventLogFile: {record['Id']}"
                )
        except Exception as e:
            log.log_exception(
                self.logger,
                e,
                "Indifidual data collection Error",
                msg_before=f"During data collection exception occured: {e}.\nTraceback: {traceback.format_exc()}",
            )

    def update_record_on_start_date_value(
        self, monitoring_interval: str, start_date: str, all_records: List[Dict]
    ) -> List[Dict]:
        """filter record whose createdDate/LogDate is same as start_date

        Args:
            monitoring_interval (string): contains details about input.
            start_date (string): start_date from
            all_records (list): list of newly fetched and remaining records

        Returns:
            list: list of records with createdDate/LogDate is same as start_date
        """
        records_on_start_date = []
        if monitoring_interval == "Hourly":
            timefield = "CreatedDate"
        else:
            timefield = "LogDate"
        for record in all_records:
            if record[timefield] == start_date:
                records_on_start_date.append(record["Id"])

        return records_on_start_date

    def filter_records(
        self, records_on_start_date: List, newly_fetched_records: List
    ) -> List:
        """This method removes the already ingested records from newly fetched records.

        Args:
            records_on_start_date (list): list of records with createdDate/LogDate is same as start_date
            newly_fetched_records (list): list of newly fetched records with createdDate/LogDate >= start_date.

        Returns:
            list: list of records after removing the already ingested records from newly fetched records.
        """
        new_records = []
        for record in newly_fetched_records:
            if record["Id"] not in records_on_start_date:
                new_records.append(record)
        return new_records

    def get_last_event_time(
        self, monitoring_interval: str, newly_fetched_records: List
    ) -> str:
        """fetch event time of the last time.

        Args:
            monitoring_interval (string): Hourly/Daily
            newly_fetched_records (list): list of newly fetched records.
        Returns:
            string: timestamp of last event.
        """
        if monitoring_interval == "Hourly":
            last_event_value = newly_fetched_records[-1]["CreatedDate"]
        else:
            last_event_value = newly_fetched_records[-1]["LogDate"]
        return last_event_value

    def build_soql_query_for_logfile_id(
        self, monitoring_interval: str, start_date: str
    ) -> str:
        """Method to build soql query to fetch events for particular logfile_Id.

        Args:
            monitoring_interval (string): monitoring interval of the input.
            start_date (string): start_date from
        Returns:
            str: query for the API request.
        """
        if monitoring_interval == "Hourly":
            soql = f"SELECT Id,EventType,LogDate,CreatedDate FROM EventLogFile WHERE CreatedDate>={start_date} AND Interval='{monitoring_interval}' ORDER BY CreatedDate LIMIT 1000"
        else:
            soql = f"SELECT Id,EventType,LogDate FROM EventLogFile WHERE LogDate>={start_date} ORDER BY LogDate LIMIT 1000"
        self.logger.info(
            f"Add-on will only collect event logs which interval is '{monitoring_interval}'"
        )
        self.logger.info(f"Query event logs soql={soql}")
        soql = urllib.parse.quote(soql)
        return soql

    def start(self) -> None:
        """Method to stream events of eventlog"""
        try:
            new_exit_gracefully = partial(
                self.exit_gracefully,
            )

            signal.signal(signal.SIGINT, new_exit_gracefully)
            signal.signal(signal.SIGTERM, new_exit_gracefully)

            # For Windows OS
            if os.name == "nt":
                signal.signal(signal.SIGBREAK, new_exit_gracefully)  # type: ignore

            self.data_collector()

        except Exception as e:
            log.log_exception(
                self.logger,
                e,
                "SfdcEventLogDataCollector start Error",
                msg_before=f"During start exception occured: {e}.\nTraceback: {traceback.format_exc()}",
            )
