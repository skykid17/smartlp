#!/usr/bin/python
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#


import time
from builtins import str

import httplib2shim
import splunk_ta_gcp.legacy.common as tacommon
import splunk_ta_gcp.legacy.resource_consts as grc
import splunktalib.common.pattern as gcp
import splunktalib.data_loader_mgr as dlm
from splunksdc import log as logging

from . import config as mconf
from . import data_loader as grdl

logger = logging.get_module_logger()
tacommon.set_local_time_for_logger()


def print_scheme():
    title = "Splunk Add-on for Google Cloud Platform"
    description = "Collect and index Google Cloud Resource Metadata data for vpc access"
    tacommon.print_scheme(title, description)


@gcp.catch_all(logger)
def run():
    """
    Main loop. Run this TA forever
    """
    logger.info("Start google_resource_metadata_vpc_access")
    metas, tasks = tacommon.get_configs(
        mconf.GoogleResourceMetadataVpcAccessConfig,
        "google_resource_metadata_vpc_access",
        logger,
    )

    if not tasks:
        logger.info("No Tasks to process for resource metadata vpc access input")
        return

    logger.debug("Received {} Tasks".format(str(len(tasks))))

    metas[grc.log_file] = grc.description_log
    loader_mgr = dlm.create_data_loader_mgr(metas)
    tacommon.setup_signal_handler(loader_mgr, logger)
    conf_change_handler = tacommon.get_file_change_handler(loader_mgr, logger)
    conf_monitor = tacommon.create_conf_monitor(
        conf_change_handler, [grc.vpcaccess_data_collection_conf]
    )
    loader_mgr.add_timer(conf_monitor, time.time(), interval=10)
    jobs = [grdl.VpcAccessResourceDataLoader(task) for task in tasks]
    loader_mgr.start(jobs)

    logger.info("End google_resource_metadata_vpc_access")


def main():
    """
    Main entry point
    """
    httplib2shim.patch()
    logging.setup_root_logger(
        "splunk_ta_google-cloudplatform", "google_cloud_resource_metadata_vpc_access"
    )
    tacommon.main(print_scheme, run)
