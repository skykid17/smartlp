#!/usr/bin/python
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
# splunk

SESSION_KEY = "session_key"
SERVER_URI = "server_uri"
CHECKPOINT_DIR = "checkpoint_dir"

# global_settings
GLOBAL_SETTINGS = "global_settings"

# mscs_settings
AGENT = "agent"
PERFORMANCE_TUNING_SETTINGS = "performance_tuning_settings"
WORKER_THREADS_NUM = "worker_threads_num"

QUERY_END_TIME_OFFSET = "query_end_time_offset"
QUERY_END_TIME_OFFSET_DEFAULT_VALUE = 180
EVENT_CNT_PER_ITEM = "event_cnt_per_item"
EVENT_CNT_PER_ITEM_DEVAULT_VALUE = 100

LIST_TABLES_PAGE_SIZE = "list_tables_page_size"
QUERY_ENTITIES_PAGE_SIZE = "query_entities_page_size"
QUERY_ENTITIES_PAGE_SIZE_DEFAULT_VALUE = 1000

LIST_BLOBS_PAGE_SIZE = "list_blobs_page_size"
GET_BLOB_BATCH_SIZE = "get_blob_batch_size"
GET_BLOB_BATCH_SIZE_DEFAULT_VALUE = 120000

LIST_MANAGEMENT_EVENTS_PAGE_SIZE = "list_management_events_page_size"

HTTP_TIMEOUT = "http_timeout"

# proxy
PROXY = "proxy"
PROXY_TYPE = "proxy_type"
PROXY_URL = "proxy_url"
PROXY_PORT = "proxy_port"
PROXY_USERNAME = "proxy_username"
PROXY_PASSWORD = "proxy_password"
PROXY_ENABLED = "proxy_enabled"

PROXY_HOST_PATTERN = r"""^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]*[A-Za-z0-9])$"""

# inputs
STANZA_NAME = "stanza_name"
TABLE_LIST = "table_list"
TABLE_NAME = "table_name"
START_TIME = "start_time"
DESCRIPTION = "description"

CONTAINER_NAME = "container_name"
BLOB_LIST = "blob_list"
LOG_TYPE = "log_type"
GUIDS = "guids"
APPLICATION_INSIGHTS = "application_insights"
EXCLUDE_BLOB_LIST = "exclude_blob_list"
BLOB_NAME = "blob_name"
INCLUDE_SNAPSHOTS = "include_snapshots"
SNAPSHOTS_START_TIME = "snapshots_start_time"
SNAPSHOTS_END_TIME = "snapshots_end_time"
SNAPSHOT = "snapshot"

BLOB_TYPE = "blob_type"
BLOB_MODE = "blob_mode"
BLOB_MODE_RANDOM = "random"
BLOB_MODE_APPEND = "append"
BLOB_MODE_LIST = [BLOB_MODE_RANDOM, BLOB_MODE_APPEND]
BLOB_COMPRESSION = "blob_compression"
BLOB_NOT_COMPRESSED = "not_compressed"
BLOB_COMPRESSION_EXT = "extension_based"
BLOB_COMPRESSION_GZIP = "gzip"
BLOB_COMPRESSION_LIST = [
    BLOB_NOT_COMPRESSED,
    BLOB_COMPRESSION_EXT,
    BLOB_COMPRESSION_GZIP,
]
DONT_REUPLOAD_BLOB_SAME_SIZE = "dont_reupload_blob_same_size"
DECODING = "decoding"
COLLECTION_INTERVAL = "collection_interval"
LINE_BREAKER = "line_breaker"
BATCH_SIZE = "batch_size"
BLOB_CREATION_TIME = "blob_creation_time"
BLOB_SIZE = "blob_size"
ETAG = "etag"
PREFIX = "prefix"
CHUNK_SIZE = 100
READ_TIMEOUT = "read_timeout"
BLOB_SCHEDULER_BLOCK_TIME = 21600
BLOB_SCHEDULER_BLOCK_TIME_APPEND = 300
# is_migrated was used in task config as checkpoint migration flag
IS_MIGRATED = "is_migrated"
# file_to_kv_migrated is used in KV Store as checkpoint migration flag
FILE_TO_KV_MIGRATED = "file_to_kv_migrated"
FILE_TO_KV_MIGRATION_LOCK = "file_to_kv_migration_lock"
FILE_TO_KV_MIGRATION_LAST_MIGRATED_BLOB = "file_to_kv_migration_last_migrated_blob"
BLOB_INPUT_HELP_LINK = "blob_input_help_link"

