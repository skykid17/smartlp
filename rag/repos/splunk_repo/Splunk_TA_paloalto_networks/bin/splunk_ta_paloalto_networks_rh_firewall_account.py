#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test

import xmltodict
import logging

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from firewall_client import FirewallClient
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.error import RestError
from typing import Dict, Any
from palo_utils import logger_instance, get_proxy_settings

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "username", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "password", required=True, encrypted=True, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "splunk_ta_paloalto_networks_firewall_account",
    model,
    config_name="firewall_account",
)

logger = logger_instance("firewall_account")


class FirewallHandler(AdminExternalHandler):
    def validate_firewall_creditentials(self) -> None:
        try:
            firewall_host = self.callerArgs.id
            firewall_username = self.callerArgs.data["username"][0]
            firewall_password = self.callerArgs.data["password"][0]
            proxy_config = get_proxy_settings(logger, self.getSessionKey())
            firewall_client = FirewallClient(
                firewall_host,
                firewall_username,
                firewall_password,
                logger,
                proxy_config,
            )
            if not firewall_client._validate_credentials():
                raise RestError(
                    407,
                    "Failed to connect/authenticate to Firewall/Panorama. "
                    "Invalid Firewall/Panorama information provided or if connection requires proxy, "
                    "please make sure that Configuration => Proxy settings are correct",
                )
        except Exception as e:
            raise RestError(400, str(e)) from e

    def handleCreate(self, confInfo: Dict[str, Any]) -> None:
        self.validate_firewall_creditentials()
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleEdit(self, confInfo: Dict[str, Any]) -> None:
        self.validate_firewall_creditentials()
        AdminExternalHandler.handleEdit(self, confInfo)


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=FirewallHandler,
    )
