#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import traceback
import os
import time
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery
from splunk_ta_gcp.common.credentials import CredentialFactory
from splunk_ta_gcp.common.settings import Settings
from splunksdc import log as logging
from splunksdc.config import (
    BooleanField,
    DateTimeField,
    IntegerField,
    StanzaParser,
    StringField,
)
from splunksdc.utils import LogExceptions

from . import bigquery_consts as bqc
from splunk_ta_gcp.common.checkpoint import KVStoreCheckpoint
from splunk_ta_gcp.modinputs.bigquery.checkpoint import CheckpointMigration

logger = logging.get_module_logger()


class BigQueryDataInputs(object):
    def __init__(self, app, config):
        self._app = app
        self._config = config

    def load(self):
        content = self._config.load("google_cloud_billing_inputs")
        for name, fields in list(content.items()):
            parser = StanzaParser(
                [
                    BooleanField(
                        "disabled", default=False, reverse=True, rename="enabled"
                    ),
                    StringField("google_bq_dataset", required=True),
                    StringField("google_bq_table", required=True),
                    StringField(
                        "google_credentials_name", required=True, rename="profile"
                    ),
                    StringField("google_project", required=True),
                    StringField(
                        "sourcetype", default="google:gcp:bigquery:billing:report"
                    ),
                    IntegerField("google_bq_query_limit", default=bqc.bq_query_limit),
                    IntegerField(
                        "google_bq_request_page_size", default=bqc.bq_request_page_size
                    ),
                    DateTimeField("ingestion_start", default="1970-01-01"),
                    IntegerField("polling_interval", default=86400, rename="interval"),
                    StringField("index"),
                ]
            )
            params = parser.parse(fields)
            if params.enabled:
                yield name, params

    def __iter__(self):
        return self.load()


