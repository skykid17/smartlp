##
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
##
##

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_FALLBACK_DATE = "1970-01-01T00:00:00.000Z"
QUERY_WINDOW_SIZE = 3600
MAX_USER_LIMIT = "200"
MAX_APP_LIMIT = "200"
MAX_GROUP_LIMIT = "10000"
ACCOUNT_CONFIG_FILE = "splunk_ta_okta_identity_cloud_account"
SETTINGS_CONFIG_FILE = "splunk_ta_okta_identity_cloud_settings"
MODULAR_INPUT_NAME = "okta_identity_cloud://{}"
REQTIMEOUT = float(90)
