#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import
import aws_bootstrap_env  # noqa: F401 # pylint: disable=unused-import
import splunk.admin as admin

from splunktalib.rest_manager import multimodel

# from splunktalib.rest_manager import base

import aws_settings_base_rh


class InspectorLogging(aws_settings_base_rh.AWSLogging):
    keyMap = {"level": "log_level"}


# class InspectorGlobalSettings(base.BaseModel):
#    optionalArgs = {'use_hec'}


class InspectorSettings(multimodel.MultiModel):
    endpoint = "configs/conf-aws_inspector"
    modelMap = {
        "logging": InspectorLogging,
    }


if __name__ == "__main__":
    admin.init(
        multimodel.ResourceHandler(InspectorSettings), admin.CONTEXT_APP_AND_USER
    )
