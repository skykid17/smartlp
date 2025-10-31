#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import os
import os.path
import sys

try:
    from splunk.clilib.bundle_paths import make_splunkhome_path
except ImportError:
    from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path

import remedy_consts as c
from solnlib import log
from splunk.clilib import cli_common as cli

sys.path.append(make_splunkhome_path(["etc", "apps", c.APP_NAME, "bin"]))
remedy_setting_local = make_splunkhome_path(
    ["etc", "apps", c.APP_NAME, "local", c.REMEDY_CONF + ".conf"]
)


def get_logger(log_name):
    """
    @log_name: which logger
    """
    log_file = "splunk_ta_remedy_" + log_name
    logger = log.Logs().get_logger(log_file)
    logger.setLevel(c.DEFAULT_LOG_LEVEL)
    if os.path.exists(remedy_setting_local):
        remedy_conf = cli.readConfFile(remedy_setting_local)
        if "logging" in remedy_conf and "loglevel" in remedy_conf["logging"]:
            logger.setLevel(remedy_conf["logging"]["loglevel"])

    return logger
