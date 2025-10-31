#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import copy
import time
import os
import json
from datetime import datetime, timedelta
from splunksdc import logging
from .endpoints import get_endpoint, NON_REPORT_CONTENT_TYPES, REPORT_CONTENT_TYPES
from splunk_ta_o365.common.checkpoint import KVStoreCheckpoint, FileBasedCheckpoint
from .consts import DEFAULT_QUERY_WINDOW_SIZE, DEFAULT_RETRY_LIST
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from splunk_ta_o365.common.utils import time_to_string, string_to_time
import re
import urllib.parse


logger = logging.get_module_logger()

"""
    class GraphApiConsumer
    This class is used to make calls to the Microsoft Graph API to retrieve reports and then ingest the events using an eventwriter to splunk.
"""

DEFAULT_START_DATE = datetime.utcnow() - timedelta(days=7)
MIGRATION_START_DATE = datetime.utcnow() - timedelta(days=4)
DEFAULT_DELAY_THROTTLE = 2


class GraphApiConsumer(object):
    def __init__(
        self, name, app, config, event_writer, portal, proxy, token, input_args
    ):
        """
        Manages retrieving and ingesting graph api data based on the endpoint

        Args:
            name (str): input name
            app (SimpleCollectorV1): Object of splunksdc.collector.SimpleCollectorV1
            config (ConfigManager): Object of splunksdc.config.ConfigManager
            event_writer (XMLEventWriter|HECWriter): event_writer to ingest the event in the splunk.
            portal (MSGraphPortalCommunications): This is an class that make api calls
            proxy (Proxy): A proxy with session for making REST calls
            token (O365TokenProvider): A token with credentials for validating the session
        """
        self._app = app
        self._name = name
        self._proxy = proxy
        self._token = token
        self._portal = portal
        self._service = config._service
        self._event_writer = event_writer
        self._now = time.time
        self._input_args = input_args

    def get_checkpoint_collection(self, name: str):
        """
        This method used to create and load the KVstore collection

        Args:
            name (str): KVstore collection name
        """
        self._collection = KVStoreCheckpoint(name, self._service)
        self._collection.get_collection()

    def load_filebased_checkpoint(self):
        """
        This method used to load the legacy file-based checkpoint if checkpoint file exists.
        This method only used by the Audit and ServiceAnnouncement Input.
        """
        checkpoint_file: str = os.path.join(
            self._app._context.checkpoint_dir, self._name + ".ckpt"
        )
        if os.path.exists(checkpoint_file):
            self._legacy_checkpoint = FileBasedCheckpoint(checkpoint_file)
            self._legacy_checkpoint.load_checkpoint()
        else:
            self._ckpt["is_migrated"] = True

    def delete_legacy_report_checkpoint(self):
        """
        This method used to delete the legacy checkpoint file for Graph report endpoints inputs.
        """
        try:
            checkpoint_file: str = os.path.join(
                self._app._context.checkpoint_dir, self._name + ".ckpt"
            )
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
                logger.info(
                    "Successfully removed stale checkpoint file.",
                    input_name=self._name,
                )
        except Exception as ex:
            logger.warn(
                "Exception occured while removing the file.", input_name=self._name
            )

    def get_query_window_and_ts_format(
        self,
        checkpoint,
        look_back_days,
        start_date,
        content_type,
        ts_format="%Y-%m-%dT%H:%M:%SZ",
    ):
        """
        This method used to update the query parameter for Audit and ServiceAnnouncement input.

        Args:
            checkpoint (dict): Contains the checkpoint related information
            look_back_days (int): default look back time to consider for query start time
            ts_format (str, optional): timestamp format. Defaults to "%Y-%m-%dT%H:%M:%SZ".

        Returns:
            Returns the query window start and end time for API call.
        """
        qs_time = checkpoint["last_event_timestamp"]
        qe_time = datetime.utcnow()
        if self.is_content_type_audit_sign_in(content_type):
            delay_throttle_min = int(self._input_args.get("delay_throttle_min", 0))
            qe_time = datetime.utcnow() - timedelta(minutes=delay_throttle_min)
        else:
            qe_time = datetime.utcnow()

        if str(qs_time).find(".") != -1:
            ts_format = "%Y-%m-%dT%H:%M:%S.%fZ"

        if not qs_time:
            qs_time = time_to_string(
                ts_format, (qe_time - timedelta(days=look_back_days))
            )
            if start_date:
                qs_time = start_date
            checkpoint["last_event_timestamp"] = qs_time

        qe_time = time_to_string(ts_format, qe_time)
        return qs_time, qe_time, ts_format

    def update_session(self):
        """
        This method used to check if the token expired or it's about to expire
        """
        if self._token.need_retire(600):
            logger.info("Access token will expire soon.")
            self._token.auth(self._session)

    def ingest(self, event):
        """
        This used to ingest the events into the splunk

        Args:
            event (dict): unique event
        """
        self._event_writer.write_event(
            json.dumps(event, ensure_ascii=False),
            source=self._endpoint["source"],
            sourcetype=self._endpoint["sourcetype"],
        )

    def get_audit_service_data(self, next_link):
        """
        This method used to communicate with portal and retreive the data
        for AduitLogs and ServiceAnnouncement Input.

        Returns:
            Return the response value and nextLink from the API response
        """
        self.update_session()
        reports = self._portal.o365_graph_api(
            params=self._endpoint["params"],
            content_parser=self._endpoint["content_parser"],
            path=self._endpoint["path"],
        )
        items, next_link = reports.throttled_get(self._session, next_link)
        return items, next_link

    def ingest_audit_service_data(self, items):
        """
        This method used to ingest the data of the Audit and ServiceAnnouncement inputs.

        Args:
            items (list[dict]): response data of the API

        Returns:
            str: Timestamp of last ingested event

        Raises:
            ex: Raise the exception to parent method if any.
        """
        try:
            ingested_events_count = skipped_count = 0
            event_count_offset = self._ckpt["event_count_offset"]
            event_timestamp = ""

            for event in items:
                if not self._ckpt["is_migrated"] and self._legacy_checkpoint.get(
                    self._endpoint.get("message_factory")(event)
                ):
                    event_timestamp = event[self._endpoint["query_field"]]
                    logger.debug(f"Skipping the existing event : {event['id']}")
                    skipped_count += 1
                elif event_count_offset > 0:
                    logger.debug(f"Skipping the existing event : {event['id']}")
                    event_count_offset -= 1
                    skipped_count += 1
                else:
                    self.ingest(event)
                    event_timestamp = event[self._endpoint["query_field"]]
                    ingested_events_count += 1
                    self._ckpt["event_count_offset"] += 1

            if len(items) != 0:
                self._ckpt["event_count_offset"] = 0
                self._ckpt["last_event_timestamp"] = event_timestamp

            logger.info(
                "Total events summary.",
                received_events_count=len(items),
                skipped_count=skipped_count,
                ingested_events_count=ingested_events_count,
            )
        except Exception as ex:
            logger.info(
                "Exception occurred while ingesting the data. Total events summary.",
                received_events_count=len(items),
                skipped_count=skipped_count,
                ingested_events_count=ingested_events_count,
            )
            raise ex
        return event_timestamp

    def is_process_in_chunks(
        self, qs_time, qe_time, query_window_size, ts_format, content_type
    ):
        """
        Checks whether to process given window in chunks or not

        Args:
            qs_time (str): Value of query_start_time
            qe_time (str): Value of query_end_time
            query_window_size (int): Value of query_window_size
            ts_format (str): Timestamp format

        Returns:
            [True|False]: Whether to process given window in chunks or not
        """
        # For non audit sign in input query_window_size would be none
        if not query_window_size and not self.is_content_type_audit_sign_in(
            content_type
        ):
            return False

        # Convert qs_time and qe_time to datetime if they are not already
        if isinstance(qs_time, str):
            qs_time = string_to_time(ts_format, qs_time)
        if isinstance(qe_time, str):
            qe_time = string_to_time(ts_format, qe_time)

        # Calculate the total duration between qs_time and qe_time
        total_duration = qe_time - qs_time

        # Check if the total duration is greater than the query_window_size
        return total_duration > timedelta(minutes=query_window_size)

    def paginate_audit_service_data(self):
        """
        Paginate the API received response of given chunk

        Raises:
            ex: Raise the exception to parent method if any.

        Returns:
            str: Returns timestamp of last processed event
        """
        # Page number indicates which page is currently being processed
        current_page_number = (
            self._ckpt["page_number"] - 1 if self._ckpt["nextLink"] else -1
        )

        # Process pages flag indicates whether to process pages or skip the already ingested pages
        process_pages = True

        # Fetch nextLink from checkpoint
        next_link = self._ckpt["nextLink"]

        while True:
            try:
                self._items, next_link = self.get_audit_service_data(next_link)
            except Exception as ex:
                if hasattr(ex, "_status_code") and ex._status_code == "400":
                    logger.warning(
                        f"Encountered error, regenerating query window. StatusCode={ex._status_code}, ErrorCode={ex._code}, ErrorMessage={ex._err_message}"
                    )

                    # Extract start time and end time from nextLink containing invalid skiptoken
                    decoded_next_link = urllib.parse.unquote(next_link)
                    qs_time, qe_time = (
                        re.findall(
                            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
                            decoded_next_link,
                        )
                    )[0:2]

                    # Update query parameters with same time window
                    self._endpoint["params"]["$filter"] = self._endpoint["params"][
                        "$filter"
                    ].format(qs_time, qe_time)

                    # Update process pages flag to skip pages
                    # Set current page number to -1 as we start fresh query window
                    # Discard nextLink
                    process_pages, current_page_number, next_link = False, -1, None

                    # Skip following steps and start fresh invocation
                    continue
                else:
                    raise ex

            # Increase the page number count to indicate the new page being processed
            current_page_number += 1

            # Check if need to skip pages or process pages - If not process pages, then skip already ingested pages
            if not process_pages:
                if current_page_number < int(self._ckpt["page_number"]):
                    logger.debug(
                        f"Skipped page {current_page_number}, as data is already ingested."
                    )
                    continue

                # Enable processing pages once ingested pages are skipped
                process_pages = True
                if current_page_number > 0:
                    logger.info(
                        f"Skipped all the pages from 0 to {current_page_number-1}, as data is already ingested."
                    )

            self._ckpt["page_number"] = current_page_number
            last_event_timestamp = self.ingest_audit_service_data(self._items)

            # Update nextLink and corresponding page_number
            self._ckpt["nextLink"], self._ckpt["page_number"] = (
                next_link,
                self._ckpt["page_number"] + 1 if next_link else -1,
            )

            if not next_link:
                return last_event_timestamp

    def save_checkpoint_info(self):
        """Save checkpoint details to KVStore"""
        self._collection.batch_save([self._ckpt])
        logger.info("Saved the checkpoint data.", checkpoint=self._ckpt)

    def delete_file_checkpoint(self):
        """Removes file based checkpoint depending on migration status"""
        if not self._ckpt["is_migrated"]:
            self._legacy_checkpoint.close()
            self._legacy_checkpoint.delete(self._legacy_checkpoint._filename)
            logger.info(
                "Successfully removed stale checkpoint file.", input_name=self._name
            )
            self._ckpt["is_migrated"] = True

    def is_content_type_audit_sign_in(self, content_type):
        """
        Returns True if the value of content_type is auditlogs.signins

        Args:
            content_type (str): Value of content_type

        Returns:
            [True|False]: Returns either true or false based on value of content_type
        """
        return content_type.lower() == "auditlogs.signins"

    def reset_audit_sign_in_checkpoint(
        self, content_type, query_window_size, start_date
    ):
        """
        Resets the checkpoint for auditlogs.signin content_type

        Args:
            content_type (str): Value of content_type
            query_window_size (int): Value of query_window_size

        Returns:
            tuple: Tuple containing three values qs_time,qe_time and ts_format
        """
        qs_time, qe_time, ts_format = None, None, None
        if (
            self.is_content_type_audit_sign_in(content_type)
            and self._ckpt.get("query_window_size") is None
        ):
            self._ckpt["query_window_size"] = query_window_size
            # If there is already nextlink present in the checkpoint then discard it and fetch the data with chunking
            # Extract start time and end time from nextLink containing skiptoken
            next_link = self._ckpt.get("nextLink")
            if next_link:
                ts_format = "%Y-%m-%dT%H:%M:%SZ"
                # Reset Checkpoint values to their default state
                self._ckpt["nextLink"] = str()
                self._ckpt["page_number"] = -1
                self._ckpt["event_count_offset"] = int()
                qs_time, qe_time, ts_format = self.get_query_window_and_ts_format(
                    self._ckpt, self._endpoint["look_back"], start_date
                )

        return qs_time, qe_time, ts_format

    def update_query_window_size(self, content_type, query_window_size):
        """
        If the query_window_size is changed in between update its value by comparing it with conf

        Args:
            content_type (str): Value of content_type
            query_window_size (int): Query window size value from conf

        Returns:
            int: Updated value of query_window_size
        """
        if self.is_content_type_audit_sign_in(content_type) and self._ckpt.get(
            "query_window_size"
        ):
            query_window_from_kv = self._ckpt["query_window_size"]
            query_window_from_conf = query_window_size
            next_link = self._ckpt.get("nextLink")
            if (
                query_window_from_kv
                and query_window_from_kv != query_window_from_conf
                and next_link
            ):
                logger.warning(
                    "Data collection of last window was not completed and Query Window Size is updated. This might lead to data duplication."
                )
                query_window_size = query_window_from_conf
                # Reset Checkpoint values to their default state
                self._ckpt["nextLink"] = str()
                self._ckpt["page_number"] = -1
                self._ckpt["event_count_offset"] = int()
                self._ckpt["query_window_size"] = query_window_size
                self._collection.batch_save([self._ckpt])
                logger.info(f"Checkpoint reset successful.", checkpoint_data=self._ckpt)
                self._ckpt = self._collection.get(self._ckpt_key)
        return query_window_size

    def update_ckpt_with_last_event_timestamp(
        self, last_event_timestamp, ts_format, api_event_timestamp_format=None
    ):
        if api_event_timestamp_format:
            last_et = string_to_time(api_event_timestamp_format, last_event_timestamp)
        else:
            last_et = string_to_time(ts_format, last_event_timestamp)
        last_et += timedelta(seconds=1)
        self._ckpt["last_event_timestamp"] = time_to_string(ts_format, last_et)
        return last_et

    def audit_service_data_collector(self, start_date, query_window_size, content_type):
        """
        This method is used to collect the data of AuditLogs and serviceAnnouncement input

        Raises:
            ex: if there is any exception then raise it to parent method.
        """
        try:
            original_filter = copy.deepcopy(self._endpoint["params"]["$filter"])
            # Load File-based Checkpoint if migration is not completed
            if not self._ckpt["is_migrated"]:
                self.load_filebased_checkpoint()

            # Add page number field for exsting inputs transition
            if self._ckpt.get("page_number") is None:
                self._ckpt["nextLink"] = str()
                self._ckpt["page_number"] = -1

            qs_time, qe_time, ts_format = self.reset_audit_sign_in_checkpoint(
                content_type, query_window_size, start_date
            )
            query_window_size = self.update_query_window_size(
                content_type, query_window_size
            )
            self._ckpt["query_window_size"] = query_window_size
            self.save_checkpoint_info()
            # Update the filter Query if nextlink not present in the checkpoint and collect the data
            if not self._ckpt["nextLink"]:
                if not qs_time and not qe_time and not ts_format:
                    qs_time, qe_time, ts_format = self.get_query_window_and_ts_format(
                        self._ckpt,
                        self._endpoint["look_back"],
                        start_date,
                        content_type,
                    )

                if qs_time > qe_time:
                    logger.info(
                        f"Start Datetime is greater than the calculated UTC end datetime(current_utc_date_time - delay_throttle_min) hence Skipping. start_date={qs_time}, end_date={qe_time}"
                    )
                    return

                if self.is_process_in_chunks(
                    qs_time, qe_time, query_window_size, ts_format, content_type
                ):
                    qs_date_time = string_to_time(ts_format, qs_time)
                    qe_date_time = string_to_time(ts_format, qe_time)
                    chunk_start_date_time = qs_date_time
                    while True:
                        chunk_end_date_time = chunk_start_date_time + timedelta(
                            minutes=query_window_size
                        )
                        if chunk_end_date_time > qe_date_time:
                            chunk_end_date_time = qe_date_time
                        self._endpoint["params"]["$filter"] = original_filter.format(
                            time_to_string(ts_format, chunk_start_date_time),
                            time_to_string(ts_format, chunk_end_date_time),
                        )
                        last_event_timestamp = self.paginate_audit_service_data()
                        if last_event_timestamp:
                            chunk_start_date_time = (
                                self.update_ckpt_with_last_event_timestamp(
                                    last_event_timestamp, ts_format
                                )
                            )
                        else:
                            self._ckpt["last_event_timestamp"] = time_to_string(
                                ts_format, chunk_end_date_time
                            )
                            chunk_start_date_time = chunk_end_date_time
                        self.save_checkpoint_info()
                        if chunk_start_date_time >= qe_date_time:
                            self.delete_file_checkpoint()
                            return

                else:
                    self._endpoint["params"]["$filter"] = original_filter.format(
                        qs_time, qe_time
                    )
            last_event_timestamp = self.paginate_audit_service_data()
            if last_event_timestamp:
                api_event_timestamp_format = None
                if str(last_event_timestamp).find(".") != -1:
                    api_event_timestamp_format = "%Y-%m-%dT%H:%M:%S.%fZ"
                self.update_ckpt_with_last_event_timestamp(
                    last_event_timestamp, ts_format, api_event_timestamp_format
                )
            self.delete_file_checkpoint()
        except Exception as ex:
            raise ex
        finally:
            self.save_checkpoint_info()

    def get_batch_size(self):
        """
        This method used to get the max batch size from the limits.conf file
        By default it will return 1000 if not specified.

        Returns:
            int: return the max_documents_per_batch_save value from the conf file
        """
        batch_size: int = int(
            self._service.confs["limits"]["kvstore"].content.get(
                "max_documents_per_batch_save", 1000
            )
        )
        return batch_size

    def get_report_data(self):
        """
        This method used to communicate with portal and retreive the data
        For reports inputs.

        Returns:
            list[dict]: return list of events
        """
        reports = self._portal.o365_graph_api_report(self._endpoint["report_name"])
        items = reports.throttled_get(self._session)
        return items

    def ingest_report_data(self, items, batch_size):
        """This used the ingests and save checkpoint in the collection using batch calls.

        Args:
            items (list[dict]): list of events
            batch_size (int): max size of the batch list

        Raises:
            ex: if there is any exception, then raise it to parent method
        """
        try:
            batch_ckpt_list: list = []
            ingested_events_count = skipped_count = 0

            for event in items:
                key = self._endpoint.get("message_factory")(event)

                if self._collection.get(key):
                    logger.debug(f"Skipping the existing event : {key}")
                    skipped_count += 1
                else:
                    # add in a timestamp to each response item before recording to an event.
                    event.update(
                        {"timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
                    )
                    self.ingest(event)
                    ingested_events_count += 1

                    batch_ckpt_list.append(
                        {"_key": key, "expiration": int(self._time + 604800)}
                    )

                if len(batch_ckpt_list) == batch_size:
                    self._collection.batch_save(batch_ckpt_list)
                    batch_ckpt_list.clear()
        except Exception as ex:
            raise ex
        finally:
            if batch_ckpt_list:
                self._collection.batch_save(batch_ckpt_list)

            if ingested_events_count:
                logger.info("Successfully saved checkpoint data.")

            self._collection.delete({"expiration": {"$lt": self._time}})
            logger.debug("Stale Checkpoints swept Successfully")

            logger.info(
                "Total events summary.",
                received_events_count=len(items),
                skipped_count=skipped_count,
                ingested_events_count=ingested_events_count,
            )

    def ingest_report_data_by_date(self, items, date, is_migrated):
        """This used the ingests and save checkpoint in the collection using batch calls.

        Args:
            items (list[dict]): list of events

        Raises:
            ex: if there is any exception, then raise it to parent method
        """
        try:
            events_count = 0

            for event in items:
                # add in a timestamp to each response item before recording to an event.
                event.update(
                    {"timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
                )
                events_count += 1
                self.ingest(event)
        except Exception as ex:
            raise ex
        finally:
            if not self._ckpt.get(self._ckpt_key):
                self._ckpt.save(
                    {
                        "_key": self._ckpt_key,
                        "state": json.dumps(
                            {
                                "report_date": date,
                                "no_of_events": events_count,
                                "is_migrated": is_migrated,
                            }
                        ),
                    }
                )
            else:
                self._ckpt.update(
                    self._ckpt_key,
                    {
                        "state": json.dumps(
                            {
                                "report_date": date,
                                "no_of_events": events_count,
                                "is_migrated": is_migrated,
                            }
                        )
                    },
                )

            if events_count:
                logger.info("Successfully saved checkpoint data.")

            logger.info(
                "Total events summary.",
                date=date,
                received_events_count=len(items),
                ingested_events_count=events_count,
            )

    def get_report_date(self, is_migrated: bool):
        """Get report date to start the data collection.
        Returns:
        date: Return the date object
        """
        report_date = None
        date_today = datetime.utcnow()
        ckpt = self._ckpt.get(self._ckpt_key)
        ckpt_date = None

        # check if checkpoint is not created and input start date is configured.
        if not ckpt and self._input_args.get("start_date"):
            ckpt_date = self._input_args["start_date"]

        # check if ckpt is already present
        elif ckpt and ckpt.get("state", {}):
            ckpt_date = json.loads(ckpt.get("state", {})).get("report_date", None)

        # convert report date to datetime format
        if ckpt_date:
            report_date = datetime.strptime(ckpt_date, "%Y-%m-%d")
            if report_date.date() < (date_today - timedelta(days=27)).date():
                report_date = date_today - timedelta(days=27)
                logger.info(
                    "As checkpointed report_date={} is older than 28 days hence resetting the report_date={}".format(
                        ckpt_date, report_date.strftime("%Y-%m-%d")
                    )
                )

        # use default start date if ckpt_date is not defined
        else:
            logger.info(f"is_migrated: {is_migrated}")
            report_date = (
                MIGRATION_START_DATE if not is_migrated else DEFAULT_START_DATE
            )
        return report_date.date()

    def update_migration_flag(self):
        """Function to update the Migration flag."""

        state = json.loads(self._ckpt.get(self._ckpt_key)["state"])
        report_date = datetime.strptime(state["report_date"], "%Y-%m-%d")
        if not state.get(
            "is_migrated"
        ) and report_date.date() >= datetime.utcnow().date() - timedelta(
            days=self.delay_throttle
        ):
            self._ckpt.update(
                self._ckpt_key,
                {
                    "state": json.dumps(
                        {
                            "report_date": state.get("report_date"),
                            "no_of_events": state.get("no_of_events"),
                            "is_migrated": True,
                        }
                    )
                },
            )
            logger.info("Successfully updated the is_migrated flag with the checkpoint")

    def report_data_collector_by_date(self, content_type, is_migrated):
        """
        This method used to collect the data of report endpoint input.

        Args:
            content_type (str): report endpoint content type
            is_migrated (bool): input KVStore collection migration  status
        """
        logger.info(
            "Collect content_type={} by function=report_data_collector_by_date".format(
                content_type
            )
        )

        report_date = self.get_report_date(is_migrated)
        self.delay_throttle = int(
            self._input_args.get("delay_throttle", DEFAULT_DELAY_THROTTLE)
        )
        end_date = (
            datetime.utcnow().today() - timedelta(days=self.delay_throttle)
        ).date()
        logger.info(
            "Current Checkpoint State={}".format(self._ckpt.get(self._ckpt_key))
        )

        if report_date > end_date:
            logger.info(
                f"Report Start date is greater than the End date(Today - Delay_throttle days). Hence skipping the data collection. report_date={report_date}, end_date={end_date}"
            )
            return

        # Collect the data until report_date <= (Today - delay throttle days)
        while report_date <= end_date:
            date = report_date.strftime("%Y-%m-%d")
            self._endpoint.update(
                {
                    "report_name": get_endpoint(content_type)["report_name"].format(
                        content_type, date
                    )
                }
            )

            # Make the API call and get the report data
            logger.debug(f"Requested to get report data. endpoint={self._endpoint}")
            items = self.get_report_data()
            logger.debug(f"Received report data. endpoint={self._endpoint}")

            # Break the look if report_date==end_date and no_of_events is same as the downloaded report items
            if self._ckpt.get(self._ckpt_key):
                state = json.loads(self._ckpt.get(self._ckpt_key)["state"])
                if (
                    state.get("report_date")
                    and date == state["report_date"]
                    and len(items)
                    == json.loads(self._ckpt.get(self._ckpt_key)["state"]).get(
                        "no_of_events"
                    )
                ):
                    logger.info(
                        f"No new events found for the date={date}. Hence skipping the event ingestion."
                    )
                    report_date = report_date + timedelta(days=1)
                    continue

            # Ingest the report data
            logger.debug(f"Send report data to index. report_date={date}")
            self.ingest_report_data_by_date(items, date, is_migrated)
            logger.debug(f"Ingested report data successfully. report_date={date}")
            report_date = report_date + timedelta(days=1)

        logger.info(
            f"Successfully collected the report data for content_type={content_type}"
        )
        # Update the migration flag
        self.update_migration_flag()
        logger.info(f"Saved checkpoint info.", state=self._ckpt.get(self._ckpt_key))

    def delete_legacy_kv_report_checkpoint(self, is_migrated):
        """
        This method used to delete the legacy KV Store collection
        """
        try:
            if is_migrated:
                KVStoreCheckpoint.delete_collection(
                    self._service.kvstore, self._ckpt_key
                )
        except Exception as e:
            logger.error(
                f"Error while deleting the Legacy KVStore Collection. collection={self._ckpt_key}",
                exception=e,
            )
            raise

    def report_data_collector(self, content_type):
        """
        This method used to collect the data of report endpoint input.

        Args:
            content_type (str): report endpoint content type
        """
        # update url for report endpoint inputs
        self._endpoint["report_name"] = self._endpoint["report_name"].format(
            content_type
        )
        # get the max batch save from limits.conf if specified else default 1000
        batch_size = self.get_batch_size()
        # Make the API call and get the report data
        items = self.get_report_data()
        # Ingest the report data
        self.ingest_report_data(items, batch_size)

    def get_audit_sign_in_chunk_params(self):
        start_date = self._input_args.get("start_date")
        query_window_size = int(self._input_args.get("query_window_size", 0))
        if start_date:
            start_date += "Z"
        if query_window_size == 0:
            # Provide chunk parameter for inputs before upgrade
            query_window_size = DEFAULT_QUERY_WINDOW_SIZE
        return start_date, query_window_size

    def run(self, content_type):
        """
        This method used to handle the flow input execution based on content-type of the input.
        It will also create the KVstore collection if not exists.

        Args:
            content_type (str): input content-type
        """
        try:
            self._time = self._now()

            logger.debug(
                "Start Retrieving Graph Api Messages.",
                timestamp=self._now(),
                report=content_type,
            )

            # Create Session Object
            self._session = self._proxy.create_requests_session()
            self._session = self._token.auth(self._session)
            adapter = HTTPAdapter(
                max_retries=Retry(
                    total=5,
                    backoff_factor=1,
                    allowed_methods=None,
                    status_forcelist=DEFAULT_RETRY_LIST,
                )
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
            # Load the input endpoint
            self._endpoint: dict = get_endpoint(content_type)

            if content_type.lower() in NON_REPORT_CONTENT_TYPES:
                start_date, query_window_size = None, None
                if self.is_content_type_audit_sign_in(content_type):
                    (
                        start_date,
                        query_window_size,
                    ) = self.get_audit_sign_in_chunk_params()
                # KVstore configuration
                self._ckpt_key: str = f"{content_type}_{self._name}"
                self.get_checkpoint_collection(self._endpoint["collection_name"])
                self._ckpt = self._collection.get(self._ckpt_key) or {
                    "_key": self._ckpt_key,
                    "event_count_offset": int(),
                    "last_event_timestamp": str(),
                    "is_migrated": bool(),
                    "nextLink": str(),
                    "page_number": -1,
                }
                logger.debug("Current checkpoint.", current_checkpoint=self._ckpt)

                # Collect the Audit and ServiceAnnouncement data
                self.audit_service_data_collector(
                    start_date, query_window_size, content_type
                )

            elif content_type.lower() in REPORT_CONTENT_TYPES:
                # KVStore Configuration
                collection_name: str = "splunk_ta_o365_graph_api_logs"
                self._ckpt_key: str = f"splunk_ta_o365_{content_type}_{self._name}"
                self.get_checkpoint_collection(collection_name)
                self._ckpt = self._collection

                # Set the is_migrated flag based on checkpoint status
                if not self._ckpt.get(self._ckpt_key) or not json.loads(
                    self._ckpt.get(self._ckpt_key)["state"]
                ).get("is_migrated", False):
                    is_migrated: bool = False
                else:
                    is_migrated: bool = True

                # Collect the data using report_data_collector_by_date
                self.report_data_collector_by_date(content_type, is_migrated)

                # Delete the legacy checkpoint
                self.delete_legacy_report_checkpoint()
                self.delete_legacy_kv_report_checkpoint(is_migrated)

            else:
                # KVStore Configuration
                collection_name: str = f"splunk_ta_o365_{content_type}_{self._name}"
                self.get_checkpoint_collection(collection_name)

                # Collect the data
                self.report_data_collector(content_type)
                # Delete the legacy checkpoint
                self.delete_legacy_report_checkpoint()

            logger.debug(
                "End Retrieving Graph Api Messages.",
                timestamp=self._now(),
                report=content_type,
            )
        except Exception as e:
            logger.error("Error retrieving Graph API Messages.", exception=e)
            raise
