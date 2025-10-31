#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

from future.utils import PY3

if PY3:
    from tkinter.filedialog import *  # noqa
else:
    try:
        from FileDialog import *  # noqa
    except ImportError:
        raise ImportError(
            "The FileDialog module is missing. Does your Py2 "
            "installation include tkinter?"
        )
    try:
        from tkFileDialog import *  # noqa
    except ImportError:
        raise ImportError(
            "The tkFileDialog module is missing. Does your Py2 "
            "installation include tkinter?"
        )
