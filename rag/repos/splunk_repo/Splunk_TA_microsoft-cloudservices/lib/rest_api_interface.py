#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from typing import List, Dict
import json

from splunk import rest
from solnlib.splunkenv import get_splunkd_uri
from solnlib import (  # isort: skip # pylint: disable=import-error
    conf_manager,
)

from splunk_ta_mscs.models import ProxyConfig

BASE_ENDPOINT = (
    f"{get_splunkd_uri()}/servicesNS/nobody/Splunk_TA_microsoft-cloudservices"
)


def flatten_query_params(params):
    """
    Query parameters are provided as a list of pairs and can be repeated, e.g.:
    "query": [ ["arg1","val1"], ["arg2", "val2"], ["arg1", val2"] ]
    This function simply accepts only the first parameter and discards duplicates
    """
    flattened = {}
    for i, j in params:
        flattened[i] = flattened.get(i) or j
    return flattened


def _make_request(session_key, module, params: Dict[str, str], method="GET"):
    response, content = rest.simpleRequest(
        f"{BASE_ENDPOINT}/{module}?{'&'.join(f'{k}={v}' for k, v in params.items())}",
        sessionKey=session_key,
        method=method,
        raiseAllErrors=True,
    )
    return json.loads(content)


def get_checkpoints(session_key, modinput_name):
    params = {
        "modinput_type": "mscs_azure_event_hub",
        "modinput_name": modinput_name,
    }
    return _make_request(session_key, "checkpoints", params)


def _get_accounts(session_key, conf_file_name):
    try:
        cfm = conf_manager.ConfManager(
            session_key,
            "Splunk_TA_microsoft-cloudservices",
            realm="__REST_CREDENTIAL__#Splunk_TA_microsoft-cloudservices#configs/conf-{}".format(
                conf_file_name
            ),
        )
        # Get Conf object of account settings
        conf = cfm.get_conf(conf_file_name)
        # Get account stanza from the settings
        account_configs = conf.get_all()

        return account_configs
    except conf_manager.ConfManagerException:
        # For fresh addon account conf file will not exist so handling that exception
        return {}


def get_azure_accounts(session_key):
    return _get_accounts(session_key, "mscs_azure_accounts")


def get_storage_accounts(session_key):
    return _get_accounts(session_key, "mscs_storage_accounts")


def get_modinputs(session_key, modinput_type: str, modinput_name: str = ""):
    params = {"output_mode": "json", "count": "-1"}

    if modinput_name:
        module = f"splunk_ta_mscs_{modinput_type}/{modinput_name}"
    else:
        module = f"splunk_ta_mscs_{modinput_type}"

    return _make_request(session_key, module, params)


def get_proxy_info_from_endpoint(session_key) -> ProxyConfig:
    splunkd_uri = get_splunkd_uri()
    rest_endpoint = (
        splunkd_uri
        + "/servicesNS/nobody/Splunk_TA_microsoft-cloudservices/splunk_ta_mscs_settings/proxy?--cred--=1&"
        "output_mode=json"
    )

    response, content = rest.simpleRequest(
        rest_endpoint, sessionKey=session_key, method="GET", raiseAllErrors=True
    )
    proxy_settings = json.loads(content)["entry"][0]["content"]

    return ProxyConfig.from_dict(proxy_settings)
