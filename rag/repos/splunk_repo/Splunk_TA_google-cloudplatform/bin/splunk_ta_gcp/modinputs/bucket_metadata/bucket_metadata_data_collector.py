#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import io
import pathlib
import time
import sys
import csv
import json
import splunk_ta_gcp.legacy.common as tacommon
import concurrent.futures
import urllib.parse
from splunksdc.utils import LogExceptions, LogWith
from splunk_ta_gcp.common.settings import Settings
from splunk_ta_gcp.common.credentials import CredentialFactory
from google.auth.transport.requests import AuthorizedSession
from googleapiclient import discovery
from google.cloud import storage
from splunksdc import logging
from splunksdc.config import IntegerField, StanzaParser, StringField
from googleapiclient.errors import HttpError
from splunktalib.kv_client import KVClient, KVException, KVNotExists
from . import bucket_metadata_consts as bmc
from requests.adapters import HTTPAdapter

logger = logging.get_module_logger()

DEFAULT_SOURCETYPE = "google:gcp:buckets:data"


class BucketMetadataCollector:
    def __init__(self, stanza):
        self._name = stanza.name
        self._args = stanza.content
        self._settings = None
        self._parameters = self.extract_arguments()
        self._input_sourcetype = self._parameters.sourcetype
        self._event_writer = None
        self._kv_client = None
        self._chunk_size = self._parameters.chunk_size
        self._start_time = int(time.time())
        self._main_context = None

    @property
    def name(self):
        return self._name

    @property
    def start_time(self):
        return self._start_time

    @property
    def main_context(self):
        return self._main_context

    @main_context.setter
    def main_context(self, value):
        self._main_context = value

    def extract_arguments(self):
        parser = StanzaParser(
            [
                StringField("bucket_name", required=True),
                StringField("google_credentials_name", required=True, rename="profile"),
                StringField("google_project", required=True),
                StringField("sourcetype", default="google:gcp:buckets:metadata"),
                IntegerField("chunk_size", default=bmc.DEFAULT_CHUNK_SIZE),
                IntegerField("interval", default=3600),
                StringField("index"),
                IntegerField("number_of_threads", default=1),
            ]
        )
        arguments = parser.parse(self._args)
        return arguments

    def create_credentials(self, config, profile):
        factory = CredentialFactory(config)
        scopes = ["https://www.googleapis.com/auth/cloud-platform.read-only"]
        credentials = factory.load(profile, scopes)
        return credentials

    def get_proxy_object(self, proxy):
        return {
            "proxy_type": proxy.scheme,
            "proxy_url": proxy.host,
            "proxy_port": proxy.port,
            "proxy_username": proxy.username,
            "username": proxy.username,
            "proxy_password": proxy.password,
            "password": proxy.password,
            "proxy_rdns": proxy.rdns,
        }

    def get_service_object(self, config, profile):
        credentials = self.create_credentials(config, profile)
        session = AuthorizedSession(credentials)
        proxy = self._settings.make_proxy_uri()
        if proxy:
            session.proxies = {"http": proxy, "https": proxy, "socks5": proxy}
            session._auth_request.session.proxies = {
                "http": proxy,
                "https": proxy,
                "socks5": proxy,
            }
        http = tacommon.authorise_http_credential(
            self.get_proxy_object(self._settings.proxy), credentials
        )
        service = discovery.build("storage", "v1", http=http, cache_discovery=False)
        storage_client = storage.Client(
            credentials=credentials,
            _http=session,
            project=self._parameters.google_project,
        )
        if self._parameters.number_of_threads > 10:
            # The default pool size of storage client is 10
            # This warning would occur if we go with defaults: Connection pool is full, discarding connection: storage.googleapis.com. Connection pool size: 10
            # https://github.com/googleapis/python-storage/issues/253
            # If we are using threads to download files concurrently it is recommended to increase the pool size

            adapter = HTTPAdapter(
                pool_connections=self._parameters.number_of_threads,
                pool_maxsize=self._parameters.number_of_threads,
                max_retries=bmc.MAXIMUM_RETRIES,
                pool_block=True,
            )
            storage_client._http.mount("http://", adapter)
            storage_client._http._auth_request.session.mount("http://", adapter)
            storage_client._http.mount("https://", adapter)
            storage_client._http._auth_request.session.mount("https://", adapter)
        return service, storage_client

    def prepare_request(self, bucket_name, service):
        try:
            req = service.objects().list(bucket=bucket_name)
            return req
        except HttpError:
            logger.exception(
                f"An error occurred while processing request for bucket {bucket_name}."
            )
            sys.exit(0)

    def get_metadata(self, bucket_name, service, req):
        """
        Obtains metadata for a particular bucket

        Args:
            bucket_name (str): _description_
            service (object): Service object for fetching the metadata
            req (object): Request object which will be executed to fetch the data

        Returns:
            tuple: Metadata for a particular bucket and request object status indicating whether it has been exhausted or not.
                   The request object will be exhausted in last page
        """
        try:
            response_object_metadata = []
            resp = req.execute()
            response_object_metadata.extend(resp.get("items", []))
            req = service.objects().list_next(req, resp)
            logger.info(
                f"Sucecssfully obtained object information present in the bucket {bucket_name}."
            )
            return response_object_metadata, req
        except HttpError:
            logger.exception(
                f"An error occurred while processing request for bucket {bucket_name}."
            )
            sys.exit(0)

    def get_files(self, name, bucket_name, items):
        """
        Constrcts metadata for the files obtained

        Args:
            name (str): Name of the input
            bucket_name (str): Name of the bucket
            items (object): List of files obtained from API

        Returns:
            list: Metadata attached list of files
        """
        files = []
        for item in items:
            files.append(
                {
                    "filename": item.get("name"),
                    "md5Hash": item.get("md5Hash"),
                    "bytes_indexed": 0,
                    "_key": f"{name}_{bucket_name}_{item['name']}_{item['timeCreated']}",
                }
            )
        return files

    def get_list_of_files_to_be_ingested(self, files):
        """
        Identifies list of fresh files which are to be ingested by doing lookup
        in KvStore checkpoint

        Args:
            files (dict): Number of files obtained by making an API call

        Returns:
            list: List of fresh files which are to be ingested
        """
        files_to_ingest = []
        skipped_files = 0
        for file in files:
            try:
                key = file.get("_key")
                encoded_key = urllib.parse.quote(key.encode(), safe="")
                checkpoint_data = self._kv_client.get_collection_data(
                    collection=bmc.OBJECTS_COLLECTION,
                    app=bmc.APP_NAME,
                    key_id=encoded_key,
                )
            except KVNotExists:
                checkpoint_data = {}

            if checkpoint_data:
                if file.get("_key") == checkpoint_data.get("_key") and file.get(
                    "md5Hash"
                ) == checkpoint_data.get("md5Hash"):
                    skipped_files += 1
                    continue
            else:
                files_to_ingest.append(file)
        if skipped_files:
            logger.info(
                f"Skipping files as they are already ingested.",
                skipped_files=skipped_files,
            )
        logger.info(f"Number of files to ingest.", fresh_files=len(files_to_ingest))
        return files_to_ingest

    def get_ingest_bucket_metadata_flag(
        self, name, bucket_name, response_bucket_metadata
    ):
        """
        Checks whether there is any fresh data which is to be ingested

        Args:
            name (str): Name of the input
            bucket_name (str): Bucket name
            response_bucket_metadata (str): This response would be fetched from API

        Returns:
            tuple: A flag and temporary checkpoint dict related to particular bucket
        """
        ingest_bucket_metadata_flag = True
        metadata_checkpoint = {}
        metadata_checkpoint["updated"] = response_bucket_metadata["updated"]
        key = f"{name}_{bucket_name}_{response_bucket_metadata['timeCreated']}"
        metadata_checkpoint["_key"] = key
        try:
            checkpoint_data = self._kv_client.get_collection_data(
                collection=bmc.BUCKET_METADATA_COLLECTION, app=bmc.APP_NAME, key_id=key
            )
        except KVNotExists:
            checkpoint_data = {}
        if checkpoint_data:
            if checkpoint_data.get("updated") == metadata_checkpoint.get("updated"):
                ingest_bucket_metadata_flag = False
        return ingest_bucket_metadata_flag, metadata_checkpoint

    def ingest_bucket_metadata(
        self,
        bucket_name,
        ingest_bucket_metadata_flag,
        response_bucket_metadata,
        metadata_checkpoint,
    ):
        """
        Ingests metadata related to a particular bucket

        Args:
            bucket_name (str): Name of the bucket for which metadata is to be ingested
            ingest_bucket_metadata_flag (bool): Indicates whether metadata has been already ingested or not
            response_bucket_metadata (object): Metadata related to bucket
            metadata_checkpoint (dict): Temporary checkpoint dict for a bucket metadata collection
        """
        if ingest_bucket_metadata_flag:
            self._event_writer.write_events(
                [json.dumps(response_bucket_metadata)],
                source="{}:{}:{}".format(
                    self._parameters.profile,
                    self._parameters.google_project,
                    bucket_name,
                ),
                sourcetype="google:gcp:buckets:metadata",
            )
            try:
                logger.debug(
                    f"Updating metadata checkpoint.",
                    bucket_name=bucket_name,
                    checkpoint_data=metadata_checkpoint,
                )
                self._kv_client.update_collection_data(
                    collection=bmc.BUCKET_METADATA_COLLECTION,
                    data=metadata_checkpoint,
                    app=bmc.APP_NAME,
                    key_id=metadata_checkpoint.get("_key"),
                    owner="nobody",
                )
                logger.info(
                    f"Updated metadata checkpoint successfully.",
                    bucket_name=bucket_name,
                )
            except KVNotExists:
                self._kv_client.insert_collection_data(
                    collection=bmc.BUCKET_METADATA_COLLECTION,
                    data=metadata_checkpoint,
                    app=bmc.APP_NAME,
                    owner="nobody",
                )
                logger.info(
                    f"Updated metadata checkpoint successfully.",
                    bucket_name=bucket_name,
                )

            except KVException:
                logger.exception(
                    f"Failed to update metadata checkpoint.", bucket_name=bucket_name
                )
                sys.exit(0)

    def setup_sourcetypes(self):
        """
        Constructs soucrtype dictionary.

        Returns:
            dict: soucrtype dictionary
        """
        sourcetype = {}
        sourcetype["csv"] = "google:gcp:buckets:csvdata"
        sourcetype["xml"] = "google:gcp:buckets:xmldata"
        sourcetype["json"] = "google:gcp:buckets:jsondata"
        sourcetype[""] = "google:gcp:buckets:data"
        return sourcetype

    def file_extension(self, filename):
        """
        Obtains extension for a provided file

        Args:
            filename (dict): Metadata about file

        Returns:
            str: File extension
        """
        file_extension = ""
        file_extension = pathlib.Path(filename).suffix[1:]
        if not file_extension:
            logger.debug(
                f"File does not have an extension. Returning empty string.",
                file=filename,
            )
        return file_extension

    def write_fileobj_chunk(self, event_writer, fileobj, completed=False, **kwargs):
        """
        Ingests a chunk using event writer

        Args:
            event_writer (object): Event writer object
            fileobj (object): The response chunk which is to be ingested
            completed (bool, optional): Defaults to False.This would become true only when all chunks for a file
                                        have been downloaded
        """
        volume = 0
        metadata = event_writer._compose_event_metadata(kwargs)
        logger.debug(f"Start writing data to STDOUT.", **metadata)
        for chunk in event_writer._read_multiple_lines(fileobj):
            volume += len(chunk)
            data = event_writer._render_element("data", chunk)
            data = event_writer._CHUNK_TEMPLATE.format(data=data, done="", **metadata)
            event_writer._write(data)

        if completed:
            logger.debug(f"Write EOS")
            eos = event_writer._CHUNK_TEMPLATE.format(
                data="", done="<done/>", **metadata
            )
            event_writer._write(eos)
        logger.debug(f"Wrote data to STDOUT success.", size=volume)

    @LogWith(prefix=main_context)
    def ingest_file(self, app, client, bucket, file_dict):
        """
        This function would be executed by each of the worker threads.
        Number of worker threads parameter is configurable.
        Downloading from a file would happen in chunks.The chunk size is
        controlled by DEFAULT_CHUNK_SIZE parameter.

        Args:
            app (object): App object.Its construction will be done in splunksdc's collector.py
            client (object): Storage Client
            bucket (object): Bucket client
            file_dict (dict): Contains metadata related to file
        """
        if app.is_aborted():
            return
        logger.debug(f"File Detail: {file_dict}")

        # get name of file or blob to be downloaded
        filename = file_dict.get("filename")
        source = f"{self._parameters.profile}:{self._parameters.google_project}:{bucket.name}:{file_dict.get('filename')}"
        file_extension = self.file_extension(filename)

        if self._input_sourcetype == DEFAULT_SOURCETYPE:
            sourcetypes = self.setup_sourcetypes()
            logger.debug(
                f"File_extension={file_extension} and sourcetype={sourcetypes.get(file_extension, DEFAULT_SOURCETYPE)} source={source}"
            )
        """ col1 | the value, is , something | col3 """

        # # create a blob object and get the size of the blob
        blob = bucket.get_blob(filename)
        blob_size = blob.size
        logger.debug(f"File Size.", file_size=blob_size)

        ingestion_status = dict()
        ingestion_status["completed"] = False

        end = -1
        success = False
        # until the full blob is ingested
        while ingestion_status.get("completed") is False:
            if app.is_aborted():
                return
            # create a temp file object
            blob_contents = io.BytesIO()

            # if blob is smaller than chunk size, ingesting in one download
            start = end + 1

            # if its a large file, ingest in chunks
            end = (
                start + self._chunk_size
                if start + self._chunk_size < blob_size
                else blob_size
            )

            logger.info(
                f"Ingesting file.",
                file=file_dict.get("filename"),
                chunk_start=start,
                chunk_end=end,
            )
            client.download_blob_to_file(
                blob_or_uri=blob, file_obj=blob_contents, start=start, end=end
            )

            if end >= blob_size:
                logger.debug(
                    f"This is the last chunk for file.", file=file_dict.get("filename")
                )
                ingestion_status["completed"] = True

            blob_contents.seek(0)
            success = self.ingest_file_content(
                file_dict,
                ingestion_status,
                blob_contents,
                source,
                (
                    self._input_sourcetype
                    if self._input_sourcetype != DEFAULT_SOURCETYPE
                    else sourcetypes.get(file_extension, DEFAULT_SOURCETYPE)
                ),
            )
            blob_contents = None

        # Checkpoint
        if ingestion_status.get("completed", False) and success:
            file_dict["bytes_indexed"] = end
            logger.debug(f"Updating checkpoint for file.", file=filename)
            # update bytes ingested with
            self._kv_client.insert_collection_data(
                collection=bmc.OBJECTS_COLLECTION,
                data=file_dict,
                app=bmc.APP_NAME,
                owner="nobody",
            )
            logger.info(f"Updated checkpoint for file successfully.", file=filename)

    def parse_csv_line(self, line):
        """
        Parses a csv line.The built in csv parser is used to respect escapes etc.

        Args:
            line (str): Line which is to be parsed

        Returns:
            list: Fields as a list
        """
        if not isinstance(line, str):
            return []
        r = csv.reader([line], delimiter=bmc.DEFAULT_SPLIT_TOKEN)
        return list(r)[0]

    def ingest_csv_file(
        self, file_dict, ingestion_status, response_chunk, source, sourcetype
    ):
        """
        Processes and ingests a csv file

        Args:
            file_dict (dict): Contains metadata related to file
            ingestion_status (dict): Ingestion status dictionary which maintains temporary state
            response_chunk (object): This would be byte_stream object and its size would be equivalent to DEFAULT_CHUNK_SIZE
            source (str): Source which would be ingested along with event
            sourcetype (str): Sourcetype value which would be google:gcp:buckets:csvdata
        """
        # python will break the chunk into logical lines
        for response in response_chunk:
            csv_stream = response.decode("utf-8")
            # if it does not end with a new line then it
            # is a partial line. Save the line to use it later
            if not csv_stream.endswith("\n"):
                logger.debug(f"Truncated Line.", file=file_dict.get("filename"))
                ingestion_status["truncated_line"] = csv_stream
                continue

            # if fieldnames is not populated then, it must be the first line of
            # the file. extract the header
            if ingestion_status.get("fieldnames", None) is None:
                field_names = self.parse_csv_line(csv_stream)
                """ pass the csv stream into stream and delimeter, if this quotation ignore until next quotation \
                        handle the escapes """

                ingestion_status["fieldnames"] = field_names
                logger.debug(
                    f"Extracted Headers.",
                    headers=ingestion_status["fieldnames"],
                    file=file_dict.get("filename"),
                )
            else:
                # if we had a truncated line from the previous chunk
                # get that and prefix to the first line of current chunk
                # reset it to None since we are done using the incomplete
                # line
                if ingestion_status.get("truncated_line", None):
                    logger.debug(
                        f"Prefix previous partial line.",
                        file=file_dict.get("filename"),
                    )
                    csv_stream = ingestion_status.get("truncated_line") + csv_stream
                    ingestion_status["truncated_line"] = None

                # split by DEFAULT_SPLIT_TOKEN to get the values
                values = self.parse_csv_line(csv_stream)
                if len(values) < len(ingestion_status["fieldnames"]):
                    values += [""] * (len(ingestion_status["fieldnames"]) - len(values))

                # associate fields to values
                csv_data = {
                    ingestion_status["fieldnames"][i]: values[i]
                    for i in range(len(ingestion_status["fieldnames"]))
                }

                self._event_writer.write_fileobj(
                    json.dumps(csv_data, ensure_ascii=False),
                    source=source,
                    sourcetype=sourcetype,
                )

    def ingest_file_content(
        self, file_dict, ingestion_status, response_chunk, source, sourcetype
    ):
        """
        Ingest data for a file in chunks

        Args:
            file_dict (dict): Contains metadata related to file
            ingestion_status (dict): Ingestion status dictionary which maintains temporary state
            response_chunk (object): This would be byte_stream object and its size would be equivalent to DEFAULT_CHUNK_SIZE
            source (str): Source which would be ingested along with event
            sourcetype (str): Sourcetype which would be ingested along with event

        Returns:
            bool: Indicates whether ingestion was successful or not
        """
        try:
            # handle csv differently
            if sourcetype == "google:gcp:buckets:csvdata":
                self.ingest_csv_file(
                    file_dict, ingestion_status, response_chunk, source, sourcetype
                )
            else:
                response = response_chunk.read().decode("utf-8")
                self.write_fileobj_chunk(
                    self._event_writer,
                    response,
                    completed=ingestion_status.get("completed", False),
                    source=source,
                    sourcetype=sourcetype,
                )
            logger.debug(f"Write events for file.", file=file_dict.get("filename"))
            return True
        except UnicodeDecodeError:
            logger.info(
                f"Cannot ingest contents of {file_dict.get('filename')}, file with this extention is not yet supported in the TA"
            )
            return False

    def process_bucket_objects(self, app, service, client, bucket_name):
        """Downloads and ingests the files from specified bucket in concurrent manner using threadpool

        Args:
            app (object): App object.Its construction will be done in splunksdc's collector.py
            service (object): GCP Storage service object
            client (object): GCP Storage client object
            bucket_name (str): Name of the bucket from which objects will be downloaded and ingested
        """
        logger.info(f"Processing bucket.", bucket_name=bucket_name)
        bucket = client.bucket(bucket_name)
        req = self.prepare_request(bucket_name, service)
        while req:
            response_object_metadata, req = self.get_metadata(bucket_name, service, req)
            logger.debug(
                f"Successfully fetched files from bucket.",
                number_of_files=len(response_object_metadata),
            )
            items = response_object_metadata
            files = self.get_files(self._name, bucket_name, items)
            files_to_ingest = self.get_list_of_files_to_be_ingested(files)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self._parameters.number_of_threads
            ) as executor:
                futures = {
                    executor.submit(self.ingest_file, app, client, bucket, file): file
                    for file in files_to_ingest
                }
                for future in concurrent.futures.as_completed(futures):
                    file = futures[future]
                    if future.exception() is not None:
                        logger.error(
                            f"An error occurred while ingesting the file.",
                            file=file.get("filename"),
                            error=future.exception(),
                        )
        logger.info(
            f"Successfully completed ingesting objects for bucket.",
            bucket_name=bucket_name,
        )

    def process_bucket_metadata(self, service, bucket_name):
        """
        Processes and ingests metadata of a specified bucket

        Args:
            service (object): GCP Storage service object
            bucket_name (str): Name of the bucket for which metadata is to be processed and ingested
        """
        logger.info(f"Started ingesting metadata for bucket.", bucket_name=bucket_name)
        request = service.buckets().get(bucket=bucket_name)
        response_bucket_metadata = request.execute()
        logger.info(
            f"Successfully obtained metadata for bucket.",
            bucket_name=bucket_name,
            bucket_metadata=response_bucket_metadata,
        )
        (
            ingest_bucket_metadata_flag,
            metadata_checkpoint,
        ) = self.get_ingest_bucket_metadata_flag(
            self._name,
            bucket_name,
            response_bucket_metadata,
        )
        self.ingest_bucket_metadata(
            bucket_name,
            ingest_bucket_metadata_flag,
            response_bucket_metadata,
            metadata_checkpoint,
        )
        logger.info(
            f"Successfully completed ingesting metadata for bucket.",
            bucket_name=bucket_name,
        )

    def process_buckets(self, app, service, client):
        """
        Collects data from all the comma seperated buckets that have been specified during
        input configuration

        Args:
            app (object): App object.Its construction will be done in splunksdc's collector.py
            service (object): GCP Storage service object
            client (object): GCP Storage client object
        """
        buckets_list = self._parameters.bucket_name.split(",")
        for bucket_name in buckets_list:
            self.process_bucket_objects(app, service, client, bucket_name)
            self.process_bucket_metadata(service, bucket_name)

    @LogWith(datainput=name, start_time=start_time)
    @LogExceptions(
        logger, "Data input was interrupted by an unhandled exception.", lambda e: -1
    )
    def run(self, app, config):
        """
        For each Cloud Storage Bucket input a seperate process would be spawned.
        The input operates in multi instance mode. The input will

        Args:
            app (object): App object.Its construction will be done in splunksdc's collector.py
            config (object): Configuration object.Its construction will be done in splunksdc's collector.py

        Returns:
            int: Exit code
        """
        self._settings = Settings.load(config)
        self._settings.setup_log_level()
        management_url = (
            f"https://{app._context._server_host}:{app._context._server_port}"
        )
        self._kv_client = KVClient(
            splunkd_host=management_url, session_key=app._context._token
        )
        service, client = self.get_service_object(config, self._parameters.profile)
        self._event_writer = app.create_event_writer(index=self._parameters.index)
        self.main_context = logging.ThreadLocalLoggingStack.top()
        self.process_buckets(app, service, client)
        return 0
