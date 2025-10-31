#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import import_declare_test  # isort: skip # noqa F401

"""
This module will be used to get oauth token from auth code
"""

import json
import logging
import urllib.parse as urllib
import okta_utils as utils
import sys

import requests
import splunk.admin as admin

from solnlib import conf_manager, log
from solnlib.utils import is_true

logger = log.Logs().get_logger("splunk_ta_okta_identity_cloud_oauth")


class splunk_ta_okta_identity_cloud_rh_oauth2_token(admin.MConfigHandler):
    """
    REST Endpoint of getting token by OAuth2 in Splunk Add-on UI Framework.
    """

    def setup(self):
        """
        This method checks which action is getting called and what parameters are required for the request.
        """
        if self.requestedAction == admin.ACTION_EDIT:
            # Add required args in supported args
            for arg in (
                "url",
                "method",
                "grant_type",
                "code",
                "client_id",
                "client_secret",
                "redirect_uri",
                "scope",
            ):
                self.supportedArgs.addReqArg(arg)
        return

    def handleEdit(self, confInfo):
        """
        This handler is to get access token from the auth code received
        It takes 'url', 'method', 'grant_type', 'code', 'client_id', 'client_secret', 'redirect_uri', 'scope' as caller args and
        Returns the confInfo dict object in response.
        """
        try:
            logger.info("In OAuth rest handler to get access token")
            # Get args parameters from the request
            url = self.callerArgs.data["url"][0]
            logger.info(f"OAuth url : {url}")
            proxy_info = utils.get_proxy_settings(self.getSessionKey(), logger)
            method = self.callerArgs.data["method"][0]
            # Create payload from the arguments received
            payload = {
                "grant_type": self.callerArgs.data["grant_type"][0],
                "code": self.callerArgs.data["code"][0],
                "client_id": self.callerArgs.data["client_id"][0],
                "client_secret": self.callerArgs.data["client_secret"][0],
                "redirect_uri": self.callerArgs.data["redirect_uri"][0],
                "scope": self.callerArgs.data["scope"][0],
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }
            # Send http request to get the access_token
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=urllib.urlencode(payload),
                proxies=proxy_info,
                timeout=90,
            )
            content = json.loads(resp.content)
            # Check for any errors in response. If no error then add the content values in confInfo
            if resp.status_code == 200:
                scope_granted = content["scope"]
                # Checking if there are no scopes assigned to the Okta Web App
                # If the condition is true, the error message willbe displayed in the UI
                # and process will be exited
                if scope_granted == "offline_access":
                    error_message = "No scopes are granted to the Okta Web App. Please provide appropriate scopes to the Okta Web App"
                    logger.error(error_message)
                    confInfo["token"]["error"] = error_message
                    return None
                for key, val in content.items():
                    confInfo["token"][key] = val
            else:
                # Else add the error message in the confinfo to display in the UI
                confInfo["token"]["error"] = content["errorSummary"]
            logger.info(
                f"Exiting OAuth rest handler after getting access token with response : {resp.status_code}"
            )
        except Exception as exc:
            logger.error("Error occurred while getting access token using auth code")
            raise exc


if __name__ == "__main__":
    admin.init(
        splunk_ta_okta_identity_cloud_rh_oauth2_token, admin.CONTEXT_APP_AND_USER
    )
