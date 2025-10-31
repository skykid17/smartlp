#!/usr/bin/python
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

import json
import os
import time
import uuid
import datetime
from enum import Enum
from os import path
from threading import Lock, Thread
from typing import Dict, Optional

from cattrs import ClassValidationError, transform_error

import import_declare_test  # noqa: F401
from azure.identity import ClientSecretCredential
from splunksdc import logging
from splunksdc.collector import SimpleCollectorV1
from splunksdc.utils import LogExceptions, LogWith

from azure.eventhub import (  # isort: skip
    CheckpointStore,
    EventHubConsumerClient,
    TransportType,
)  # isort: skip
from splunksdc.config import (  # isort: skip
    BooleanField,
    IntegerField,
    StanzaParser,
    StringField,
    LogLevelField,
    ConfigManager,
)  # isort: skip

import mscs_consts
from splunk_ta_mscs.models import (
    ProxyConfig,
    AzureAccountConfig,
    AzureStorageAccountConfig,
    format_validation_exception,
)
from mscs_storage_service import (
    _create_blob_checkpoint_store_service,
)
from splunk_ta_mscs.mscs_credential_provider import get_credential

logger = logging.get_module_logger()


class FileLock:
    """
    A FileLock that synchronizes the access to a shared file from multiple processes.

    This class leverages `os.lockf` on POSIX compatible system and `msvcrt.locking` on Windows.
    it has also implemented the interface of Context Manager for convenience.
    """

    def __init__(self, fd, size):
        self._fd = fd
        self._size = size

    @classmethod
    def _ms_locking(cls, fd, size, lock):
        import msvcrt

        flag = msvcrt.LK_LOCK if lock else msvcrt.LK_UNLCK
        msvcrt.locking(fd, flag, size)

    @classmethod
    def _posix_locking(cls, fd, size, lock):
        flag = os.F_LOCK if lock else os.F_ULOCK
        os.lockf(fd, flag, size)

    _locking = _ms_locking if os.name == "nt" else _posix_locking

    def __enter__(self):
        os.lseek(self._fd, 0, os.SEEK_SET)
        self._locking(self._fd, self._size, True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.fsync(self._fd)
        os.lseek(self._fd, 0, os.SEEK_SET)
        self._locking(self._fd, self._size, False)


class SyncBy:
    """
    A handful decorator for synchronize the call to a callee by a coordinator function.
    """

    def __init__(self, coordinator):
        self._coordinator = coordinator

    def __call__(self, callee):
        def _wrapper(this, *args, **kwargs):
            return self._coordinator(this, callee, *args, **kwargs)

        return _wrapper


class CheckpointSize(Enum):
    # File size of checkpointer with that many partitions
    PARTITIONS_64 = 528384
    PARTITIONS_100 = 823296
    PARTITIONS_1024 = 8392704


class SharedLocalCheckpoint:
    # TODO: Refactor to 1 partition per file
    """
    A SharedLocalCheckpoint that is responsible for persisting the changes of ingestion status to a local file.

    The segmented structure makes partial updating has a constant IO cost.
    """

    def __init__(self, fullname):
        self._lock = Lock()
        self._fd = os.open(fullname, os.O_RDWR | os.O_CREAT)
        self._pages_of_header = 1
        self._number_of_partition = 100
        self._pages_per_partition = 2
        self._number_of_page = (
            self._pages_of_header
            + self._number_of_partition * self._pages_per_partition
        )
        # The typical block size of most Linux systems is 4KB
        self._page_size = 4096
        self._padding = b"\x20"
        self._file_size = self._number_of_page * self._page_size
        self._now = time.time
        self._uuid = uuid.uuid4

    def close(self):
        os.close(self._fd)

    def _get_page_index(self, partition_id, slot):
        if 100 > partition_id >= self._number_of_partition:
            self._initialize(force_partitions=100)
        elif 1024 > partition_id >= self._number_of_partition:
            self._initialize(force_partitions=1024)

        assert (
            partition_id < self._number_of_partition
            and slot < self._pages_per_partition
        )
        return self._pages_of_header + self._pages_per_partition * partition_id + slot

    def _write(self, index, data):
        page_size = self._page_size
        data_size = len(data)
        if data_size > page_size:
            raise ValueError("Data doesn't not fit into one page")
        if data_size < page_size:
            data = data + self._padding * (page_size - data_size)
        offset = index * page_size
        os.lseek(self._fd, offset, os.SEEK_SET)
        os.write(self._fd, data)

    def _write_record(self, index, *args):
        record = [str(self._uuid()), int(self._now())]
        record.extend(args)
        data = json.dumps(record, ensure_ascii=True).encode()
        self._write(index, data)
        return record

    def _read(self, index):
        page_size = self._page_size
        pos = index * page_size
        os.lseek(self._fd, pos, os.SEEK_SET)
        return os.read(self._fd, page_size)

    def _read_record(self, index):
        data = self._read(index)
        if not data.startswith(b"["):
            data = b"[]"
        return json.loads(data)

    def _if_match_origin(self, index, origin):
        record = self._read_record(index)
        if not record:
            if not origin:
                return True
            return False
        return record[0] == origin

    def _lock_thread_and_file(self, func, *args, **kwargs):
        with self._lock:
            with FileLock(self._fd, self._file_size):
                return func(self, *args, **kwargs)

    def _set_partition_size(self, number_of_partition):
        self._number_of_partition = number_of_partition
        self._number_of_page = (
            self._pages_of_header
            + self._number_of_partition * self._pages_per_partition
        )
        self._file_size = self._number_of_page * self._page_size

    def _initialize(self, force_partitions=0):
        # To make it backwards compatible I cannot touch the header inside the file
        # or the name of the file, so I will do it from the filesize which is constant
        header = [4096, 1, 2, 64, 1 + 64 * 2]

        try:
            file_size = os.path.getsize(self._fd)

            # The ratio over the file_size is just to make sure OS won't make any weird things
            if file_size > 0.6 * CheckpointSize.PARTITIONS_1024.value:
                # 1024 partition is the biggest, so we need to extend file
                self._set_partition_size(1024)
                return
            elif (
                0.9 * CheckpointSize.PARTITIONS_100.value
                < file_size
                < 0.6 * CheckpointSize.PARTITIONS_1024.value
            ):
                if force_partitions == 1024:
                    # File is 100p, but needs to be extended to 1024
                    self._set_partition_size(1024)
            elif 0 < file_size < 0.9 * CheckpointSize.PARTITIONS_100.value:
                if force_partitions == 100:
                    # File is 64p, but we need to extend it to 100p
                    self._set_partition_size(100)
                else:
                    # 64 partition is the lowest, so do not truncate it
                    self._set_partition_size(64)
                    return
        except OSError:  # If the file doesn't exist
            logger.debug("EventHub checkpointer doesn't exist")
            pass

        page_size = self._page_size
        pos = self._number_of_page * page_size
        os.lseek(self._fd, pos, os.SEEK_SET)

        record = self._read_record(0)
        if not record:
            self._write_record(0, *header)

        if not record or force_partitions > 0:
            os.ftruncate(self._fd, self._file_size)

    @SyncBy(_lock_thread_and_file)
    def initialize(self, force_max_partitions=False):
        # Taken out, as twice SyncBy breaks it completely
        self._initialize(force_max_partitions)

    @SyncBy(_lock_thread_and_file)
    def read_partition_ownerships(self):
        result = []
        for i in range(self._number_of_partition):
            index = self._get_page_index(i, 0)
            ownership = self._read_record(index)
            if not ownership:
                continue
            result.append([i, ownership])
        return result

    @SyncBy(_lock_thread_and_file)
    def update_partition_ownership(self, partition_id, owner_id, origin):
        index = self._get_page_index(partition_id, 0)
        if self._if_match_origin(index, origin):
            return self._write_record(index, owner_id)
        return []

    @SyncBy(_lock_thread_and_file)
    def read_partition_checkpoints(self):
        result = []
        for i in range(self._number_of_partition):
            index = self._get_page_index(i, 1)
            checkpoint = self._read_record(index)
            if not checkpoint:
                continue
            result.append([i, checkpoint])
        return result

    @SyncBy(_lock_thread_and_file)
    def update_partition_checkpoint(self, partition_id, offset, sequence_number):
        index = self._get_page_index(partition_id, 1)
        return self._write_record(index, offset, sequence_number)


class LocalFileCheckpointStore(CheckpointStore):
    """
    This class is an implementation of `azure.eventhub.CheckpointStore`.

    It uses SharedLocalCheckpoint to store the partition ownership and checkpoint data.
    """

    @classmethod
    def open(cls, workspace, fully_qualified_namespace, eventhub_name, consumer_group):
        urn = [fully_qualified_namespace, eventhub_name, consumer_group]
        filename = "-".join(urn) + ".v1.ckpt"
        fullname = path.join(workspace, filename)
        checkpoint = SharedLocalCheckpoint(fullname)
        checkpoint.initialize()
        return cls(*urn, checkpoint=checkpoint)

    def __init__(
        self, fully_qualified_namespace, eventhub_name, consumer_group, checkpoint
    ):
        self._fully_qualified_namespace = fully_qualified_namespace
        self._eventhub_name = eventhub_name
        self._consumer_group = consumer_group
        self._checkpoint = checkpoint

    def _validate_source(
        self, fully_qualified_namespace, eventhub_name, consumer_group
    ):
        return all(
            [
                self._fully_qualified_namespace == fully_qualified_namespace,
                self._eventhub_name == eventhub_name,
                self._consumer_group == consumer_group,
            ]
        )

    def list_ownership(self, fully_qualified_namespace, eventhub_name, consumer_group):
        assert self._validate_source(
            fully_qualified_namespace, eventhub_name, consumer_group
        )

        result = []
        ownership_list = self._checkpoint.read_partition_ownerships()
        for partition_id, ownership in ownership_list:
            etag, last_modified, owner_id = ownership
            result.append(
                {
                    "fully_qualified_namespace": fully_qualified_namespace,
                    "eventhub_name": eventhub_name,
                    "consumer_group": consumer_group,
                    "partition_id": str(partition_id),
                    "owner_id": owner_id,
                    "etag": etag,
                    "last_modified_time": last_modified,
                }
            )
        return result

    def claim_ownership(self, ownership_list):
        ownership_acquired = []
        for ownership in ownership_list:
            assert self._validate_source(
                *[
                    ownership[key]
                    for key in [
                        "fully_qualified_namespace",
                        "eventhub_name",
                        "consumer_group",
                    ]
                ]
            )

            partition_id = int(ownership["partition_id"])
            owner_id = ownership["owner_id"]
            etag = ownership.get("etag")

            record = self._checkpoint.update_partition_ownership(
                partition_id, owner_id, etag
            )
            if not record:
                continue
            ownership["etag"] = record[0]
            ownership["last_modified_time"] = record[1]
            ownership_acquired.append(ownership)

        return ownership_acquired

    def list_checkpoints(
        self, fully_qualified_namespace, eventhub_name, consumer_group
    ):
        assert self._validate_source(
            fully_qualified_namespace, eventhub_name, consumer_group
        )

        result = []
        checkpoint_list = self._checkpoint.read_partition_checkpoints()
        for partition_id, checkpoint in checkpoint_list:
            _, _, offset, sequence_number = checkpoint
            result.append(
                {
                    "fully_qualified_namespace": fully_qualified_namespace,
                    "eventhub_name": eventhub_name,
                    "consumer_group": consumer_group,
                    "partition_id": str(partition_id),
                    "offset": offset,
                    "sequence_number": sequence_number,
                }
            )
        return result

    def update_checkpoint(self, checkpoint):
        assert self._validate_source(
            *[
                checkpoint[key]
                for key in [
                    "fully_qualified_namespace",
                    "eventhub_name",
                    "consumer_group",
                ]
            ]
        )
        partition_id = int(checkpoint["partition_id"])
        offset = checkpoint["offset"]
        sequence_number = checkpoint["sequence_number"]
        self._checkpoint.update_partition_checkpoint(
            partition_id, offset, sequence_number
        )


class SettingsConfiguration:
    """
    This utility class is responsible for holding Logging information across the full life cycle of an input.
    """

    @classmethod
    def load(cls, config):
        """Loads MSCS settings."""
        content = config.load(
            "splunk_ta_mscs_settings", stanza="logging", use_cred=True
        )
        parser = StanzaParser([LogLevelField("agent", default="INFO")])
        settings = parser.parse(content)
        return cls(settings)

    def __init__(self, settings):
        self._settings = settings

    def get_log_level(self):
        """Get log level."""
        return self._settings.agent


class EventHubConsumerHandler:
    WithSystemProperties = 1
    WithPartitionID = 2
    WithConsumerGroup = 4

    """
    This class bridges events from an `EventHubConsumerClient` to a Splunk event writer.
    """

    def __init__(
        self,
        event_hub_consumer,
        event_writer,
        max_wait_time,  # type: int
        max_batch_size,  # type: int
        event_format_flags,  # type: int
        ensure_ascii,  # type: bool
    ):
        self._event_hub_consumer = event_hub_consumer
        self._event_writer = event_writer
        self._thread = Thread(target=self._work_proc)
        self._max_wait_time = max_wait_time
        self._max_batch_size = max_batch_size
        self._event_format_flags = event_format_flags
        self._ensure_ascii = ensure_ascii
        self._encoding = "utf-8"
        self._main_context = logging.ThreadLocalLoggingStack.top()
        self._next_logging_time = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=5
        )
        # Dictionary to store event counts for each partition
        self._partition_event_counts = {}
        self.event_not_json = 0

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._event_hub_consumer.close()
        self._event_hub_consumer = None
        self._thread.join()

    def is_alive(self):
        return self._thread.is_alive()

    def _has_set(self, flag):
        return self._event_format_flags & flag

    def _format_source(self, context):
        params = {
            "endpoint": "eventhub://{namespace}/{entity};".format(
                namespace=context.fully_qualified_namespace,
                entity=context.eventhub_name,
            ),
            "partition_id": "partition_id={};".format(context.partition_id)
            if self._has_set(self.WithPartitionID)
            else "",
            "consumer_group": "consumer_group={};".format(context.consumer_group)
            if self._has_set(self.WithConsumerGroup)
            else "",
        }
        source = "{endpoint}{partition_id}{consumer_group}".format(**params)
        return source

    def _format_json_pair(self, key, value):
        key = json.dumps(key, ensure_ascii=self._ensure_ascii)
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=self._ensure_ascii)
        elif not value.startswith("{") or not value.endswith("}"):
            value = json.dumps(value, ensure_ascii=self._ensure_ascii)
        return "{}:{}".format(key, value)

    @staticmethod
    def _normalize_event(event):
        try:
            body = event.body
            if isinstance(body, bytes):
                return [body]
            return [line for line in body]
        except ValueError:
            logger.warn("The event content is empty.")
        return []

    def _decode_event(self, event):
        for line in self._normalize_event(event):
            try:
                yield line.decode(self._encoding)
            except UnicodeDecodeError:
                logger.warn("An error occured during decoding the event.")
                yield line.hex()

    def _format_event(self, event, body):
        if self._has_set(self.WithSystemProperties):
            pairs = [self._format_json_pair("body", body)]
            for props in [event.system_properties, event.properties]:
                if not props:
                    continue
                for key, value in props.items():
                    key = key.decode() if isinstance(key, bytes) else key
                    value = (
                        value.decode("utf-8", "backslashreplace")
                        if isinstance(value, bytes)
                        else value
                    )
                    pairs.append(self._format_json_pair(key, value))
            return "".join(["{", ",".join(pairs), "}"])
        elif isinstance(body, str):
            return body
        else:
            return json.dumps(body, ensure_ascii=self._ensure_ascii)

    def _select_elements(self, source, event):
        event_count = 0
        decoded_events = "".join([line for line in self._decode_event(event)])
        is_event_body_json = False
        volume = 0
        try:
            event_body = json.loads(decoded_events)
            is_event_body_json = True
        except ValueError:
            self.event_not_json = self.event_not_json + 1

        if is_event_body_json and isinstance(event_body, dict):
            if "records" in event_body and isinstance(
                event_body["records"], (list, set, tuple)
            ):
                for val in event_body["records"]:
                    data = self._format_event(event, val)
                    volume += self._event_writer.write_fileobj(data, source=source)
                    event_count += 1
            else:
                data = self._format_event(event, event_body)
                volume = self._event_writer.write_fileobj(data, source=source)
                event_count += 1
        else:
            data = self._format_event(event, decoded_events)
            volume = self._event_writer.write_fileobj(data, source=source)
            event_count += 1
        return event_count, volume

    def _on_event_batch(self, context, event_batch):
        current_partition = context.partition_id
        if current_partition not in self._partition_event_counts:
            self._partition_event_counts[current_partition] = {
                "event_count": 0,
                "event_volume": 0,
            }

        if event_batch:
            source = self._format_source(context)
            for event in event_batch:
                event_count, event_volume = self._select_elements(source, event)
                self._partition_event_counts[current_partition][
                    "event_count"
                ] += event_count
                self._partition_event_counts[current_partition][
                    "event_volume"
                ] += event_volume

            context.update_checkpoint()
        self._log_events_periodically()

    def _log_events_periodically(self, is_aborted=False):
        if is_aborted:
            self._log_partition_events()
        else:
            cur_time = datetime.datetime.utcnow()
            if cur_time >= self._next_logging_time:
                self._log_partition_events()
                self._next_logging_time = cur_time + datetime.timedelta(minutes=5)

    def _log_partition_events(self):
        for partition, data in self._partition_event_counts.items():
            event_count = data["event_count"]
            event_volume = data["event_volume"]
            logger.info(
                "Ingested events. ",
                partition_id=partition,
                event_count=event_count,
                event_volume=event_volume,
            )
            logger.debug(
                f"Splunk Event message body is not JSON - parsing as text. Times: {self.event_not_json}"
            )
            self.event_not_json = 0
        self._partition_event_counts.clear()

    @property
    def main_context(self):
        return self._main_context

    @LogWith(prefix=main_context)
    def _work_proc(self):

        logger.info(
            "Start collecting events.",
            max_wait_time=self._max_wait_time,
            max_batch_size=self._max_batch_size,
        )
        while self._event_hub_consumer:
            self._event_hub_consumer.receive_batch(
                on_event_batch=self._on_event_batch,
                max_wait_time=self._max_wait_time,
                max_batch_size=self._max_batch_size,
                # "-1" is from the beginning of the partition.
                starting_position="-1",
            )


