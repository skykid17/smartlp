#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

from crowdstrike_ta_bitmask_lookup import bitmask_lookup

lookup_table = {
    1: "SHOW_IN_UI",
    2: "INVASIVE_BLOCK",
    4: "REPORT_ONLY",
    8: "MTP_PTP_RULE",
}

bitmask_lookup(lookup_table)
