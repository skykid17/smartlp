#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test
import logging
from typing import Dict, Any
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.error import RestError
from pyxdr.pyxdr import PyXDRClient
from palo_utils import logger_instance, get_proxy_settings

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "region", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "api_key_id", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "api_key", required=True, encrypted=True, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "splunk_ta_paloalto_networks_xdr_account", model, config_name="xdr_account"
)

logger = logger_instance("xdr_account")


class CortexAccountHandler(AdminExternalHandler):
    def validate_cortex_creditentials(self) -> None:
        try:
            tenant_name = self.callerArgs.id
            region = self.callerArgs.data["region"][0]
            api_key_id = self.callerArgs.data["api_key_id"][0]
            api_key = self.callerArgs.data["api_key"][0]
            proxy_config = get_proxy_settings(logger, self.getSessionKey())
            base_url = f"https://api-{tenant_name}.xdr.{region}.paloaltonetworks.com"
            xdr_client = PyXDRClient(
                api_key_id,
                api_key,
                base_url,
                logger,
                proxy_config,
            )
            if not xdr_client._validate_credentials():
                raise RestError(
                    407,
                    "Failed to connect/authenticate to Cortex XDR environment. "
                    "Invalid Cortex XDR information provided or if connection requires proxy, "
                    "please make sure that Configuration => Proxy settings are correct",
                )
        except Exception as e:
            raise RestError(400, str(e)) from e

    def handleCreate(self, confInfo: Dict[str, Any]) -> None:
        self.validate_cortex_creditentials()
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleEdit(self, confInfo: Dict[str, Any]) -> None:
        self.validate_cortex_creditentials()
        AdminExternalHandler.handleEdit(self, confInfo)


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=CortexAccountHandler,
    )