class EventHubDataInput:
    """
    The facade class for an instance of Azure Event Hub input.

    Simply creating components with corresponding arguments and wire them up all together.
    """

    # TODO: Refactor the structure of EventHub modinput, why is everything JIT processed and merged together

    def __init__(self, stanza):
        self._kind = stanza.kind
        self._name = stanza.name
        self._args = stanza.content
        self._start_time = int(time.time())

    @property
    def name(self):
        return self._name

    @property
    def start_time(self):
        return self._start_time

    def _extract_arguments(self, parser):
        return parser.parse(self._args)

    def _get_account_name(self):
        parser = StanzaParser(
            [
                StringField("account", required=True),
            ]
        )
        args = self._extract_arguments(parser)
        return args.account

    @staticmethod
    def _get_https_scheme(proxy: ProxyConfig) -> Dict[str, Optional[str]]:
        if not proxy.enabled:
            return {}
        return {"https": proxy.url}

    def _create_credentials(
        self, config: ConfigManager, proxy: ProxyConfig
    ) -> ClientSecretCredential:
        proxies = self._get_https_scheme(proxy)
        account_name = self._get_account_name()
        content = config.load(
            "splunk_ta_mscs_azureaccount",
            stanza=account_name,
            virtual=True,
            use_cred=True,
        )
        account = AzureAccountConfig.from_dict(content)
        credential = get_credential(account, proxies)
        return credential

    def _try_creating_blob_checkpoint_store(
        self, config: ConfigManager, proxy: ProxyConfig
    ):
        parser = StanzaParser(
            [
                BooleanField("blob_checkpoint_enabled", default=False),
                StringField("storage_account", default=""),
                StringField("container_name", default=""),
            ]
        )
        args = self._extract_arguments(parser)
        if not args.blob_checkpoint_enabled:
            logger.info("Blob checkpoint store not configured")
            return None

        logger.info("Blob checkpoint store has been configured")
        logger.debug(" container_name: " + str(args.container_name))

        if not (args.storage_account and args.container_name):
            logger.warn(
                "Either Storage Account or Storage Container Name not provided for Blob "
                "Checkpointing"
            )
            return None

        try:
            storage_account_name = args.storage_account
            content_storage = config.load(
                "splunk_ta_mscs_storageaccount",
                stanza=storage_account_name,
                virtual=True,
                use_cred=True,
            )
            storage_account = AzureStorageAccountConfig.from_dict(content_storage)
            proxies = self._get_https_scheme(proxy)

            blob_service_checkpoint = _create_blob_checkpoint_store_service(
                storage_account=storage_account,
                container_name=args.container_name,
                proxies=proxies,
            )
            return blob_service_checkpoint
        except ClassValidationError as e:
            logger.error(
                f"Failed to validate Azure Account model for the account: {storage_account_name}. Error details: {transform_error(e, format_exception=format_validation_exception)}",
                exc_info=e,
            )
            return None
        except Exception as e:
            logger.error(
                f"Unknown exception occurred while getting Azure Storage Account from config",
                exc_info=e,
            )
            return None

    def _extract_transport_type(self):
        parser = StanzaParser(
            [BooleanField("use_amqp_over_websocket", default=True, rename="aow")]
        )
        args = self._extract_arguments(parser)
        if args.aow:
            return TransportType.AmqpOverWebsocket
        return TransportType.Amqp

    def _extract_force_amqp_over_proxy(self):
        parser = StanzaParser(
            [BooleanField("force_amqp_over_proxy", default=False, rename="aop")]
        )
        args = self._extract_arguments(parser)
        return bool(args.aop)

    def _extract_ensure_ascii(self):
        """Backwards compatibility requires ensure_ascii to be True, while in UI it defaults False"""
        parser = StanzaParser([BooleanField("ensure_ascii", default=True, rename="ea")])
        args = self._extract_arguments(parser)
        return bool(args.ea)

    def isExists(
        self, workspace, fully_qualified_namespace, eventhub_name, consumer_group
    ):
        urn = [fully_qualified_namespace, eventhub_name, consumer_group]
        filename = "-".join(urn) + ".v1.ckpt"
        fullname = path.join(workspace, filename)
        if path.isfile(fullname):
            return True
        return False

    def _create_event_hub_consumer(
        self,
        workspace: str,
        config: ConfigManager,
        credential: ClientSecretCredential,
        proxy: ProxyConfig,
    ):
        parser = StanzaParser(
            [
                StringField("event_hub_namespace", required=True),
                StringField("event_hub_name", required=True),
                StringField("consumer_group", default="$Default"),
            ]
        )
        args = self._extract_arguments(parser)
        checkpoint_store = self._try_creating_blob_checkpoint_store(config, proxy)

        if not checkpoint_store:
            checkpoint_store = LocalFileCheckpointStore.open(
                workspace,
                args.event_hub_namespace,
                args.event_hub_name,
                args.consumer_group,
            )
        elif not checkpoint_store.list_checkpoints(
            args.event_hub_namespace, args.event_hub_name, args.consumer_group
        ):
            logger.info(" LocalFileCheckpoint file Exists ")

            if self.isExists(
                workspace,
                args.event_hub_namespace,
                args.event_hub_name,
                args.consumer_group,
            ):

                # if checkpoint list is empty then needs to try to migrate.
                checkpoint_store_source = LocalFileCheckpointStore.open(
                    workspace,
                    args.event_hub_namespace,
                    args.event_hub_name,
                    args.consumer_group,
                )
                try:

                    migrate_checkpoints(
                        checkpoint_store_source,
                        checkpoint_store,
                        args.event_hub_namespace,
                        args.event_hub_name,
                        args.consumer_group,
                    )
                except Exception as ex:
                    raise Exception(ex)
        else:
            logger.info("checkpoint using blob storage and already migrated")

        http_proxy = None
        transport_type = self._extract_transport_type()
        if proxy.enabled and not (
            transport_type == TransportType.Amqp
            and self._extract_force_amqp_over_proxy()
        ):
            http_proxy = {
                "proxy_hostname": proxy.host,
                "proxy_port": proxy.port,
                "username": proxy.username,
                "password": proxy.password,
            }

        client = EventHubConsumerClient(
            args.event_hub_namespace,
            args.event_hub_name,
            args.consumer_group,
            credential=credential,
            http_proxy=http_proxy,
            checkpoint_store=checkpoint_store,
            transport_type=transport_type,
            partition_ownership_expiration_interval=300,
        )
        return client

    def _create_event_writer(self, app):
        stanza = self._kind + "://" + self._name
        parser = StanzaParser(
            [
                StringField("sourcetype", default="mscs:azure:eventhub"),
                StringField("index"),
                StringField("host"),
                StringField("stanza", fillempty=stanza),
            ]
        )
        args = self._extract_arguments(parser)
        return app.create_event_writer(sourcetype=args.sourcetype, index=args.index)

    def _create_eventhub_consumer_handler(self, consumer, event_writer):
        parser = StanzaParser(
            [
                IntegerField("max_wait_time", default=10, lower=5, upper=20),
                IntegerField("max_batch_size", default=300, lower=150, upper=10000),
                IntegerField("event_format_flags", default=0),
            ]
        )
        args = self._extract_arguments(parser)
        ensure_ascii = self._extract_ensure_ascii()
        return EventHubConsumerHandler(
            consumer, event_writer, **vars(args), ensure_ascii=ensure_ascii
        )

    @LogWith(datainput=name, start_time=start_time)
    @LogExceptions(
        logger, "Data input was interrupted by an unhandled exception.", lambda e: -1
    )
    def run(self, app, config: ConfigManager):
        settings = SettingsConfiguration.load(config)
        logger.setLevel(settings.get_log_level())

        workspace = app.workspace()
        proxy_settings = config.load(
            "splunk_ta_mscs_settings",
            stanza=mscs_consts.PROXY,
            virtual=True,
            use_cred=True,
        )
        proxy = ProxyConfig.from_dict(proxy_settings)
        credential = self._create_credentials(config, proxy)
        consumer = self._create_event_hub_consumer(workspace, config, credential, proxy)

        # calling get_eventhub_properties on consumer in order to check whether parameters are valid or not
        try:
            consumer.get_eventhub_properties()
        except Exception as exc:
            logger.error(f"Error occurred while connecting to eventhub: {exc}")
            return 0

        event_writer = self._create_event_writer(app)
        with self._create_eventhub_consumer_handler(consumer, event_writer) as handler:
            while handler.is_alive():
                if app.is_aborted():
                    break
                time.sleep(1.0)
            handler._log_events_periodically(is_aborted=True)
        return 0


