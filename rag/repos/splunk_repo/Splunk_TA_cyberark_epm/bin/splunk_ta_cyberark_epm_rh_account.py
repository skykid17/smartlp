#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

# isort: off
import import_declare_test  # noqa: F401
import logging
import json

import splunk.rest as rest
from solnlib import conf_manager, log
from cyberark_epm_utils import set_logger
from splunk_ta_cyberark_epm_account_validation import account_validation
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.endpoint import (
    RestModel,
    SingleModel,
    field,
    validator,
)
from splunktaucclib.rest_handler.error import RestError
from cyberark_epm_utils import add_ucc_error_logger
from constants import (
    SERVER_ERROR,
    GENERAL_EXCEPTION,
    UCC_EXECPTION_EXE_LABEL,
)

util.remove_http_proxy_env_vars()
APP_NAME = "Splunk_TA_cyberark_epm"

fields = [
    field.RestField(
        "url",
        required=True,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""https://\S*""",
        ),
    ),
    field.RestField(
        "username",
        required=True,
        encrypted=False,
        default=None,
        validator=validator.String(
            max_len=200,
            min_len=1,
        ),
    ),
    field.RestField(
        "password", required=True, encrypted=True, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel("splunk_ta_cyberark_epm_account", model, config_name="account")


class CyberarkEpmAccountExternalHandler(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)

    def handleEdit(self, confInfo):
        account_validation(
            self.payload.get("url"),
            self.payload.get("username"),
            self.payload.get("password"),
            self.getSessionKey(),
        )
        AdminExternalHandler.handleEdit(self, confInfo)

    def handleCreate(self, confInfo):
        account_validation(
            self.payload.get("url"),
            self.payload.get("username"),
            self.payload.get("password"),
            self.getSessionKey(),
        )
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleRemove(self, confInfo):
        session_key = self.getSessionKey()
        server_name = self.callerArgs.id
        logger = set_logger(session_key, "splunk_ta_cyberark_epm_account_validation")
        try:
            response_status, response_content = rest.simpleRequest(
                "/servicesNS/nobody/" + str(APP_NAME) + "/configs/conf-inputs/",
                sessionKey=session_key,
                getargs={"output_mode": "json"},
                raiseAllErrors=True,
            )
            res = json.loads(response_content)
            if "entry" in res:
                for inputs in res["entry"]:
                    if "name" in inputs:
                        input_name = inputs["name"]
                        if (
                            "app" in inputs.get("acl", "")
                            and inputs["acl"].get("app", "") == APP_NAME
                        ):
                            if (
                                "content" in inputs
                                and "account_name" in inputs["content"]
                            ):
                                account_name = inputs["content"]["account_name"]
                                if account_name == server_name:
                                    raise RestError(
                                        409,
                                        "Cannot delete the account as it is already been used in {}.".format(
                                            input_name.split("//")[1]
                                        ),
                                    )
        except Exception as e:
            add_ucc_error_logger(logger, SERVER_ERROR, e)
            raise RestError(
                409,
                "Cannot delete the account as it is already been used in {}.".format(
                    input_name.split("//")[1]
                ),
            )
        AdminExternalHandler.handleRemove(self, confInfo)


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=CyberarkEpmAccountExternalHandler,
    )
