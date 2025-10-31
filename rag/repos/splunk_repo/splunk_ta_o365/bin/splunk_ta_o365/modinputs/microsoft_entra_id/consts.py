#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
VALID_ENTRA_ID_TYPES = ["users", "groups", "applications", "devices"]
# Reference regarding 5xx series codes https://developer.mozilla.org/en-US/docs/Web/HTTP/Status#server_error_responses
DEFAULT_RETRY_LIST = [500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511]
NUMBER_OF_THREADS = 4  # Currently, there are only four types of Microsoft Entra ID, so the number of threads is set to four. If there are more new Entra ID types in the future, we can increase the number of threads accordingly.
METADATA_ENDPOINTS = {
    "users": "/v1.0/users",
    "groups": "/v1.0/groups",
    "applications": "/v1.0/applications",
    "devices": "/v1.0/devices",
}
DEFAULT_SOURCETYPE = "o365:metadata"
TOKEN_REFRESH_WINDOW = 600