def migrate_checkpoints(
    source, destination, fully_qualified_namespace, eventhub_name, consumer_group
):
    """
    migrates a checkpoint from one storage to the other.

    :param  CheckpointStore source
    :param  CheckpointStore destination
    :param str fully_qualified_namespace: The fully qualified namespace that the Event Hub belongs to.
        The format is like "<namespace>.servicebus.windows.net".
    :param str eventhub_name: The name of the specific Event Hub the checkpoints are associated with, relative to
        the Event Hubs namespace that contains it.
    :param str consumer_group: The name of the consumer group the checkpoints are associated with.
    :rtype: Iterable[Dict[str,Any]], Iterable of dictionaries containing partition checkpoint information:

    """
    logger.info("migration: Starting migration of event hub checkpoint")
    if not (source and destination):
        return True

    checkpoints = source.list_checkpoints(
        fully_qualified_namespace, eventhub_name, consumer_group
    )
    logger.info(f"migration: {len(checkpoints)} checkpoints to migrate")

    # exit if there is nothing in the source. Maybe new input
    if len(checkpoints) == 0:
        return True

    # copy each checkpoint to new storage
    for checkpoint in checkpoints:
        logger.debug("migration: update", checkpoint=checkpoint)
        destination.update_checkpoint(checkpoint)
    logger.info("migration: migration complete")
    # will throw exeption if input can not continue.
    return True


