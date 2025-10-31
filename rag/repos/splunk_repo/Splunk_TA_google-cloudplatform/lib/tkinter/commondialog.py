#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

from future.utils import PY3

if PY3:
    from tkinter.commondialog import *  # noqa
else:
    try:
        from tkCommonDialog import *  # noqa
    except ImportError:
        raise ImportError(
            "The tkCommonDialog module is missing. Does your Py2 "
            "installation include tkinter?"
        )
