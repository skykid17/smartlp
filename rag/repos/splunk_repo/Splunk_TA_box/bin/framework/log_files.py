#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
ta_box = "ta_box"
ta_frmk = "ta_frmk"
ta_frmk_conf = "ta_frmk_conf"
ta_frmk_rest = "ta_frmk_rest"
ta_frmk_state_store = "ta_frmk_state_store"
ta_box_data_input_ckpt = "ta_box_data_input_checkpoint"
ta_box_live_monitoring_input_ckpt = "ta_box_live_monitoring_input_checkpoint"
ta_box_rh_oauth = "splunk_ta_box_rh_oauth2_token"


def get_all_logs():
    g = globals()
    # semgrep ignore reason: the variable log can have the pre-defined values and not user interferable
    return [
        g[  # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
            log
        ]
        for log in g
        if log.startswith("ta_")
    ]
