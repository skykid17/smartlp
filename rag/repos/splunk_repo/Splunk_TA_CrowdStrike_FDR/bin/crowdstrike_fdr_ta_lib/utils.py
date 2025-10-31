#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import copy
from typing import Dict, Any


def saxescape(data: str, entities: Dict[str, str] = {}) -> str:
    """Escape &, <, and > in a string of data.

    You can escape other strings of data by passing a dictionary as
    the optional entities parameter. The keys and values must all be
    strings; each key will be replaced with its corresponding value.
    """

    # must do ampersand first
    data = data.replace("&", "&amp;")
    data = data.replace(">", "&gt;")
    data = data.replace("<", "&lt;")

    for key, value in entities.items():
        data = data.replace(key, value)

    return data


def sanitize(src: Dict[str, Any]) -> Dict[str, Any]:
    res = {}
    keywords = ["secret", "password", "pwd", "token"]
    for key, value in src.items():
        if [kw in key for kw in keywords if kw in key]:
            res[key] = "*****"
        else:
            res[key] = value
    return res


def sanitized_copy(src: Dict[str, Any]) -> Dict[str, Any]:
    return sanitize(copy.deepcopy(src))