SUBSCRIPTION_RESOURCE_TYPE = "subscriptions"
RESOURCE_GRAPH_RESOURCE_TYPE = "resource_graph"
TOPOLOGY_RESOURCE_TYPE = "topology"

SUBSCRIPTION_ID = "subscription_id"
RESOURCE_TYPE = "resource_type"
RESOURCE_GROUP_LIST = "resource_group_list"
NETWORK_WATCHER_NAME = "network_watcher_name"
NETWORK_WATCHER_RESOURCE_GROUP = "network_watcher_resource_group"
TARGET_RESOURCE_GROUP = "target_resource_group"
RESOURCE_GRAPH_QUERY = "resource_graph_query"
RESOURCE_GRAPH_API_TYPE = "metrics_resources"

INDEX = "index"
SOURCETYPE = "sourcetype"

# checkpoint
QUERY_START_TIME = "query_start_time"
QUERY_END_TIME = "query_end_time"
PAGE_LINK = "page_link"
CUR_PARTITIONKEY = "cur_partitionkey"
CUR_ROWKEY = "cur_rowkey"
CUR_TIMESTAMP = "cur_timestamp"
STATUS = "status"

RECEIVED_BYTES = "received_bytes"
LAST_MODIFIED = "last_modified"
IS_COMPLETED = "is_completed"
CODESET = "codeset"

CUR_INDEX = "cur_index"

# storage account
ACCOUNT = "account"
ACCOUNTS = "accounts"
ACCOUNT_NAME = "account_name"
ACCOUNT_SECRET_TYPE = "account_secret_type"
ACCOUNT_SECRET = "account_secret"
ACCOUNT_CLASS_TYPE = "account_class_type"

# azure account
CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
DISABLED = "disabled"
TENANT_ID = "tenant_id"

# api_settings
API_SETTINGS = "api_settings"
URL = "url"
INSTANCE_VIEW_URL = "instance_view_url"
NETWORK_WATCHER_URL = "network_watcher_url"
API_VERSION = "api_version"
AZURE_CLOUD_PUBLIC_MANAGEMENT_URL = "https://management.azure.com/"
AZURE_CLOUD_GOV_MANAGEMENT_URL = "https://management.usgovcloudapi.net/"
AZURE_CLOUD_PUBLIC_LOG_ANALYTICS_URL = "https://api.loganalytics.io"
AZURE_CLOUD_GOV_LOG_ANALYTICS_URL = "https://api.loganalytics.us"
AZURE_CLOUD_PUBLIC_BLOB_URL = "https://{account_name}.blob.core.windows.net"
AZURE_CLOUD_GOV_BLOB_URL = "https://{account_name}.blob.core.usgovcloudapi.net"
AZURE_CLOUD_PUBLIC_TABLE_URL = "https://{account_name}.table.core.windows.net"
AZURE_CLOUD_GOV_TABLE_URL = "https://{account_name}.table.core.usgovcloudapi.net"
PUBLISHER_ID = "2ed28a74-1f6f-4829-8530-fe359c77d35c"

AUDIT = "audit"

# azure cloud parameters
LOG_ANALYTICS_ENDPOINT = "log_analytics"


class CheckpointStatusType:
    CUR_PAGE_ONGOING = "cur_page_ongoing"

    CUR_PAGE_DONE = "cur_page_done"

    ALL_DONE = "all_done"


GLOBAL_FIELD_NAMES_STORAGE_TABLE = [
    EVENT_CNT_PER_ITEM,
    QUERY_END_TIME_OFFSET,
    QUERY_ENTITIES_PAGE_SIZE,
]
GLOBAL_FIELD_NAMES_STORAGE_BLOB = [
    WORKER_THREADS_NUM,
    GET_BLOB_BATCH_SIZE,
]
