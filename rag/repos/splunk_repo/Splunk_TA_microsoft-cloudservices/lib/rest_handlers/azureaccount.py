#!/usr/bin/python
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import traceback
from solnlib import log
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from cattrs import ClassValidationError, transform_error

from splunk_ta_mscs.models import AzureAccountConfig, format_validation_exception
from mscs_util import (
    get_proxy_info_from_endpoint,
)
from splunk_ta_mscs.mscs_credential_provider import validate_credential


class AzureAccountValidation(validator.Validator):
    def __init__(self):

        super(AzureAccountValidation, self).__init__()
        self.put_msg(
            "Account authentication failed. Please check your credentials and try again"
        )
        self.proxy_config = None

    def validate(self, value, data):
        """Validate the given values.

        :param value: Value of particular parameter
        :param data: Whole payload
        :return: True if validation pass, False otherwise.
        """

        logger = log.Logs().get_logger(
            "splunk_ta_microsoft-cloudservices_azure_account_validation"
        )
        logger.info("Verifying credentials for MSCS Azure account")
        try:
            account = AzureAccountConfig.from_dict(data)
        except ClassValidationError as e:
            logger.error(
                f"Failed to validate Azure Account model. Error details: {transform_error(e, format_exception=format_validation_exception)}",
                exc_info=e,
            )
            return False

        logger.info("Getting proxy details")
        try:
            self.proxy_config = get_proxy_info_from_endpoint()

        except Exception as e:
            logger.error(
                "Error {} while getting proxy details: {}".format(
                    e, traceback.format_exc()
                )
            )
            return False

        try:
            validate_credential(account, self.proxy_config.proxy_dict, logger)
        except Exception as e:
            logger.error(
                "Error {} while verifying the credentials: {}".format(
                    e, traceback.format_exc()
                )
            )
            return False

        logger.info("Credentials validated successfully")
        return True


class AzureAccountHandler(AdminExternalHandler):
    """
    This handler is to check if the account configurations are valid or not
    """

    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)

    def handleEdit(self, confInfo):
        AdminExternalHandler.handleEdit(self, confInfo)
        edited_account = next(iter(confInfo))

    def handleCreate(self, confInfo):
        AdminExternalHandler.handleCreate(self, confInfo)
        edited_account = next(iter(confInfo))


fields = [
    field.RestField(
        "client_id", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "client_secret", required=True, encrypted=True, default=None, validator=None
    ),
    field.RestField(
        "tenant_id",
        required=True,
        encrypted=False,
        default=None,
        validator=AzureAccountValidation(),
    ),
    field.RestField(
        "account_class_type",
        required=True,
        encrypted=False,
        default="1",
        validator=None,
    ),
    field.RestField(
        "app_account_help_link",
        required=False,
        encrypted=False,
        default=None,
        validator=None,
    ),
    field.RestField("disabled", required=False, validator=None),
]

model = RestModel(fields, name=None)

endpoint = SingleModel("mscs_azure_accounts", model, config_name="azureaccount")
