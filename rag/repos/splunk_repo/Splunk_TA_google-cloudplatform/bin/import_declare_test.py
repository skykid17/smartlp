#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import os
import sys

path_to_lib = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"
)
sys.path.insert(0, path_to_lib)
path_to_splunktalib = os.path.join(path_to_lib, "splunktalib_helper")
sys.path.insert(0, path_to_splunktalib)


path_to_tp_root = os.path.join(path_to_lib, "3rdparty")
if sys.platform.startswith("win32"):
    platform_dir = "windows_x86_64"
elif sys.platform.startswith("darwin"):
    platform_dir = "darwin_x86_64"
else:
    platform_dir = "linux_x86_64"

path_to_tp = os.path.join(
    path_to_tp_root,
    platform_dir,
    f"python{sys.version_info.major}{sys.version_info.minor}",
)
sys.path.insert(0, path_to_tp)
