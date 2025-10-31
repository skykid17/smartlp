#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#


import requests
import json
import traceback

from time import time
from urllib.parse import quote_plus
from json.decoder import JSONDecodeError
from typing import Optional, Union, Generator, Callable, Dict, Any, List, Tuple
from requests import Response

import solnlib

from .logger_adapter import CSLoggerAdapter

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("crowdstrike_helpers")
)


MAX_FORCED_AUTH_ATTEMPTS = 2
FIND_RESULTS_DEFAULT_CHUNK_SIZE = 1000
VERIFY = True


class CrowdStrikeApiError(Exception):
    def __init__(self, message: str = "", response: Optional[Response] = None) -> None:
        super(CrowdStrikeApiError, self).__init__(message)
        self.response = response

    def __str__(self):
        message = (
            super(CrowdStrikeApiError, self).__str__()
            or "CrowdStrike API unexpected error"
        )
        if self.response is not None:
            all_msgs = [message]
            try:
                resp_json = json.loads(self.response.text)
                for err in resp_json.get("errors") or [{}]:
                    all_msgs.append(f'code={err["code"]}, message={err["message"]}')
            except (JSONDecodeError, KeyError):
                one_liner = self.response.text.replace("\n", " ")
                logger.debug(
                    f"{message} Response data dump: status_code={self.response.status_code}, response_text={one_liner}"
                )
            except Exception as e:
                msg = f"CrowdStrike API extract response general exception: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger, e, "CrowdSrtike API Error", msg_before=f"{msg} {tb}"
                )
                raise

            return "|".join(all_msgs)

        return message


class CrowdStrikeApiAccessDenied(CrowdStrikeApiError):
    pass


class CrowdStrikeApiAuthorizationFailed(CrowdStrikeApiAccessDenied):
    pass


class CrowdstrikeApiInvalidBearerToken(CrowdStrikeApiAccessDenied):
    pass


def crowdstrike_except_and_auth(fn: Callable) -> Callable:
    def crowdstrike_except_and_auth_wrapper(self, *args: Any, **kwargs: Any) -> None:

        for attempt in range(MAX_FORCED_AUTH_ATTEMPTS + 1):
            try:
                self.auth(attempt > 0)
            except CrowdStrikeApiAuthorizationFailed as csaf:
                solnlib.log.log_authentication_error(
                    logger,
                    csaf,
                    msg_after=f"Authentication to CrowdStrike API has failed: {csaf}",
                )
                raise
            except CrowdStrikeApiError as cse:
                solnlib.log.log_exception(
                    logger,
                    cse,
                    "CrowdSrtike API Error",
                    msg_after=f"Unexpected API error during authentication: {cse}",
                )
                raise
            except Exception as e:
                msg = f"Unexpected error during authentication: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_authentication_error(
                    logger,
                    e,
                    msg_after=msg + tb,
                )
                raise

            try:
                return fn(self, *args, **kwargs)
            except CrowdstrikeApiInvalidBearerToken as ibt:
                if attempt == MAX_FORCED_AUTH_ATTEMPTS:
                    raise
                continue
            except CrowdStrikeApiError as cse:
                solnlib.log.log_exception(
                    logger,
                    cse,
                    "Unexpected API Error",
                    msg_before=f"Unexpected API request error: {cse}",
                )
                raise
            except Exception as e:
                msg = f"Unexpected error: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger,
                    e,
                    "Unexpected Error",
                    msg_before=f"{msg} {tb}",
                )
                raise

    return crowdstrike_except_and_auth_wrapper


