#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

from future.utils import PY3

if PY3:
    from tkinter.colorchooser import *  # noqa
else:
    try:
        from tkColorChooser import *  # noqa
    except ImportError:
        raise ImportError(
            "The tkColorChooser module is missing. Does your Py2 "
            "installation include tkinter?"
        )
