#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import time
import traceback
import solnlib
from queue import Queue
from threading import Thread
from .kvstore_collection import KVStoreCollection
from .crowdstrike_helpers import CrowdStrikeClient
from .logger_adapter import CSLoggerAdapter
from typing import Callable, Dict, Any

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("device_api_inventory_sync")
)

DEVICES_INFO_DEFAULT_CHUNK_SIZE = 50

collection_fields = frozenset(
    [
        "agent_load_flags",
        "agent_local_time",
        "agent_version",
        "bios_manufacturer",
        "bios_version",
        "build_number",
        "chassis_type",
        "chassis_type_desc",
        "cid",
        "config_id_base",
        "config_id_build",
        "config_id_platform",
        "connection_ip",
        "connection_mac_address",
        "cpu_signature",
        "default_gateway_ip",
        "device_id",
        "external_ip",
        "first_seen",
        "group_hash",
        "hostname",
        "instance_id",
        "kernel_version",
        "last_seen",
        "local_ip",
        "mac_address",
        "major_version",
        "minor_version",
        "modified_timestamp",
        "os_build",
        "os_product_name",
        "os_version",
        "platform_id",
        "platform_name",
        "pointer_size",
        "product_type",
        "product_type_desc",
        "provision_status",
        "reduced_functionality_mode",
        "serial_number",
        "service_pack_minor",
        "service_provider",
        "service_provider_account_id",
        "status",
        "system_manufacturer",
        "system_product_name",
        "zone_group",
    ]
)


class StopSyncOperationIteration(StopIteration):
    pass


def device_sync_operation_thread(sync_operation_fn: Callable) -> Callable:
    def device_sync_operation_thread_wrapper(*args: Any, **kvargs: Any):
        while True:
            try:
                sync_operation_fn(*args, **kvargs)
            except StopSyncOperationIteration:
                break
            except Exception as e:
                msg = f"Device API inventory sync, sync_action=log_error, sync_operation={sync_operation_fn.__name__}, exception={e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger,
                    e,
                    "Device API Inventory Sync Error",
                    msg_before=f"{msg} {tb}",
                )
                break

    return device_sync_operation_thread_wrapper


