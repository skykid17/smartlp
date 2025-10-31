#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import time
import traceback
import re
from urllib.parse import quote_plus, urlencode

import requests
import solnlib
from defusedxml import ElementTree
from typing import Optional, Callable, Dict, Any, List, Union

from .logger_adapter import CSLoggerAdapter

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("kvstore_collection")
)


class KVStoreApiError(Exception):
    def __init__(self, message: str = "", response=None):
        super(KVStoreApiError, self).__init__(message)
        self.response = response

    def __str__(self) -> str:
        message = (
            super(KVStoreApiError, self).__str__()
            or "Splunk KVStore API unexpected error."
        )
        if self.response is not None:
            all_msgs = [message]
            try:
                root = ElementTree.fromstring(self.response.text)
                for msg in root.iter("msg"):
                    msg_text = msg.attrib.get("type")
                    if msg_text:
                        msg_text += f": {msg.text}"
                    else:
                        msg_text = msg.text
                    all_msgs.append(msg_text)
            except ElementTree.ParseError:
                one_liner = self.response.text.replace("\n", " ")
                logger.debug(
                    f"{message} Response data dump: status_code={self.response.status_code}, response_text={one_liner}"
                )
            except Exception as e:
                msg = f"KVStore API extract response general exception: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger, e, "KVstore Error", msg_before=f"{msg} {tb}"
                )
                raise

            return " | ".join(all_msgs)

        return message


def handle_kvstore_exceptions(request_fn: Callable) -> Callable:
    def kwstore_request_wrapper(*args, **kvargs) -> Callable:
        try:
            start_time = time.time()
            res = request_fn(*args, **kvargs)
            logger.debug(
                f"kvstore_benchmark_{request_fn.__name__}={time.time()-start_time} seconds"
            )
            return res
        except Exception as e:
            msg = f"{request_fn.__name__}: kvstore_response_exception={e}"
            tb = " ---> ".join(traceback.format_exc().split("\n"))
            solnlib.log.log_exception(
                logger, e, "KVstore Error", msg_before=f"{msg} {tb}"
            )
            if isinstance(e, KVStoreApiError):
                raise
            raise KVStoreApiError(msg) from e

    return kwstore_request_wrapper


