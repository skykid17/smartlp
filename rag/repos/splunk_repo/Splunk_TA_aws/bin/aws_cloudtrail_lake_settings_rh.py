#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import
import aws_bootstrap_env  # noqa: F401 # pylint: disable=unused-import

import splunk.admin as admin

from splunktalib.rest_manager import multimodel

import aws_settings_base_rh


class CloudTrailLakeLogging(aws_settings_base_rh.AWSLogging):
    keyMap = {"level": "log_level"}


class CloudTrailLakeSettings(multimodel.MultiModel):
    endpoint = "configs/conf-aws_cloudtrail_lake"
    modelMap = {
        "logging": CloudTrailLakeLogging,
    }


if __name__ == "__main__":
    admin.init(
        multimodel.ResourceHandler(CloudTrailLakeSettings), admin.CONTEXT_APP_AND_USER
    )