class DeviceApiInventorySync:
    def __init__(self, cs_config, splunk_config):
        self._client_crowdstrike = CrowdStrikeClient(**cs_config)
        self._client_kvstore = KVStoreCollection(**splunk_config)

        self._queue_cs_device_info = Queue()
        self._queue_kvstore_lookup = Queue()
        self._queue_kvstore_create = Queue()
        self._queue_kvstore_update = Queue()
        self._queue_kvstore_delete = Queue()

    @device_sync_operation_thread
    def kvstore_create_entries(self) -> None:
        dvc = self._queue_kvstore_create.get()
        if dvc is None:
            self._queue_kvstore_create.task_done()
            raise StopSyncOperationIteration()

        logger.debug(
            f"Device API inventory sync, sync_action=kvstore_create_entries, device_count={len(dvc)}"
        )
        self._client_kvstore.batch_save(dvc)
        self._queue_kvstore_create.task_done()

    @device_sync_operation_thread
    def kvstore_update_entries(self) -> None:
        dvc = self._queue_kvstore_update.get()
        if dvc is None:
            self._queue_kvstore_update.task_done()
            raise StopSyncOperationIteration()

        logger.debug(
            f"Device API inventory sync, sync_action=kvstore_update_entries, device_count={len(dvc)}"
        )
        self._client_kvstore.batch_save(dvc)
        self._queue_kvstore_update.task_done()

    @device_sync_operation_thread
    def kvstore_delete_entry(self) -> None:
        data = self._queue_kvstore_delete.get()
        if data is None:
            self._queue_kvstore_delete.task_done()
            raise StopSyncOperationIteration()

        _key, device_id, cid = data
        logger.debug(
            f"Device API inventory sync, sync_action=kvstore_delete_entry, _key='{_key}', cid='{cid}' device_id='{device_id}'"
        )
        self._client_kvstore.delete_records(key=_key)
        self._queue_kvstore_delete.task_done()

    @device_sync_operation_thread
    def kvstore_search_entries(self) -> None:
        devices = self._queue_kvstore_lookup.get()
        if devices is None:
            self._queue_kvstore_create.put(None)
            self._queue_kvstore_update.put(None)
            self._queue_kvstore_delete.put(None)
            self._queue_kvstore_lookup.task_done()
            raise StopSyncOperationIteration()

        if len(devices) > 0:
            cid = devices[0]["cid"]
            id2info = {dvc["device_id"]: dvc for dvc in devices}
            queue = {
                "cid": cid,
                "$or": [{"device_id": id} for id in id2info.keys()],
            }

            logger.debug(
                f"Device API inventory sync, sync_action=kvstore_search_entries, queue='{json.dumps(queue)}'"
            )

            found = self._client_kvstore.search_records(query=queue)

            updated = set()
            update_list, delete_list, create_list = [], [], []
            for dvc in found:
                device_id, cid = dvc["device_id"], dvc["cid"]

                info = id2info.pop(device_id, None)
                if info:
                    data_to_save = {
                        k: v for k, v in info.items() if k in collection_fields
                    }
                    dvc.update(data_to_save)
                    update_list.append(dvc)
                    updated.add((device_id, cid))
                elif (device_id, cid) in updated:
                    delete_list.append((dvc["_key"], device_id, cid))

            if update_list:
                self._queue_kvstore_update.put(update_list)

            for info in id2info.values():
                create_list.append(
                    {k: v for k, v in info.items() if k in collection_fields}
                )

            if create_list:
                self._queue_kvstore_create.put(create_list)

            for dvc in delete_list:
                self._queue_kvstore_delete.put(dvc)

        self._queue_kvstore_lookup.task_done()

    @device_sync_operation_thread
    def crowdstrike_collect_device_info(self) -> None:
        id_chunk = self._queue_cs_device_info.get()
        if id_chunk is None:
            self._queue_kvstore_lookup.put(None)
            self._queue_cs_device_info.task_done()
            raise StopSyncOperationIteration()

        logger.debug(
            f"Device API inventory sync, sync_action=crowdstrike_collect_device_info, device_ids='{id_chunk}'"
        )
        info_chunk = self._client_crowdstrike.get_device_chunk_info(id_chunk)
        self._queue_kvstore_lookup.put(info_chunk)
        self._queue_cs_device_info.task_done()

    def run(
        self, time_check_point: str, chunk_size: int = DEVICES_INFO_DEFAULT_CHUNK_SIZE
    ) -> int:
        start_time = time.time()
        logger.info(
            f"Device API inventory sync, sync_action=device_api_sync_start, time_checkpoint='{time_check_point}'"
        )

        if not self._client_kvstore.check_collection_exists():
            raise Exception(
                f"Collection '{self._client_kvstore.collection_name}' is not available"
            )

        pipeline = [
            Thread(target=self.crowdstrike_collect_device_info),
            Thread(target=self.kvstore_search_entries),
            Thread(target=self.kvstore_create_entries),
            Thread(target=self.kvstore_update_entries),
            Thread(target=self.kvstore_delete_entry),
        ]

        for stage in pipeline:
            stage.start()

        buffer = []
        for chunk, _, total in self._client_crowdstrike.find_devices_changed_after(
            time_check_point
        ):
            logger.debug(
                f"Device API inventory sync, sync_action=list_updated_devices, device_id_chunk_size={len(chunk)}, device_id_chunk='{chunk}'"
            )

            buffer += chunk
            while len(buffer) >= chunk_size:
                self._queue_cs_device_info.put(buffer[:chunk_size])
                buffer = buffer[chunk_size:]

        if len(buffer) > 0:
            self._queue_cs_device_info.put(buffer)

        self._queue_cs_device_info.put(None)

        for stage in pipeline:
            stage.join()

        logger.info(
            f"Device API inventory sync, sync_action=device_api_sync_done, sync_devices_updated={total}, sync_time_taken={time.time()-start_time}"
        )
        return total
