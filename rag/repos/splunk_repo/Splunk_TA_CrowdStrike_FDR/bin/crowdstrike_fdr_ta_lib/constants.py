#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

APP_NAME = "Splunk_TA_CrowdStrike_FDR"
SESSION_KEY = "session_key"
SERVER_URI = "server_uri"
SERVER_HOST = "server_host"
APP = "__app"

DEVICE_API_HOST_RES_COLLECTION_NAME = (
    "crowdstrike_ta_host_resolution_device_api_collection"
)
DEVICE_API_HOST_RES_REFRESH_INTERVAL = 300  # every 5 minutes ingest modinput will refresh host resolution infotmaion dict from above kvstore collection


HOST_RES_COLLECTION_NAME = "crowdstrike_ta_combined_host_resolution_collection"
HOST_RES_LOCAL_COLLECTION_CSV = "crowdstrike_ta_index_time_host_resolution_lookup.csv"

DEFAULT_EVENT_ENCODING = "utf-8"

JOURNAL_MAX_TASK_ATTEMPTS = 3
JOURNAL_RESTART_FAILED_TASKS_INTERVAL = 300  # in seconds
JOURNAL_MONITOR_INTERVAL = 30  # in seconds
JOURNAL_HEARTBEAT_INTERVAL = 10  # in seconds
JOURNAL_REG_TTL = (
    3 * JOURNAL_HEARTBEAT_INTERVAL
)  # unassign task from worker if it's inactive longer than TTL
JOURNAL_HISTORY_CLEANUP = (
    60 * 60 * 24 * 30
)  # to remove all jpurnal records older then 30 days
JOURNAL_COLLECTION_NAME = "crowdstrike_fdr_ta_journal"


MAX_MESSAGE_REQUEST_RETRIES = 5
MESSAGE_REQUEST_RETRY_INTERVAL_RANGE = (10, 20)

VISIBILITY_TIMEOUT_EXCESS_ALERT = (
    "ALERT: {}, {} ingested {} seconds after sqs message visibility timeout expiration"
)

KB = 1024
MB = 1024 * KB
MAX_IN_MEM_SIZE = 30 * MB

SOURCETYPE_SENSOR = "crowdstrike:events:sensor"
SOURCETYPE_SENSOR_ITHR = "crowdstrike:events:sensor:ithr"
SOURCETYPE_EXTERNAL = "crowdstrike:events:external"
SOURCETYPE_ZTHA = "crowdstrike:events:ztha"
SOURCETYPE_AIDMASTER = "crowdstrike:inventory:aidmaster"
SOURCETYPE_MANAGEDASSETS = "crowdstrike:inventory:managedassets"
SOURCETYPE_NOTMANAGED = "crowdstrike:inventory:notmanaged"
SOURCETYPE_APPINFO = "crowdstrike:inventory:appinfo"
SOURCETYPE_USERINFO = "crowdstrike:inventory:userinfo"

SOURCETYPE_TO_INDEX_PROP_NAME = {
    SOURCETYPE_SENSOR: "index",
    SOURCETYPE_SENSOR_ITHR: "index",
    SOURCETYPE_EXTERNAL: "index_for_external_events",
    SOURCETYPE_ZTHA: "index_for_ztha_events",
    SOURCETYPE_AIDMASTER: "index_for_aidmaster_events",
    SOURCETYPE_MANAGEDASSETS: "index_for_managedassets_events",
    SOURCETYPE_NOTMANAGED: "index_for_notmanaged_events",
    SOURCETYPE_APPINFO: "index_for_appinfo_events",
    SOURCETYPE_USERINFO: "index_for_userinfo_events",
}
