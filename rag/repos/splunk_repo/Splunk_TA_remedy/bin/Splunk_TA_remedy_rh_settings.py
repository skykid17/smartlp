#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

"""

* isort ignores:
- isort: skip = Should not be sorted.
* flake8 ignores:
- noqa: F401 -> Def = module imported but unused
    Reason for ignoring = This is necessary as it contains adding a path to sys.path
"""

import splunk_ta_remedy_declare  # isort: skip # noqa: F401

import logging
import ipaddress

from splunk_ta_remedy_soap_account_validation import SoapAccountValidation
from solnlib import log
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler

from splunktaucclib.rest_handler.endpoint import (  # isort: skip
    MultipleModel,
    RestModel,
    field,
    validator,
)


util.remove_http_proxy_env_vars()

fields_additional_parameters = [
    field.RestField(
        "server_url",
        required=True,
        encrypted=False,
        default="",
        validator=validator.AllOf(
            validator.String(
                max_len=8192,
                min_len=0,
            ),
            validator.Pattern(
                regex=r"""^((?!://).)*$""",
            ),
        ),
    ),
    field.RestField(
        "server_name",
        required=True,
        encrypted=False,
        default="",
        validator=validator.String(
            max_len=8192,
            min_len=0,
        ),
    ),
    field.RestField(
        "user",
        required=True,
        encrypted=False,
        default="",
        validator=SoapAccountValidation(),
    ),
    field.RestField(
        "password",
        required=False,
        encrypted=True,
        default="",
        validator=validator.String(
            max_len=8192,
            min_len=0,
        ),
    ),
]
model_additional_parameters = RestModel(
    fields_additional_parameters, name="additional_parameters"
)

fields_proxy = [
    field.RestField(
        "proxy_enabled", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "proxy_type", required=False, encrypted=False, default="http", validator=None
    ),
    field.RestField(
        "proxy_url",
        required=False,
        encrypted=False,
        default=None,
        validator=validator.String(
            max_len=4096,
            min_len=0,
        ),
    ),
    field.RestField(
        "proxy_port",
        required=False,
        encrypted=False,
        default=None,
        validator=validator.Number(
            max_val=65535,
            min_val=1,
        ),
    ),
    field.RestField(
        "proxy_username",
        required=False,
        encrypted=False,
        default=None,
        validator=validator.String(
            max_len=50,
            min_len=0,
        ),
    ),
    field.RestField(
        "proxy_password",
        required=False,
        encrypted=True,
        default=None,
        validator=validator.String(
            max_len=8192,
            min_len=0,
        ),
    ),
    field.RestField(
        "proxy_rdns", required=False, encrypted=False, default=None, validator=None
    ),
]
model_proxy = RestModel(fields_proxy, name="proxy")

fields_logging = [
    field.RestField(
        "loglevel", required=False, encrypted=False, default="INFO", validator=None
    )
]
model_logging = RestModel(fields_logging, name="logging")

endpoint = MultipleModel(
    "splunk_ta_remedy_settings",
    models=[model_additional_parameters, model_proxy, model_logging],
)


class SettingsHandler(AdminExternalHandler):
    """
    Manage Settings Details.
    """

    def __init__(self, *args, **kwargs):
        log_filename = "splunk_ta_remedy_settings"
        self.logger = log.Logs().get_logger(log_filename)
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)
        if confInfo.get("proxy") and "proxy_url" in confInfo["proxy"]:
            confInfo["proxy"]["proxy_url"] = confInfo["proxy"]["proxy_url"].strip("[]")

    def handleEdit(self, conf_info):
        """
        Managing IPv6 address in proxy host.
        """
        if self.payload.get("proxy_url") and self.is_ipv6(
            self.payload.get("proxy_url")
        ):
            self.payload["proxy_url"] = f'[{self.payload.get("proxy_url")}]'
            self.logger.debug(
                f'Added the square brackets around the proxy host: {self.payload.get("proxy_url")}'
            )
        AdminExternalHandler.handleEdit(self, conf_info)

    def is_ipv6(self, ipv6_address):
        try:
            ipaddress.IPv6Address(ipv6_address)
            self.logger.debug("proxy_url contains IPv6 address.")
            return True
        except ipaddress.AddressValueError:
            self.logger.debug(f"Not a valid IPv6 address: {ipv6_address}.")
            return False


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=SettingsHandler,
    )