class CrowdStrikeClient:
    def __init__(
        self,
        base_url: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self.__base_url = base_url
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__token = None
        self.__expires = 0
        self.__proxies = {"http": proxy, "https": proxy} if proxy else {}

    @staticmethod
    def log_rest_error(response: Response) -> None:
        logger.error(str(CrowdStrikeApiError(response=response)))

    def configure(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> None:
        if base_url is not None:
            self.__base_url = base_url
            self.__token = None

        if client_id is not None:
            self.__client_id = client_id
            self.__token = None

        if client_secret is not None:
            self.__client_secret = client_secret
            self.__token = None

        if proxy is not None:
            self.__proxies = {"http": proxy, "https": proxy} if proxy else {}
            self.__token = None

    def auth(self, force: bool = False) -> str:
        endpoint = "/oauth2/token"

        if not force and self.__token and time() < self.__expires:
            return self.__token

        assert self.__client_id and self.__client_secret

        url = f"{self.__base_url}{endpoint}"
        payload = f"client_id={self.__client_id}&client_secret={self.__client_secret}"
        headers = {
            "accept": "application/json",
            "Content-type": "application/x-www-form-urlencoded",
        }

        logger.debug(f"CrowdStrike API request: action='authenticate' url='{url}'")
        response = requests.post(
            url, headers=headers, data=payload, proxies=self.__proxies, verify=VERIFY
        )

        if response.status_code == 201:
            resp_json = response.json()
            self.__token = resp_json.get("access_token")
            self.__expires = time() + resp_json.get("expires_in")
        elif response.status_code in (400, 401, 403):
            self.__token = None
            self.__expires = 0
            raise CrowdStrikeApiAuthorizationFailed(response=response)
        else:
            self.__token = None
            self.__expires = 0
            raise CrowdStrikeApiError(response=response)

        return self.__token

    @property
    def headers(self) -> Dict[str, Any]:
        return {
            "Authorization": f"Bearer {self.__token}",
            "Content-Type": "application/json",
        }

    @crowdstrike_except_and_auth
    def find_devices_get_chunk(
        self, filter: str = "", offset: int = 0, limit: int = 100, sort: str = ""
    ) -> Tuple[str, int, int]:
        endpoint = "/devices/queries/devices/v1"
        url = f"{self.__base_url}{endpoint}?limit={limit}&offset={offset}"
        if filter:
            url += f"&filter={quote_plus(filter)}"
        if sort:
            url += f"&sort={sort}"

        logger.debug(
            f"CrowdStrike API request: action='find_updated_devices' url='{url}'"
        )
        response = requests.get(
            url, headers=self.headers, proxies=self.__proxies, verify=VERIFY
        )
        if response.status_code == 200:
            resp_json = response.json()
            resources = resp_json["resources"]
            next_offset = resp_json["meta"]["pagination"]["offset"]
            total = resp_json["meta"]["pagination"]["total"]
            return resources, next_offset, total

        if response.status_code == 401:
            raise CrowdstrikeApiInvalidBearerToken(response=response)

        raise CrowdStrikeApiError(response=response)

    @crowdstrike_except_and_auth
    def get_modified_timestamp(self, device_id: str) -> str:
        endpoint = f"/devices/entities/devices/v2?ids={device_id}"
        url = f"{self.__base_url}{endpoint}"
        logger.debug(
            f"CrowdStrike API request: action='get_modified_timestamp' url='{url}'"
        )
        response = requests.get(
            url, headers=self.headers, proxies=self.__proxies, verify=VERIFY
        )
        if response.status_code == 200:
            resp_json = response.json()
            return resp_json["resources"][0]["modified_timestamp"]

        if response.status_code == 401:
            raise CrowdstrikeApiInvalidBearerToken(response=response)

        raise CrowdStrikeApiError(response=response)

    def find_devices_changed_after(
        self,
        isotime_str: Optional[str] = None,
        limit: int = FIND_RESULTS_DEFAULT_CHUNK_SIZE,
    ) -> Generator[Tuple[str, int, int], None, None]:
        filter = f"modified_timestamp:>'{isotime_str}'" if isotime_str else ""

        offset, total, sort = 0, float("inf"), "modified_timestamp.asc"
        while offset < total:
            resources, offset, total = self.find_devices_get_chunk(
                filter, offset, limit, sort
            )
            yield resources, offset, total
            if offset + limit >= 10000:
                last_device_id = resources[-1]
                isotime_str = self.get_modified_timestamp(last_device_id)
                filter = f"modified_timestamp:>'{isotime_str}'" if isotime_str else ""
                offset = 0

    @crowdstrike_except_and_auth
    def get_device_chunk_info(self, ids: List[str]) -> Optional[str]:
        endpoint = "/devices/entities/devices/v2"
        ids = "&".join([f"ids={id}" for id in ids])
        url = f"{self.__base_url}{endpoint}?{ids}"

        logger.debug(f"CrowdStrike API request: action='get_devices_info' url='{url}'")

        response = requests.get(
            url, headers=self.headers, proxies=self.__proxies, verify=VERIFY
        )
        if response.status_code == 200:
            resp_json = response.json()
            return resp_json["resources"]

        if response.status_code == 401:
            raise CrowdstrikeApiInvalidBearerToken(response=response)

        raise CrowdStrikeApiError(response=response)

    def get_devices_info(
        self, ids: Union[Dict[str, Any], List[Any], None], limit: int
    ) -> List[str]:
        result = []
        for i in range(0, len(ids), limit):
            result += self.get_device_chunk_info(ids[i : i + limit])

        return result
