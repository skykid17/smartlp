#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test

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
from palo_utils import logger_instance, get_proxy_settings, make_get_request
import logging

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "access_key_id", required=True, encrypted=True, default=None, validator=None
    ),
    field.RestField(
        "secret_access_key", required=True, encrypted=True, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "splunk_ta_paloalto_networks_iot_account", model, config_name="iot_account"
)
logger = logger_instance("iot_account")


class IoTAccountHandler(AdminExternalHandler):
    def validate_iot_creditentials(self) -> None:
        try:
            customer_id = self.callerArgs.id
            access_key_id = self.callerArgs.data["access_key_id"][0]
            secret_access_key = self.callerArgs.data["secret_access_key"][0]
            proxy_config = get_proxy_settings(logger, self.getSessionKey())
            base_url = (
                f"https://{customer_id}.iot.paloaltonetworks.com/pub/v4.0/device/list"
            )
            headers = {
                "X-Key-Id": access_key_id,
                "X-Access-Key": secret_access_key,
            }
            params = {"customerid": customer_id}
            response = make_get_request(
                url=base_url, params=params, headers=headers, proxies=proxy_config
            )
            if not response.ok:
                raise RestError(
                    407,
                    "Failed to connect/authenticate to IoT Security environment. "
                    "Invalid IoT Security information provided or if connection requires proxy, "
                    "please make sure that Configuration => Proxy settings are correct",
                )
        except Exception as e:
            raise RestError(400, str(e)) from e

    def handleCreate(self, confInfo: Dict[str, Any]) -> None:
        self.validate_iot_creditentials()
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleEdit(self, confInfo: Dict[str, Any]) -> None:
        self.validate_iot_creditentials()
        AdminExternalHandler.handleEdit(self, confInfo)


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=IoTAccountHandler,
    )
