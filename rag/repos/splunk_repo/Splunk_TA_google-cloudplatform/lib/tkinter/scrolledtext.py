#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

from future.utils import PY3

if PY3:
    from tkinter.scrolledtext import *  # noqa
else:
    try:
        from ScrolledText import *  # noqa
    except ImportError:
        raise ImportError(
            "The ScrolledText module is missing. Does your Py2 "
            "installation include tkinter?"
        )
