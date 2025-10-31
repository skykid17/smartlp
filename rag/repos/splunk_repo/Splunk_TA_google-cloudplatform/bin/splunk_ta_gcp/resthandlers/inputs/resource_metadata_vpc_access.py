#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunk_ta_gcp.resthandlers.inputs import custom_validator
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
import logging

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
        "location_name",
        required=False,
        encrypted=False,
        default=None,
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "google_apis",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.APIValidator(),
    ),
    field.RestField(
        "index",
        required=True,
        encrypted=False,
        default="default",
        validator=None,
    ),
    field.RestField(
        "sourcetype",
        required=True,
        encrypted=False,
        default="google:gcp:resource:metadata",
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "google_cloud_resource_metadata_inputs_vpc_access",
    model,
    config_name="inputs_resource_metadata_vpc_access",
)


def main():
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
