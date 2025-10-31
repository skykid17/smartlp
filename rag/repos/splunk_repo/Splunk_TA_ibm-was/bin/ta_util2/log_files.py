#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
ta_util = "ta_util"
ta_util_conf = "ta_util_conf"
ta_util_rest = "ta_util_rest"
ta_util_state_store = "ta_util_state_store"


def get_all_logs():
    g = globals()
    return [g[log] for log in g if log.startswith("ta_")]
