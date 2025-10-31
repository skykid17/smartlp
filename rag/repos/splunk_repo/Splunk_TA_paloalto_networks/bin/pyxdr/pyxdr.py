#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from typing import Dict, List, Iterator, Optional, Any
from palo_utils import make_post_request, make_get_request
import json
import datetime
import logging
import random
import string
import hashlib
from solnlib import log

XDR_FILTERS = [
    "modification_time",
    "creation_time",
    "incident_id_list",
    "description",
    "alert_sources",
    "status",
]
XDR_OPERATORS = ["in", "contains", "gte", "lte", "eq", "neq", "value"]
XDR_STATUSES = [
    "new",
    "under_investigation",
    "resolved_threat_handled",
    "resolved_known_issue",
    "resolved_false_positive",
    "resolved_other",
    "resolved_auto",
]
XDR_SORT_FIELDS = ["modification_time", "creation_time"]
XDR_SORT_KEYWORDS = ["asc", "desc"]

DEFAULT_INCIDENT_LIMIT = 1000
DEFAULT_ALERT_LIMIT = 1000


class PyXDRError(Exception):
    """
    Generic PyXDR Error exception class.
    """


class PyXDRInputError(PyXDRError):
    """
    PyXDR Error exception class for user inputs.
    """


class PyXDRResponseError(PyXDRError):
    """
    PyXDR Error exception class for server responses.
    """


