#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

"""
This module validates account being saved by the user
"""

import json
import traceback

import requests

# isort: off
import import_declare_test  # noqa: F401
import splunk.admin as admin  # noqa: F401
from cyberark_epm_utils import (
    get_cyberark_epm_api_version,
    get_proxy_settings,
    get_account_details,
    add_ucc_error_logger,
)
from solnlib import log
from splunktaucclib.rest_handler.error import RestError
from splunktaucclib.rest_handler.endpoint.validator import Validator
from constants import (
    SERVER_ERROR,
    CONNECTION_ERROR,
    AUTHENTICATION_ERROR,
    PERMISSION_ERROR,
    CONFIGURATION_ERROR,
)

_LOGGER = log.Logs().get_logger("splunk_ta_cyberark_epm_account_validation")


class GetSessionKey(admin.MConfigHandler):
    def __init__(self):
        self.session_key = self.getSessionKey()


def account_validation(url, username, password, session_key):
    """
    This method verifies the credentials by making an API call
    """

    _LOGGER.debug("Verifying username and password for the EPM instance {}".format(url))
    if not url or not username or not password:
        raise RestError(
            400, "Provide all necessary arguments : url , username and password."
        )

    if "https://" not in url:
        raise RestError(400, "Provided base URL of Cyberark EPM must start with https.")
    try:
        proxy_settings = get_proxy_settings(_LOGGER, session_key)

        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        body = {"Username": username, "Password": password, "ApplicationID": "Splunk"}
        api_url = url + "/EPM/API/{}/Auth/EPM/Logon".format(
            get_cyberark_epm_api_version()
        )

        resp = requests.post(
            url=api_url,
            proxies=proxy_settings,
            data=json.dumps(body),
            headers=headers,
            timeout=120,
        )

    except Exception as e:
        msg = (
            "Could not connect to {}. Check configuration and network settings".format(
                url
            )
        )
        add_ucc_error_logger(_LOGGER, CONNECTION_ERROR, e, msg_before=msg)

        raise RestError(400, msg)

    if resp.status_code in (200, 201):
        try:
            resp.json()["EPMAuthenticationResult"]
            _LOGGER.info("Account credentials successfully validated.")
            return True
        except Exception as e:
            msg = (
                "Unable to validate the Account credentials, please check the details."
            )
            _LOGGER.error(f"Exception raised: {str(e)}. {msg}")
            raise RestError(resp.status_code, msg)

    if resp.status_code == 400:
        e = Exception(
            "ERROR [{}] - EPM server {} cannot or will not process the request due to Bad Request. {}".format(
                resp.status_code, url, resp.json()
            )
        )
        add_ucc_error_logger(_LOGGER, CONNECTION_ERROR, e)
        raise RestError(
            resp.status_code, "EPM server cannot process the request. Bad Request."
        )
    if resp.status_code == 401:
        e = Exception(
            "ERROR [{}] - The request has not been applied because of Invalid Credentials. {}".format(
                resp.status_code, resp.json()
            )
        )
        add_ucc_error_logger(_LOGGER, AUTHENTICATION_ERROR, e)
        raise RestError(resp.status_code, "Invalid Credentials.")
    if resp.status_code == 403:
        e = Exception(
            "ERROR [{}] - Access to the EPM server {} is forbidden for this user. {}".format(
                resp.status_code, url, resp.json()
            )
        )
        add_ucc_error_logger(_LOGGER, PERMISSION_ERROR, e)
        raise RestError(
            resp.status_code, "Access to the EPM server is forbidden for this user."
        )
    if resp.status_code == 404:
        e = Exception(
            "ERROR [{}] - EPM server {} not found OR Invalid EPM url. {}".format(
                resp.status_code, url, resp.json()
            )
        )
        add_ucc_error_logger(_LOGGER, CONNECTION_ERROR, e)
        raise RestError(resp.status_code, "EPM server not found OR Invalid EPM url.")
    if resp.status_code == 500:
        e = Exception(
            "ERROR [{}] - Internal Server Error. {}".format(
                resp.status_code, resp.json()
            )
        )
        add_ucc_error_logger(_LOGGER, SERVER_ERROR, e)
        raise RestError(resp.status_code, "Internal Server Error.")

    _LOGGER.error("Error [{}]. {}".format(resp.status_code, resp.json()))
    raise RestError(
        resp.status_code,
        "ERROR {}. Could not connect to {}".format(resp.status_code, url),
    )


class AccountNameValidation(Validator):
    """
    Account name validation
    """

    def __init__(self, *args, **kwargs):
        super(AccountNameValidation, self).__init__(*args, **kwargs)

    def validate(self, value, data):
        """
        This function validates the account_name present in the payload when saving an input
        It validates that any account with provided account_name is configured or not.
        """
        try:
            session_key = GetSessionKey().session_key
            account_details = get_account_details(_LOGGER, session_key, value)
            if (
                account_details.get("username")
                and account_details.get("password")
                and account_details.get("epm_url")
            ):
                return True
            errorMsg = "Configurations missing for account with name: {}.".format(value)
            self.put_msg(errorMsg)
            return False
        except Exception:
            errorMsg = "No account found with name: {}.".format(value)
            e = Exception(errorMsg)
            add_ucc_error_logger(_LOGGER, CONFIGURATION_ERROR, e)
            self.put_msg(errorMsg)
            return False