class KVStoreCollection:
    def __init__(self, server_uri: str, token: str, app: str, name: str):
        self._server_uri = server_uri
        self._token = token
        self._app = app
        self._name = name
        self._user = "nobody"
        self._service = f"{self._server_uri}/servicesNS/{self._user}/{self._app}/storage/collections"
        self._headers = {"Authorization": f"Bearer {self._token}"}

    @property
    def collection_name(self) -> str:
        return self._name

    @property
    def is_unsafe_endpoint(self) -> bool:
        return not (
            self._server_uri.startswith("https://127.0.0.1:")
            or self._server_uri.startswith("https://localhost:")
            or self._server_uri.startswith("https://[::1]:")
            or re.search(r"https://.*:8089", self._server_uri)
        )

    @classmethod
    def dump_response(cls, resp: requests.Response) -> None:
        request_body = resp.request.body
        if isinstance(request_body, str):
            request_body = " ".join(request_body.split("\n"))

        response_body = resp.text
        if isinstance(response_body, str):
            response_body = " ".join(response_body.split("\n"))

        logger.warning(
            f"kvstore_status_code={resp.status_code}, "
            + f"kvstore_method={resp.request.method}, "
            + f"kvstore_request_url={resp.request.url}, "
            + f"kvstore_request_body={request_body}, "
            + f'kvstore_response_body="{response_body}"'
        )

    @handle_kvstore_exceptions
    def make_get_request_to_kvstore(self, url: str) -> requests.Response:
        response = requests.get(
            url, headers=self._headers, verify=self.is_unsafe_endpoint
        )
        return response

    @handle_kvstore_exceptions
    def make_post_request_to_kvstore(
        self,
        url: str,
        data: Union[Dict[str, Any], str],
        headers: Optional[Dict[str, Any]] = None,
        json=None,
    ) -> requests.Response:
        response = requests.post(
            url,
            data=data if not json else None,
            headers=headers if headers else self._headers,
            json=json if json else None,
            verify=self.is_unsafe_endpoint,
        )
        return response

    @handle_kvstore_exceptions
    def make_delete_request_to_kvstore(self, url: str) -> requests.Response:
        response = requests.delete(
            url, headers=self._headers, verify=self.is_unsafe_endpoint
        )
        return response

    @handle_kvstore_exceptions
    def check_collection_exists(self) -> Optional[bool]:
        url = f"{self._service}/config/{self._name}"
        resp = self.make_get_request_to_kvstore(url)
        if resp.status_code // 100 == 2:
            return True

        if resp.status_code == 404:
            return False

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_check_collection_exists", resp)

    @handle_kvstore_exceptions
    def create_collection(self) -> Optional[bool]:
        url = f"{self._service}/config"
        data = f"name={self._name}"
        resp = self.make_post_request_to_kvstore(url, data)
        if resp.status_code // 100 == 2:
            return True

        if resp.status_code == 409 and " already exists" in resp.text:
            return True

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_create_collection", resp)

    @handle_kvstore_exceptions
    def delete_collection(self) -> Optional[bool]:
        url = f"{self._service}/config/{self._name}"
        resp = self.make_delete_request_to_kvstore(url)
        if resp.status_code // 100 == 2:
            return True

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_delete_collection", resp)

    @handle_kvstore_exceptions
    def define_collection_schema(self, schema: Dict[str, Any]) -> Optional[bool]:
        url = f"{self._service}/config/{self._name}"
        data = urlencode(schema)
        resp = self.make_post_request_to_kvstore(url, data)
        if resp.status_code // 100 == 2:
            return True

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_define_collection_schema", resp)

    @handle_kvstore_exceptions
    def search_records(
        self, query: Optional[Dict[str, Any]] = None, limit: int = 32023
    ) -> Optional[List[Dict[str, Any]]]:
        query_param = ";query=" + quote_plus(json.dumps(query)) if query else ""

        result = []
        skip = 0
        while True:
            url = f"{self._service}/data/{self._name}?skip={skip};limit={limit}{query_param}"
            logger.debug(f"kvstore_search_records: kvstore_request_url={url}")
            resp = self.make_get_request_to_kvstore(url)
            if resp.status_code // 100 != 2:
                break

            batch = resp.json()
            batch_size = len(batch)
            skip += batch_size
            result.extend(batch)
            if batch_size < limit:
                return result

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_search_records", resp)

    @handle_kvstore_exceptions
    def create_record(self, data: Dict[str, Any]) -> Optional[str]:
        url = f"{self._service}/data/{self._name}"
        resp = self.make_post_request_to_kvstore(
            url,
            data=None,
            headers=None,
            json=data,
        )

        logger.debug(f"kvstore_create_record: {resp.status_code}, {data}")
        if resp.status_code // 100 == 2:
            return resp.json()["_key"]

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_create_record", resp)

    @handle_kvstore_exceptions
    def update_record(self, key: str, data: Dict[str, Any]) -> Optional[bool]:
        url = f"{self._service}/data/{self._name}/{key}"
        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)
        resp = self.make_post_request_to_kvstore(
            url,
            data=None,
            headers=headers,
            json=data,
        )
        logger.debug(f"kvstore_update_record: {resp.status_code}, {data}")
        if resp.status_code // 100 == 2:
            return True

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_update_record", resp)

    @handle_kvstore_exceptions
    def batch_save(self, data: Dict[str, Any]) -> Optional[bool]:
        url = f"{self._service}/data/{self._name}/batch_save"
        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)
        resp = self.make_post_request_to_kvstore(
            url,
            data=None,
            headers=headers,
            json=data,
        )
        logger.debug(f"kvstore_batch_save: {resp.status_code}, {data}")
        if resp.status_code // 100 == 2:
            return True

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_batch_save", resp)

    @handle_kvstore_exceptions
    def delete_records(self, query=None, key=None) -> Optional[bool]:
        url = f"{self._service}/data/{self._name}"
        if key:
            if isinstance(key, (list, tuple)):
                list_keys = [{"_key": val} for val in key]
                url += "?query=" + quote_plus(json.dumps({"$or": list_keys}))
            else:
                url += "/" + key
        elif query:
            url += "?query=" + quote_plus(json.dumps(query))

        logger.debug(f"kvstore_delete_records: kvstore_request_url={url}")
        resp = self.make_delete_request_to_kvstore(url)
        if resp.status_code // 100 == 2:
            return True

        self.dump_response(resp)
        raise KVStoreApiError("kvstore_delete_records", resp)
