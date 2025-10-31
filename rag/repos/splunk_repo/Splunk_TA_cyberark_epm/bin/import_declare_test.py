#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import os
import sys

COLLECTION_VALUE_FROM_ENDPOINT = {
    "inbox_events": "Splunk_TA_cyberark_epm_inbox_events_checkpointer",
    "policy_audit_events": "Splunk_TA_cyberark_epm_policy_audit_events_checkpointer",
    "admin_audit_logs": "Splunk_TA_cyberark_epm_admin_audit_logs_checkpointer",
    "account_admin_audit_logs": "Splunk_TA_cyberark_epm_account_admin_audit_logs_checkpointer",
}
sys.path.insert(
    0,
    os.path.sep.join(
        [os.path.dirname(os.path.realpath(os.path.dirname(__file__))), "lib"]
    ),
)
sys.path.insert(
    1, os.path.sep.join([os.path.dirname(os.path.realpath(os.path.dirname(__file__)))])
)
