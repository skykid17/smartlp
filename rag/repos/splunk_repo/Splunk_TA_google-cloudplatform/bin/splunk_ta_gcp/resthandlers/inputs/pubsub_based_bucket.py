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
    DataInputModel,
    RestModel,
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
        "google_subscriptions",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "index",
        required=True,
        encrypted=False,
        default="default",
        validator=validator.AllOf(
            validator.String(
                max_len=1023,
                min_len=1,
            ),
            validator.Pattern(
                regex=r"""^[a-zA-Z0-9][a-zA-Z0-9\_\-]*$""",
            ),
        ),
    ),
    field.RestField(
        "sourcetype",
        required=True,
        encrypted=False,
        default="google:gcp:buckets:data",
        validator=validator.AllOf(
            validator.String(
                max_len=8192,
                min_len=1,
            ),
            validator.Pattern(
                regex=r"""^[^<>?#&]*$""",
            ),
        ),
    ),
    field.RestField(
        "message_batch_size",
        required=True,
        encrypted=False,
        default="10",
        validator=custom_validator.NumberValidator(min_len=1, max_len=1000),
    ),
    field.RestField(
        "number_of_threads",
        required=True,
        encrypted=False,
        default="10",
        validator=custom_validator.NumberValidator(min_len=1, max_len=10),
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)

endpoint = DataInputModel("google_cloud_pubsub_based_bucket", model)


def main():
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
