#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import time
import json
import platform
import threading
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import TypeVar

from splunk_ta_o365.common.settings import Logging, Proxy
from splunk_ta_o365.common.portal import O365PortalRegistry
from splunk_ta_o365.common.tenant import O365Tenant
from splunksdc.config import StanzaParser, StringField

from splunksdc import logging
from splunksdc.batch import BatchExecutor
from splunksdc.collector import SimpleCollectorV1
from splunksdc.utils import LogExceptions, LogWith

from .consts import (
    DEFAULT_RETRY_LIST,
    VALID_ENTRA_ID_TYPES,
    NUMBER_OF_THREADS,
    METADATA_ENDPOINTS,
    DEFAULT_SOURCETYPE,
    TOKEN_REFRESH_WINDOW,
)

logger = logging.get_module_logger()
token_refresh_lock = threading.RLock()
Requests = TypeVar("Requests")


class MicrosoftEntraIDConsumer(object):
    def __init__(
        self, name, app, config, event_writer, portal, proxy, token, input_args
    ):
        self._name = name
        self._app = app
        self._config = config
        self._event_writer = event_writer
        self._portal = portal
        self._proxy = proxy
        self._token = token
        self._input_args = input_args

        self._now: datetime = time.time

    def is_aborted(self) -> bool:
        """
        Check if aborted

        Returns:
            bool: aborted or not
        """
        return self._app.is_aborted()

    def _get_session(self) -> Requests:
        """
        Get session and authenticate token

        Returns:
            Requests: requests session object
        """
        session = self._proxy.create_requests_session()
        self._token.auth(session)
        return session

    def _handle_token_expiration(self, session: Requests) -> None:
        """
        Handle token update for multiple threads, making sure only
        one thread update the token.

        Args:
            session (Requests): requests session object
        """
        if self._token.need_retire(TOKEN_REFRESH_WINDOW):
            with token_refresh_lock:
                # self._token object is shared across threads, simultaneous calls to update token from multiple threads could cause race conditions. Using lock to ensure that only one thread updates the token at a time.
                self._update_session(session)

    def _update_session(self, session: Requests) -> None:
        """
        This method is used to check if the token is expired or it's about to expire.

        Args:
            session (Requests): A requests.Session object to use for the request.

        Returns:
            None
        """
        if self._token.need_retire(TOKEN_REFRESH_WINDOW):
            logger.info("Access token will expire soon. Hence, refreshing the token.")
            self._token.auth(session)

    def _ingest(self, event: dict, endpoint: str) -> None:
        """
        This method is used to ingest the event.

        Args:
            event (dict): Single Entra ID event.
            endpoint: entra_id_type which would be used to get the source name.

        Returns:
            None
        """
        self._event_writer.write_event(
            json.dumps(event, ensure_ascii=False),
            source=self._portal.get_source(endpoint),
            sourcetype=self._input_args.get("sourcetype", DEFAULT_SOURCETYPE),
        )

    def allocate(self):
        """
        Session will be allocated to each thread of do() method
        to avoid any connection-pool failure or any
        discrepancy with threading

        Allocate a new HTTP session and configure retry policies
        for handling network errors.

        Returns:
        A new instance of requests.Session with the retry policies configured.
        """
        session = self._proxy.create_requests_session()
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                allowed_methods=None,
                status_forcelist=DEFAULT_RETRY_LIST,
            )
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def discover(self):
        """
        The discover method is a generator that yields all the jobs/tasks to fetch.

        Yields:
            list: A list entra_id_type selected by user.

        Raises:
            Exception: If there is any error while creating tasks,
            it will raise an exception.
        """
        try:
            session = self._get_session()
            metadata_types = list(self._input_args.get("entra_id_type", "").split(","))
            metadata_list = set()
            for metadata in metadata_types:
                if metadata.lower() not in VALID_ENTRA_ID_TYPES:
                    logger.warning(
                        "Invalid Microsoft Entra ID Type hence skipping the data collection.",
                        entra_id_type=metadata,
                    )
                    continue
                metadata_list.add(metadata.lower())
            yield metadata_list

        except Exception:
            logger.error(
                "Failed to create the tasks for selected Entra ID types",
                exc_info=True,
                stack_info=True,
            )

    def _is_https(self, url: str) -> bool:
        """
        Checks whether the url starts with https:// or not.

        Args:
            url (str): url which should be validated.

        Returns:
            bool: True if url starts with https://, False otherwise.
        """
        if url.startswith("https://"):
            return True
        else:
            return False

    def _entra_id_metadata_collector(
        self, url: str, endpoint: str, session: Requests
    ) -> None:
        """
        This method is responsible for retrieving the Entra ID events by handling pagination and ingest all the events in splunk.

        Args:
            url (str): The url which would be used to collect Entra ID events.
            endpoint (str): entra_id_type used to get source name.
            session (Requests): A requests.Session object to use for the request.

        Returns:
            None
        """
        response = self._portal.perform(session, url)
        items = [] if response == {} else response["value"]
        total_ingested_events = 0
        empty_events_count = 0

        while True:
            for event in items:
                if event:
                    self._ingest(event, endpoint)
                    total_ingested_events += 1
                else:
                    empty_events_count += 1

            if "@odata.nextLink" in response:
                nextLink = response["@odata.nextLink"]
                logger.debug("NextLink found in the response.", nextlink=nextLink)

                if not self._is_https(nextLink):
                    raise ValueError(
                        "nextLink scheme is not HTTPS. nextLink URL: %s" % nextLink
                    )
                self._handle_token_expiration(session)
                response = self._portal.perform(session=session, url=nextLink)
                items = [] if response == {} else response["value"]
            else:
                break
        if empty_events_count:
            logger.warning(
                "Skipped the ingestion of empty events as API returned empty events because of wrong Query Parameters.",
                entra_id_type=endpoint,
                empty_events_count=empty_events_count,
            )
        logger.info(
            "Successfully ingested the events.",
            entra_id_type=endpoint,
            events_count=total_ingested_events,
        )

    def do(self, endpoint: str, session: Requests) -> None:
        """
        The do method retrieves the events for the provided entra id endpoint.In case of any exception, it logs the error.

        Args:
            endpoint (str): endpoint based on Entra ID Type.
            session (Requests): A requests.Session object to use for the request.

        Returns:
            None

        Raises:
            Exception: If the event collection fails.
        """

        try:
            self._handle_token_expiration(session)
            session = self._token.set_auth_header(session)
            logger.info(
                "Start Retrieving Microsoft Entra ID events.",
                timestamp=self._now(),
                entra_id_type=endpoint,
            )
            query_parameters = self._input_args.get("query_parameters", "")

            url = self._portal.make_url(METADATA_ENDPOINTS[endpoint], query_parameters)
            self._entra_id_metadata_collector(url, endpoint, session)
            logger.info(
                "End of Retrieving Microsoft Entra ID events.",
                timestamp=self._now(),
                entra_id_type=endpoint,
            )
        except Exception as e:
            logger.error(
                "An error occurred while collecting data",
                exc_info=True,
                stack_info=True,
            )

    def done(self, endpoint: str, results: None):
        """
        done method.
        """
        pass


