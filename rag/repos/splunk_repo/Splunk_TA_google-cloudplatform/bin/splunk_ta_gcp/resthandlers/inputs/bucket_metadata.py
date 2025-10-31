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
    DataInputModel,
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
        "bucket_name",
        required=True,
        encrypted=False,
        default=None,
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "conf_version",
        required=False,
        encrypted=False,
        default=None,
        validator=None,
    ),
    field.RestField(
        "interval",
        required=True,
        encrypted=False,
        default=3600,
        validator=custom_validator.NumberValidator(min_len=1, max_len=31536000),
    ),
    field.RestField(
        "number_of_threads",
        required=True,
        encrypted=False,
        default="1",
        validator=custom_validator.NumberValidator(min_len=1, max_len=256),
    ),
    field.RestField(
        "index",
        required=True,
        encrypted=False,
        default="default",
        validator=custom_validator.StringValidator(min_len=1, max_len=4096),
    ),
    field.RestField(
        "sourcetype",
        required=True,
        encrypted=False,
        default="google:gcp:buckets:data",
        validator=custom_validator.StringValidator(max_len=8192, min_len=1),
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)


endpoint = DataInputModel("google_cloud_bucket_metadata", model)


class BucketMetadataHandler(AdminExternalHandler):
    def handleCreate(self, confInfo):
        self.payload["conf_version"] = "v1"
        AdminExternalHandler.handleCreate(self, confInfo)


def main():
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=BucketMetadataHandler,
    )
