#!/usr/bin/python

"""
This is the main entry point for AWS Inspector v2 Modinput
"""

#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

import time

import splunk_ta_aws.common.ta_aws_common as tacommon
import splunk_ta_aws.common.ta_aws_consts as tac
import splunktalib.common.util as scutil
import splunktalib.data_loader_mgr as dlm
from splunksdc import log as logging

from . import aws_inspector_v2_conf as aiconf
from . import aws_inspector_v2_consts as aiconst
from . import aws_inspector_v2_data_loader as aidl

logger = logging.get_module_logger()


def print_scheme():
    """Prints scheme for aws inspector v2 input."""
    title = "AWS Inspector_v2"
    description = "Collect and index AWS Inspector v2 findings"
    tacommon.print_scheme(title, description)


def _do_run():
    meta_configs, _, tasks = tacommon.get_configs(
        aiconf.AWSInspectorV2Conf, "aws_inspector_v2", logger
    )

    if not tasks:
        return

    meta_configs[tac.log_file] = aiconst.inspector_v2_log
    loader_mgr = dlm.create_data_loader_mgr(meta_configs)
    tacommon.setup_signal_handler(loader_mgr, logger)
    conf_change_handler = tacommon.get_file_change_handler(loader_mgr, logger)
    conf_monitor = aiconf.create_conf_monitor(conf_change_handler)
    loader_mgr.add_timer(conf_monitor, time.time(), 10)

    jobs = [aidl.AWSInspectorV2DataLoader(task) for task in tasks]
    loader_mgr.run(jobs)


@scutil.catch_all(logger, False)
def run():
    """
    Main loop. Run this TA forever
    """

    logger.info("Start aws_inspector_v2")
    _do_run()
    logger.info("End aws_inspector_v2")


def main():
    """
    Main entry point
    """
    logging.setup_root_logger(app_name="splunk_ta_aws", modular_name="inspector_v2")
    tacommon.main(print_scheme, run)


if __name__ == "__main__":
    main()
