#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import absolute_import

import logging

from splunk_ta_gcp.resthandlers.inputs import custom_validator
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.endpoint import (
    RestModel,
    SingleModel,
    field,
    validator,
)

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "google_credentials_name",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "google_project",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "google_monitored_projects",
        required=True,
        encrypted=False,
        default="All",
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "google_metrics",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.MetricValidator(),
    ),
    field.RestField(
        "polling_interval",
        required=True,
        encrypted=False,
        default=300,
        validator=custom_validator.NumberValidator(min_len=1, max_len=31536000),
    ),
    field.RestField(
        "oldest",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.DateValidator("%Y-%m-%dT%H:%M:%S"),
    ),
    field.RestField(
        "index",
        required=True,
        encrypted=False,
        default="default",
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "google_cloud_monitor_inputs", model, config_name="inputs_monitoring"
)


def main():
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