class GoogleCloudBigQuery(object):
    """
    BigQuery  object
    params: settings
    params:BigQuery Handler
    """

    def __init__(self, handler):
        self._settings = None
        self._report_handler = handler
        self._collection = None
        self._collection_name = None

    @LogExceptions(
        logger, "Modular input was interrupted by an unhandled exception.", lambda e: -1
    )
    def __call__(self, app, config):
        self._settings = Settings.load(config)
        self._settings.setup_log_level()
        inputs = BigQueryDataInputs(app, config)

        scheduler = app.create_task_scheduler(self.run_task)
        for name, params in inputs:
            scheduler.add_task(name, params, params.interval)

        if scheduler.idle():
            logger.info("No data input has been enabled.")

        scheduler.run([app.is_aborted, config.has_expired])
        return 0

    def run_task(self, app, name, params):
        return self._run_ingest(app, name, params)

    @LogExceptions(
        logger, "Data input was interrupted by an unhandled exception.", lambda e: -1
    )
    def _run_ingest(self, app, name, params):
        """
        All the steps involved in the pipeline to ingest data for application configured
        :param app: A request object that originates from the UI
        :param name: A data input name
        :param params: Parameters configured during input creation
        :return: 0
        """

        if len(params.google_bq_dataset) == 0:
            logger.warning(
                " Billing ingestion error. "
                + " You must use the Cloud BigQuery Billing input in order to ingest billing data. "
            )
            return

        logger.info("Data input started", data_input=name, **vars(params))
        config = app.create_config_service()

        # Step 1 - Create credentials object
        logger.debug("Calling create_credentials ")
        try:
            credentials = self._create_credentials(config, params.profile)
        except Exception as e:
            traceback.print_exc()
            raise e

        # Step 2 - Create a BigQuery Client
        logger.debug("Calling bigquery.Client")
        try:
            # Client to bundle configuration needed for API requests.
            bq_client = self._build_bigquery_client(credentials, params.google_project)

        except Exception as e:
            traceback.print_exc()
            raise e

        # Step 3 - Create a event writer
        logger.debug("Calling create_event_writer")
        try:
            event_writer = app.create_event_writer(
                sourcetype=params.sourcetype, index=params.index
            )

        except Exception as e:
            traceback.print_exc()
            raise e
        logger.debug("Calling Data Collection for {}".format(self._report_handler))

        # Load/Create KV collection
        self._initialize_collection(app, config)

        # create checkpoint key
        checkpoint_key = "{}.{}.{}.{}".format(
            name,
            params.google_project,
            params.google_bq_dataset,
            params.google_bq_table,
        )

        # check migration status against checkpoint_key
        is_migrated = self._get_migration_status(checkpoint_key)

        file_name = "".join([name, ".ckpt"])
        file_path = os.path.join(app.workspace(), file_name)

        # check if checkpoint file is exists or not
        is_file_ckpt_exist = self._is_file_path_exist(file_path)

        # check if file checkpoint is migrated and file path exist then delete the checkpoint file in second invocation
        if is_migrated and is_file_ckpt_exist:
            self._delete_checkpoint_file(file_path)

        # check if file checkpoint is not migrated and file path exists then migrate it (old input)
        if not is_migrated and is_file_ckpt_exist:
            self._perform_migration(app, config, name)

        # Step 4 - Start Data Collection
        handler = self._report_handler(
            self._collection,
            event_writer,
            bq_client,
            name,
            params.google_project,
            params.google_bq_dataset,
            params.google_bq_table,
            params.google_bq_query_limit,
            params.google_bq_request_page_size,
            params.ingestion_start,
            app,
        )
        handler.run()

        return 0

    def _build_bigquery_client(self, credentials, google_project):
        session = AuthorizedSession(credentials)
        proxy = self._settings.make_proxy_uri()
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}
            session._auth_request.session.proxies = {
                "http": proxy,
                "https": proxy,
                "socks5": proxy,
            }

        return bigquery.Client(
            credentials=credentials, project=google_project, _http=session
        )

    def _initialize_collection(self, app, config):
        """
        Prepare collection for checkpointing
        Load/Create the collection
        """
        self._collection_name = self._get_collection_name(app)
        self._collection = KVStoreCheckpoint(
            collection_name=self._collection_name, service=config._service
        )
        self._collection.get_collection()

    def _get_collection_name(self, app):
        """
        Get collection name
        """
        appname = app._app_name
        google_service = app._modular_name
        return "_".join([appname, google_service])

    def _get_migration_status(self, checkpoint_key):
        """
        Get migration flag value
        Returns:
            bool: 0 or 1
        """
        ckpt = self._collection.get(checkpoint_key)
        if ckpt:
            return ckpt.get("is_migrated", 0)
        return 0

    def _perform_migration(self, app, config, name):
        """
        Perform migration of file checkpoint to KVStore
        Args:
            app (Any): App object
            config (Any): Config object
        """
        migrate_ckpt = CheckpointMigration(self._collection, app, config)
        migrate_ckpt.load_checkpoint(name)
        migrate_ckpt.migrate()
        migrate_ckpt.send_notification(
            f"Migration Completed for input {name} {time.time()}.",
            "Splunk Add-on for Google Cloud Platform: Checkpoint for {} input is now migrated to KV Store.".format(
                name
            ),
        )

    def _delete_checkpoint_file(self, file_path):
        """
        delete the file checkpoint once migration is completed
        Args:
            file_path (Any): file path value
        """
        CheckpointMigration.remove_file(file_path)

    def _is_file_path_exist(self, file_path):
        """
        check if file path exists or not
        Args:
            file_path (Any): file path value
        """
        return os.path.exists(file_path)

    """def _get_proxy_info(self, scheme="http"):
        if scheme not in ["http", "https"]:
            return

        proxy = self._settings.make_proxy_uri()
        if not proxy:
            return
        parts = urlparse(proxy)
        proxy_scheme = parts.scheme

        traits = {
            "http": (PROXY_TYPE_HTTP, False),
            "socks5": (PROXY_TYPE_SOCKS5, False),
            "socks5h": (PROXY_TYPE_SOCKS5, True),
        }
        if proxy_scheme not in traits:
            logger.warning("Unsupported proxy protocol.")
            return

        proxy_type, proxy_rdns = traits[proxy_scheme]
        proxy_user, proxy_pass = parts.username, parts.password
        if proxy_user:
            proxy_user = unquote(proxy_user)
        if proxy_pass:
            proxy_pass = unquote(proxy_pass)

        return httplib2.ProxyInfo(
            proxy_type=proxy_type,
            proxy_rdns=proxy_rdns,
            proxy_host=parts.hostname,
            proxy_port=parts.port,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
        )
"""

    @staticmethod
    def _create_credentials(config, profile):
        factory = CredentialFactory(config)
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform.read-only",
            "https://www.googleapis.com/auth/bigquery",
            "https://www.googleapis.com/auth/cloud-platform",
        ]
        credentials = factory.load(profile, scopes)
        return credentials