class PyXDRClient:
    """
    Python Client to interact with Cortex XDR API.
    """

    def __init__(
        self,
        api_key_id: int,
        api_key: str,
        base_url: str,
        logger: logging.Logger,
        proxy: Optional[Dict[str, str]] = None,
    ):
        self._api_key_id = api_key_id
        self._api_key = api_key
        self._base_url = base_url
        self._logger = logger
        self._proxy_enabled = proxy

    @staticmethod
    def get_now(timezone: datetime.timezone) -> datetime.datetime:
        """
        Datetime for particular timezone

        :param timezone: Timezone.
        :returns: Current date and time dependent on timezone.
        """
        return datetime.datetime.now(timezone)

    def generate_auth_headers(self) -> Dict[str, str]:
        """
        Generates authentication headers for Advanced key.
        Example from:
        https://docs.paloaltonetworks.com/cortex/cortex-xdr/cortex-xdr-api/cortex-xdr-api-overview/get-started-with-cortex-xdr-apis.html#id6b4e8ed2-9a0c-4f47-9573-63702ffdc29d

        :returns: authentication dict.
        """
        if not self._api_key:
            raise PyXDRInputError("API Key not set")

        nonce = "".join(random.choices(string.ascii_uppercase + string.digits, k=64))
        timestamp = int(PyXDRClient.get_now(datetime.timezone.utc).timestamp() * 1000)
        auth_key_hash = hashlib.sha256(
            f"{self._api_key}{nonce}{timestamp}".encode()
        ).hexdigest()

        return {
            "x-xdr-timestamp": str(timestamp),
            "x-xdr-nonce": nonce,
            "x-xdr-auth-id": str(self._api_key_id),
            "Authorization": auth_key_hash,
        }

    def _validate_credentials(self) -> bool:
        headers = self.generate_auth_headers()
        headers["Content-Type"] = "application/json"
        response_authinticate = make_get_request(
            f"{self._base_url}/public_api/v1/healthcheck/",
            headers=headers,
            proxies=self._proxy_enabled,
        )
        if response_authinticate.ok:
            return True
        return False

    def call_api_get_incidents(
        self,
        parameters: Dict[str, Any],
        url: str,
        limit: int,
        search_from: Optional[int] = None,
        search_to: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Calls Cortex XDR API and returns incidents if there are any.

        :param parameters: Parameters used in request.
        :param url: Url to call.
        :param limit: Limit of returned incidents.
        :param search_from: Integer representing the starting offset within the query result set from incidents returned.
        :param search_to: Integer representing the end offset within the result set after which incidents returned.
        :returns: Incidents fetched from API.
        """

        # Calculate pagination values.
        # If search_from is explicitly provided, use it, otherwise start from 0
        # If search_to is explicitly provided, use it, otherwise set it to min(limit, 100)
        # because if limit is provided and is lower than 100, no need to fetch 100 incidents
        parameters["search_from"] = search_from if search_from else 0
        parameters["search_to"] = search_to if search_to else min(100, limit)
        request_param = {"request_data": parameters}

        headers = self.generate_auth_headers()
        headers["Content-Type"] = "application/json"

        response = make_post_request(
            url,
            data=json.dumps(request_param),
            headers=headers,
            proxies=self._proxy_enabled,
        )

        self._logger.debug(f"Cortex XDR response: {response.text}")

        response.raise_for_status()

        reply = response.json().get("reply")
        if not reply:
            raise PyXDRResponseError("reply not present in API response")

        result_count = reply.get("result_count")
        if result_count is None:
            raise PyXDRResponseError("result_count not present in API response")
        if result_count == 0:
            return None

        incidents = reply.get("incidents")
        if not incidents or not isinstance(incidents, list):
            raise PyXDRResponseError("incidents keyword not present in API response")

        if len(incidents) != result_count:
            raise PyXDRResponseError("inconsistent result count in API response")

        return incidents

    def get_incidents(
        self,
        limit: int = DEFAULT_INCIDENT_LIMIT,
        sort_field: str = "creation_time",
        sort_order: str = "asc",
        search_from: Optional[int] = None,
        search_to: Optional[int] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Gets incidents from Cortex XDR API.

        :param limit: Limit of returned incidents per call.
        :param sort_field: Sort according to this field.
        :param sort_order: Order of sorting.
        :param search_from: Integer representing the starting offset within the query result set from incidents returned.
        :param search_to: Integer representing the end offset within the result set after which incidents returned.
        :param filters: Filters used in request.
        :returns: Fetched incidents.
        """

        if sort_field not in XDR_SORT_FIELDS:
            raise PyXDRInputError(
                f'Invalid sort field. Available sort fields: {", ".join(XDR_SORT_FIELDS)}'
            )
        if sort_order not in XDR_SORT_KEYWORDS:
            raise PyXDRInputError(
                f'Invalid sort order. Available sort orders: {", ".join(XDR_SORT_KEYWORDS)}'
            )

        if not filters:
            filters = []

        for flt in filters:
            field = flt.get("field")
            if not field or field not in XDR_FILTERS:
                raise PyXDRInputError(
                    f'Invalid filter field. Available filter fields are: {", ".join(XDR_FILTERS)}'
                )
            operator = flt.get("operator")
            if not operator or operator not in XDR_OPERATORS:
                raise PyXDRInputError(
                    f'Invalid filter operator. Available operators are: {", ".join(XDR_OPERATORS)}'
                )
            value = flt.get("value")
            if not value:
                raise PyXDRInputError("Invalid filter value")
            if field == "status" and value not in XDR_STATUSES:
                raise PyXDRInputError(
                    f'Invalid status filter. Available statuses are: {", ".join(XDR_STATUSES)}'
                )

        parameters = {
            "sort": {"field": sort_field, "keyword": sort_order},
            "filters": filters,
        }

        incidents = self.call_api_get_incidents(
            url=f"{self._base_url}/public_api/v1/incidents/get_incidents/",
            parameters=parameters,
            limit=limit,
            search_from=search_from,
            search_to=search_to,
        )

        return incidents

    def get_incident_extra_data(
        self, incident_id: int, alerts_limit: int = DEFAULT_ALERT_LIMIT
    ) -> Dict[str, Any]:
        """
        Gets extra incident data (i.e. alerts) given an incident ID

        :param incident_id: Id of incident that we want to get details for.
        :param alerts_limit: The maximum number of related alerts in the incident to retrieve.
        :returns: Incident with details.
        """
        try:
            if not incident_id or not isinstance(incident_id, int):
                error_message = f"Invalid incident ID (must be a positive integer) ID: {incident_id}"
                raise PyXDRInputError(error_message)

            if not alerts_limit or not isinstance(alerts_limit, int):
                error_message = f"Invalid alert limit (must be a positive integer) Limit: {alerts_limit}"
                raise PyXDRInputError(error_message)

            response = make_post_request(
                url=f"{self._base_url}/public_api/v1/incidents/get_incident_extra_data/",
                data=json.dumps(
                    {
                        "request_data": {
                            "incident_id": str(incident_id),
                            "alerts_limit": alerts_limit,
                        }
                    }
                ),
                headers=self.generate_auth_headers(),
                proxies=self._proxy_enabled,
            )
            self._logger.debug(response)
            response.raise_for_status()

            reply = response.json().get("reply")
            if not reply:
                error_message = "reply not present in API response"
                self._logger.error(error_message)
                raise PyXDRResponseError(error_message)

            return reply
        except PyXDRInputError as e:
            log.log_exception(
                self._logger,
                e,
                "Cortex XDR Error",
                msg_before=str(e),
            )
        except PyXDRResponseError as e:
            log.log_exception(
                self._logger,
                e,
                "Cortex XDR Error",
                msg_before=str(e),
            )
        except Exception as e:
            log.log_exception(
                self._logger,
                e,
                "Cortex XDR Error",
                msg_before="Unexpected error during Cortex XDR API quert",
            )