class MicrosoftEntraID:
    def __init__(self, stanza):
        self._kind = stanza.kind
        self._name = stanza.name
        self._args = stanza.content
        self._start_time = int(time.time())

    def _create_metadata(self):
        stanza = self._kind + "://" + self._name
        parser = StanzaParser(
            [
                StringField("index"),
                StringField("host"),
                StringField("stanza", fillempty=stanza),
                StringField("sourcetype", default=DEFAULT_SOURCETYPE),
            ]
        )
        # often splunk will not resolve $decideOnStartup if not use the OS's
        # host name
        metadata = self._extract_arguments(parser)
        if metadata.host == "$decideOnStartup":
            metadata.host = platform.node()
        return metadata

    def _extract_arguments(self, parser):
        return parser.parse(self._args)

    def _get_tenant_name(self):
        parser = StanzaParser(
            [
                StringField("tenant_name"),
            ]
        )
        args = self._extract_arguments(parser)
        return args.tenant_name

    def _create_event_writer(self, app):
        metadata = self._create_metadata()
        return app.create_event_writer(None, **vars(metadata))

    def _create_tenant(self, config):
        tenant_name = self._get_tenant_name()
        return O365Tenant.create(config, tenant_name)

    def _create_executor(self):
        return BatchExecutor(number_of_threads=NUMBER_OF_THREADS)

    @property
    def name(self):
        return self._name

    @property
    def start_time(self):
        return self._start_time

    @LogWith(datainput=name, start_time=start_time)
    @LogExceptions(
        logger, "Data input was interrupted by an unhandled exception.", lambda e: -1
    )
    def run(self, app, config):
        session_key = config._service.token
        Logging.load(config).apply()
        proxy = Proxy.load(session_key)
        registry = O365PortalRegistry.load(config)
        tenant = self._create_tenant(config)
        entraid = tenant.create_graph_portal(registry)
        policy = tenant.create_v2_token_policy(registry)
        token = entraid.create_graph_token_provider(policy)
        event_writer = self._create_event_writer(app)
        portal = entraid.get_entra_id_metadata_communications()
        executor = self._create_executor()

        consumer = MicrosoftEntraIDConsumer(
            self.name, app, config, event_writer, portal, proxy, token, self._args
        )
        executor.run(consumer)
        return 0


def modular_input_run(app, config):
    array = app.inputs()
    data_input = MicrosoftEntraID(array[0])
    return data_input.run(app, config)


"""
    def main
    Accepts arguments for the tenant_name,entra_id_type,filter and runs SimpleCollectorV1 to ingest Microsoft Entra ID Metadata events from the API.
"""


def main():
    arguments = {
        "tenant_name": {
            "title": "Tenant Name",
            "description": "Which Office 365 tenant will be used.",
        },
        "entra_id_type": {
            "title": "Microsoft Entra ID Type",
            "description": "Which Entra ID events should be collected.",
        },
        "query_parameters": {
            "title": "Query Parameters",
            "description": "Which filters should be applied while retrieving the events.",
            "required_on_edit": False,
            "required_on_create": False,
        },
    }

    SimpleCollectorV1.main(
        modular_input_run,
        title="Splunk Add-on for Microsoft Office 365 Entra ID Metadata",
        description="Ingest Microsoft Entra ID Metadata events",
        use_single_instance=False,
        arguments=arguments,
    )
