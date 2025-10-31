#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#

import import_declare_test  # isort: skip # noqa: F401
import json
import urllib.error
import urllib.parse
import urllib.request
from traceback import format_exc

import httplib2


def splunkd_request(
    splunkd_uri,
    session_key,
    _LOGGER,
    method="GET",
    headers=None,
    data=None,
    timeout=30,
    retry=1,
):
    """
    @return: httplib2.Response and content
    """

    headers = headers if headers is not None else {}
    headers["Authorization"] = "Splunk {}".format(session_key)
    content_type = headers.get("Content-Type")
    if not content_type:
        content_type = headers.get("content-type")

    if not content_type:
        content_type = "application/x-www-form-urlencoded"
        headers["Content-Type"] = content_type

    if data is not None:
        if content_type == "application/json":
            data = json.dumps(data)
        else:
            data = urllib.parse.urlencode(data)

    http = httplib2.Http(timeout=timeout, disable_ssl_certificate_validation=True)
    msg_temp = "Failed to send rest request=%s, errcode=%s, reason=%s"
    resp, content = None, None
    _LOGGER.debug("Making a request to %s with [%s] method", splunkd_uri, method)
    for _ in range(retry):
        try:
            resp, content = http.request(
                splunkd_uri, method=method, headers=headers, body=data
            )
        except Exception:
            _LOGGER.error(msg_temp, splunkd_uri, "unknown", format_exc())
        else:
            if resp.status not in (200, 201):
                _LOGGER.debug(
                    msg_temp, splunkd_uri, resp.status, code_to_msg(resp, content)
                )
            else:
                return resp, content
    return resp, content


def code_to_msg(resp, content):
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

    return code_msg_tbl.get(resp.status, content)
