#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import traceback
from time import time
from threading import Thread, Lock


import solnlib

from .constants import APP_NAME, DEVICE_API_HOST_RES_COLLECTION_NAME

from .filtering import (
    SUPPORTED_DEVICE_PROP_FILTER_TYPES,
    DEVICE_PROP_FILTER_TYPE_ENRICH,
    DEVICE_PROP_FILTER_TYPE_SKIP,
    AID_VALUE_PATTERN,
)
from .kvstore_collection import KVStoreCollection
from .logger_adapter import CSLoggerAdapter

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("event_enricher")
)


class HostResolution:
    property_exclusion_list = ("_user", "_key", "device_id")

    def __init__(
        self,
        server_uri,
        token,
        refresh_interval,
        filter_type=None,
        filter_value=None,
    ):
        self._server_uri = server_uri
        self._token = token
        self._partitions = [{}, {}]
        self._active_partition = None
        self._active_partition_index = 0
        self._refresh_interval = refresh_interval
        self._expire = None

        self._partition_switch_lock = Lock()
        self._refresh_resolution_data = None

        self.__kvstore = KVStoreCollection(
            self._server_uri, self._token, APP_NAME, DEVICE_API_HOST_RES_COLLECTION_NAME
        )

        assert filter_type is None or filter_type in SUPPORTED_DEVICE_PROP_FILTER_TYPES

        self.filter_type = filter_type
        self.filter_value = filter_value
        self.filter_descriptor = None

        if isinstance(filter_value, (set, list)):
            filter_value_set = set(self.filter_value)

        if filter_type == DEVICE_PROP_FILTER_TYPE_ENRICH:
            self.filter = lambda x: x in filter_value_set
        elif filter_type == DEVICE_PROP_FILTER_TYPE_SKIP:
            self.filter = lambda x: x not in filter_value_set
        elif filter_type is None:
            self.filter = lambda x: True
            self.filter_descriptor = "No filter, accepting all fields"

    def __str__(self) -> str:
        if self.filter_descriptor:
            return self.filter_descriptor

        return json.dumps(
            dict(filter_type=self.filter_type, filter_value=self.filter_value)
        )

    def load(self) -> None:
        if self._active_partition is None:  # first load only is not async
            self._load(in_thread=False)
            return

        refresh_delay = time() - self._expire
        if isinstance(self._expire, (int, float)) and refresh_delay > 0:
            if (
                self._refresh_resolution_data is not None
                and self._refresh_resolution_data.is_alive()
            ):
                logger.warning(
                    "Postpone host resolution information refresh as previous refresh operation is still in progress. "
                    + f"refresh interval:{self._refresh_interval}, expiration time: {self._expire}, refresh delay: {refresh_delay}"
                )
            else:
                refresh_args = dict(in_thread=True)
                self._refresh_resolution_data = Thread(
                    target=self._load, kwargs=refresh_args
                )
                self._refresh_resolution_data.start()  # all reloads are async

    def _load(self, in_thread: bool) -> None:
        start_time = time()
        if self._refresh_interval:
            self._expire = start_time + self._refresh_interval

        try:
            next_active_partition_index = (self._active_partition_index + 1) % 2
            next_active_partition = self._partitions[next_active_partition_index]
            next_active_partition.clear()

            found = self.__kvstore.search_records()
            for rec in found:
                key = rec["device_id"]
                next_active_partition[key] = {
                    f"device_{k}": v
                    for k, v in rec.items()
                    if v and k not in self.property_exclusion_list and self.filter(k)
                }

            prev_active_partition = self._active_partition
            with self._partition_switch_lock:
                self._active_partition_index = next_active_partition_index
                self._active_partition = next_active_partition
                if prev_active_partition:
                    prev_active_partition.clear()

            logger.info(
                f"enricher cache prpeparation: cache_prpeparation_time_taken={time()-start_time}, "
                + f"cache_prpeparation_run_in_thread={'Yes' if in_thread else 'No'}"
            )
        except Exception as e:
            msg = f"Unexpected error while loading collection {DEVICE_API_HOST_RES_COLLECTION_NAME} content"
            tb = " ---> ".join(traceback.format_exc().split("\n"))
            solnlib.log.log_exception(
                logger,
                e,
                "Unexpected Error Collection",
                msg_before=f"{msg} {tb}",
            )
            if not in_thread:
                raise

    def enrich(self, raw_event: str) -> str:
        if not self._active_partition:
            return raw_event

        res = AID_VALUE_PATTERN.search(raw_event)
        if res:
            device_id = res.group("aid")
            with self._partition_switch_lock:
                extras = self._active_partition.get(device_id)
            if extras:
                extras_dump = json.dumps(extras)
                return extras_dump[:-1] + "," + raw_event.lstrip()[1:]

        return raw_event
