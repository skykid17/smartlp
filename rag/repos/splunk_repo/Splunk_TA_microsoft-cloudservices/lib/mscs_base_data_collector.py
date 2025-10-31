#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import abc
import time
from cattrs import ClassValidationError, transform_error
from solnlib.conf_manager import ConfManagerException, ConfManager

from splunk_ta_mscs.models import ProxyConfig
from mscs_common_utils import (
    get_account_from_config,
    get_api_details,
    APP_NAME,
)
from splunk_ta_mscs.mscs_credential_provider import get_credential

import mscs_common_api_error as mae
import mscs_consts
from splunk_ta_mscs.mscs_service_client import ServiceClient
from azure.core.rest import HttpRequest

MAX_RETRIES = 2
DEFAULT_TIMEOUT_SEC = 120
RESOURCE_MANAGER_ENDPOINT = "resource_manager"


class AzureBaseDataCollector(metaclass=abc.ABCMeta):
    def __init__(
        self,
        logger,
        session_key,
        account_name,
        endpoint=RESOURCE_MANAGER_ENDPOINT,
    ):
        """
        Init method
        :param logger: Logger object for logging in file
        :param session_key: Session key for the particular modular input
        :param account_name: Account name configured in the addon
        """
        self._logger = logger
        self._session_key = session_key
        self._account_name = account_name

        self._url = None
        self._api_version = None

        self._proxies = self._rest_get_proxy_config()
        self._account = get_account_from_config(
            self._logger, self._session_key, self._account_name
        )
        self._logger.info(
            f"{self._account.class_type.cloud_environment.name} selected as cloud environment"
        )
        self._manager_url = getattr(
            self._account.class_type.cloud_environment.endpoints, endpoint
        )

        service_credentials = get_credential(self._account, self._proxies.proxy_dict)

        credential_scopes = self._manager_url + "/.default"

        self._service = ServiceClient(
            service_credentials, self._proxies, scopes=credential_scopes
        )

    def _rest_get_proxy_config(self) -> ProxyConfig:
        try:
            settings_cfm = ConfManager(
                self._session_key,
                APP_NAME,
                realm="__REST_CREDENTIAL__#{}#configs/conf-splunk_ta_mscs_settings".format(
                    APP_NAME
                ),
            )
            splunk_ta_mscs_settings_conf = settings_cfm.get_conf(
                "splunk_ta_mscs_settings"
            ).get_all()

            proxy = splunk_ta_mscs_settings_conf[mscs_consts.PROXY]
            return ProxyConfig.from_dict(proxy)

        except ConfManagerException as e:
            self._logger.error(
                "Failed to fetch proxy details from configuration.",
                exc_info=e,
            )
            raise e
        except ClassValidationError as e:
            self._logger.error(
                f"Failed to validate ProxyConfig model. Error details: {transform_error(e)}",
                exc_info=e,
            )
            raise e

    def _parse_api_setting(self, api_stanza_name):
        """
        Method to parse api setting for the particular service
        :return api setting
        """
        api_setting = get_api_details(self._logger, self._session_key, api_stanza_name)
        self._url = api_setting[mscs_consts.URL]
        self._api_version = api_setting[mscs_consts.API_VERSION]
        return api_setting

    def _perform_request(
        self,
        url,
        method="get",
        params=None,
        body=None,
        headers={},
        timeout=DEFAULT_TIMEOUT_SEC,
        retries=MAX_RETRIES,
        log_error=True,
        **kwargs,
    ):
        """
        Method to perform request
        :param url: URL to be requested
        :param headers: headers to be passed
        :return response of the request
        """
        request = HttpRequest(
            method, url, headers=headers, params=params, content=body, **kwargs
        )
        self._logger.debug(f"URL: {request.url}")
        self._logger.debug(
            f"API params: {params} API body: {body} API headers: {headers} Kwargs: {kwargs}"
        )
        try:
            for _ in range(retries + 1):
                response = self._service.send(request)
                if response.status_code not in (429, 503):
                    break
                else:
                    sleep_duration = 60
                    for key in response.headers.keys():
                        """
                        The "retry-after" key keeps changing in response headers
                        so need to take dynamically
                        e.g "x-ms-ratelimit-microsoft.consumption-retry-after","x-ms-ratelimit-microsoft.consumption-tenant-retry-after","Retry-After"
                        """
                        if "retry-after" in key.lower():
                            sleep_duration = response.headers.get(key)
                            break
                    if response.status_code == 429:
                        self._logger.warn(
                            "Throttling limit reached. Hence retrying the request."
                        )
                    else:
                        self._logger.warn(
                            "Service is unavailable. Hence retrying the request."
                        )
                    time.sleep(int(sleep_duration))
            else:
                self._logger.warn("Maximum number of retries has been exhausted")
            if response.status_code != 204 and response.text:
                result = response.json()
            else:
                result = None
            self._error_check(response, result)
            return result
        except Exception as e:
            if log_error:
                self._logger.error(f"Error occurred in request url={url}", exc_info=e)
            raise e

    @staticmethod
    def _error_check(response, result):
        """
        Method to raise error
        :param response: response of the request
        :param result: json response
        """
        if response.status_code == 204:
            raise mae.APIError(response.status_code, error_msg="No Content")
        if isinstance(result, str):
            raise mae.APIError(status=response.status_code, result=result)
        else:
            if response.status_code != 200 or (result and result.get("error")):
                err = result.get("error", {})
                code = err.get("code", result)
                message = err.get("message", result)
                innererror = err.get("innererror", {})
                raise mae.APIError(
                    response.status_code,
                    code,
                    message,
                    innererror,
                    result,
                    response,
                    err,
                )
