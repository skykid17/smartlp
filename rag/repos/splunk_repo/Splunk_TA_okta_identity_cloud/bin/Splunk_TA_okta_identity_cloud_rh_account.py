#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import import_declare_test  # noqa # isort: skip
import json
import logging

import splunk.rest as rest
from solnlib import conf_manager, log
from Splunk_TA_okta_identity_cloud_account_validation import AccountValidation
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.endpoint import (
    RestModel,
    SingleModel,
    field,
    validator,
)
from splunktaucclib.rest_handler.error import RestError

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "domain",
        required=False,
        encrypted=False,
        default=None,
        validator=validator.String(
            max_len=1024,
            min_len=8,
        ),
    ),
    field.RestField(
        "password",
        required=False,
        encrypted=True,
        default=None,
        validator=AccountValidation(),
    ),
    field.RestField(
        "client_id", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "client_secret", required=False, encrypted=True, default=None, validator=None
    ),
    field.RestField(
        "redirect_url", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "endpoint", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "access_token", required=False, encrypted=True, default=None, validator=None
    ),
    field.RestField(
        "refresh_token", required=False, encrypted=True, default=None, validator=None
    ),
    field.RestField(
        "instance_url", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "scope", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "auth_type", required=True, encrypted=False, default="basic", validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "splunk_ta_okta_identity_cloud_account", model, config_name="account"
)
APP_NAME = import_declare_test.ta_name


class OktaAccountExternalHandler(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleRemove(self, confInfo):
        session_key = self.getSessionKey()
        server_name = self.callerArgs.id
        logger = log.Logs().get_logger(
            "splunk_ta_okta_identity_cloud_account_validation"
        )
        log_level = conf_manager.get_log_level(
            logger=logger,
            session_key=session_key,
            app_name=APP_NAME,
            conf_name="splunk_ta_okta_identity_cloud_settings",
        )
        logger.setLevel(log_level)
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
                                and "global_account" in inputs["content"]
                            ):
                                account_name = inputs["content"]["global_account"]
                                if account_name == server_name:
                                    raise RestError(
                                        409,
                                        "Cannot delete the account as it is already been used in {}.".format(
                                            input_name.split("//")[1]
                                        ),
                                    )
        except Exception:
            logger.error(
                "Cannot delete the account as it is already been used in {}.".format(
                    input_name.split("//")[1]
                )
            )
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
        handler=OktaAccountExternalHandler,
    )