def modular_input_run(app, config: ConfigManager):
    stanza = app.inputs()[0]
    data_input = EventHubDataInput(stanza)
    return data_input.run(app, config)


def main():
    arguments = {
        "account": {"title": "The Azure Account Name"},
        "event_hub_namespace": {"title": "The Azure Event Hub Namespace (FQDN)"},
        "event_hub_name": {"title": "The Azure Event Hub Name"},
        "consumer_group": {"title": "The Azure Event Hub Consume Group"},
        "blob_checkpoint_enabled": {
            "title": "Enabling EventHub Blob Checkpointing Checkbox"
        },
        "storage_account": {"title": "Storage Account  "},
        "container_name": {
            "title": "Storage Blob Container name for EventHub checkpoint"
        },
        "max_wait_time": {
            "title": "The maximum interval in seconds that the event processor will wait before processing"
        },
        "max_batch_size": {
            "title": "The maximum number of events that would be retrieved in one batch"
        },
        "event_format_flags": {
            "title": "The bitwise flags that determines the format of output events"
        },
        "use_amqp_over_websocket": {
            "title": "The switch that allow using AMQP over WebSocket"
        },
        "ensure_ascii": {
            "title": "The switch that allows enforce ASCII encoding of ingested events"
        },
        "force_amqp_over_proxy": {
            "title": "The switch that allows to override the proxy with AMQP configuration"
        },
        "export_status": {
            "title": "Export status of EventHub modinput to Data Manager"
        },
    }

    SimpleCollectorV1.main(
        modular_input_run,
        title="Azure Event Hub",
        use_single_instance=False,
        arguments=arguments,
    )
