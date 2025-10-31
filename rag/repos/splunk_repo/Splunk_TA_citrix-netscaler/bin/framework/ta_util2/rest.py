#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import logging
import urllib.parse
from traceback import format_exc
import requests

import ta_util2.log_files as log_files
import ta_util2.utils as utils

_LOGGER = logging.getLogger(log_files.ta_util_rest)


def splunkd_request(
    splunkd_uri, session_key, method="GET", headers=None, data=None, timeout=30, retry=1
):
    """
    @return: repsonse object received by the request.
    """

    headers = headers if headers else {}
    headers["Authorization"] = "Splunk {0}".format(session_key)

    if not (headers.get("Content-Type") or headers.get("content-type")):
        content_type = "application/x-www-form-urlencoded"
        headers["Content-Type"] = content_type

    if data:
        if headers.get("Content-Type") == "application/json":
            data = json.dumps(data)
        else:
            data = urllib.parse.urlencode(data)

    if not headers.get("Content-Type"):
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    msg_temp = "Failed to send rest request=%s, errcode=%s, reason=%s"
    response = None

    for _ in range(retry):
        try:
            response = requests.request(  # nosemgrep: splunk.disabled-cert-validation
                url=splunkd_uri,
                method=method,
                headers=headers,
                data=data,
                verify=False,
                timeout=timeout,
            )
        except Exception:
            _LOGGER.error(msg_temp, splunkd_uri, "unknown", format_exc())
        else:
            if response and response.status_code not in (200, 201):
                _LOGGER.debug(
                    msg_temp,
                    splunkd_uri,
                    response.status_code,
                    code_to_msg(response.status_code, response.content),
                )
    return response


def code_to_msg(status_code, content):
    code_msg_tbl = {
        400: "Request error. reason={}".format(content),
        401: "Authentication failure, invalid access credentials.",
        402: "In-use license disables this feature.",
        403: "Insufficient permission.",
        404: "Requested endpoint does not exist.",
        409: "Invalid operation for this endpoint. reason={}".format(content),
        500: "Unspecified internal server error. reason={}".format(content),
        503: (
            "Feature is disabled in the configuration file. "
            "reason={}".format(content)
        ),
    }

    return code_msg_tbl.get(status_code, content)
