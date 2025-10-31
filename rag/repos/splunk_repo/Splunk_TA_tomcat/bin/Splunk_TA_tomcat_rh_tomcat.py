#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import logging

import import_declare_test
from Splunk_TA_tomcat_validations import SignatureParamsValidator
from splunktaucclib.rest_handler import admin_external
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.endpoint import (
    DataInputModel,
    RestModel,
    field,
    validator,
)

assert import_declare_test, "Module is used to filter the sys.path"

fields = [
    field.RestField(
        "duration",
        required=True,
        encrypted=False,
        default=120,
        validator=validator.Number(max_val=31536000, min_val=1, is_int=True),
    ),
    field.RestField(
        "account", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "object_name",
        required=False,
        encrypted=False,
        default="java.lang:type=Threading",
        validator=validator.String(
            max_len=80,
            min_len=1,
        ),
    ),
    field.RestField(
        "operation_name",
        required=False,
        encrypted=False,
        default="dumpAllThreads",
        validator=validator.String(
            max_len=80,
            min_len=1,
        ),
    ),
    field.RestField(
        "signature",
        required=False,
        encrypted=False,
        default="boolean, boolean",
        validator=SignatureParamsValidator(),
    ),
    field.RestField(
        "params",
        required=False,
        encrypted=False,
        default="true, true",
        validator=None,
    ),
    field.RestField(
        "split_array",
        required=False,
        encrypted=False,
        default="true",
        validator=None,
    ),
    field.RestField("disabled", required=False, validator=None),
    field.RestField(
        "index",
        required=True,
        encrypted=False,
        default="default",
        validator=validator.String(
            min_len=1,
            max_len=80,
        ),
    ),
]
model = RestModel(fields, name=None)


endpoint = DataInputModel(
    "tomcat",
    model,
)


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
