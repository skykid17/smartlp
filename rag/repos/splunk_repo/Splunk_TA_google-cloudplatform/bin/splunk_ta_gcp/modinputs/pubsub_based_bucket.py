#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from future import standard_library

standard_library.install_aliases()
import json
import platform
import threading
import time
import uuid
import pathlib
import io

from builtins import object

from splunk_ta_gcp.common.credentials import CredentialFactory
from splunk_ta_gcp.common.settings import Settings
from splunk_ta_gcp.common.csv_parser import CSVParser
import splunk_ta_gcp.legacy.common as tacommon
from splunksdc import logging
from splunksdc.collector import SimpleCollectorV1
from splunksdc.config import StanzaParser, StringField, IntegerField
from splunksdc.utils import LogExceptions, LogWith
from splunksdc.batch import BatchExecutor, BatchExecutorExit

from google import pubsub_v1 as g_pubsub_v1
from google.cloud import pubsub_v1
from google.cloud import storage

DEFAULT_CHUNK_SIZE = 1048576
DEFAULT_SPLIT_TOKEN = ","
DEFAULT_SOURCETYPE = "google:gcp:buckets:data"
ACK_DEADLINE_SECONDS = 600

# retry to fetch messages for 3 times and then exit
EXIT_ON_IDLE = 4

logger = logging.get_module_logger()


class Job:
    """Class for Job used by BatchExecutor to spawn threads."""

    def __init__(self, message):
        self._message = message
        self._job_id = uuid.uuid4()

    @property
    def message(self):
        """Returns message."""
        return self._message

    @property
    def brief(self):
        """Returns message brief."""
        return {
            "message_id": self._message.get_message_id(),
            "created": self._message.get_created(),
            "expires": self._message.get_expires(),
            "job_id": self._job_id,
        }


class Message:
    """Class for PubSub Message."""

    def __init__(self, received_message, created, ttl):
        """Initializes the Message object

        Args:
            received_message: PubsubMessage object
            created: time indicating when message was pulled from Pub/Sub
            ttl: message visibility heartbeat
        """
        self._message = received_message.message
        self._created = created
        self._expires = ttl + created
        self._is_done = False
        self._is_acknowledged = False
        self._ack_id = received_message.ack_id

    @property
    def brief(self):
        """Returns message brief."""
        return {
            "message_id": self.get_message_id(),
            "created": self._created,
            "expires": self._expires,
            "is_done": self._is_done,
            "is_acknowledged": self._is_acknowledged,
        }

    def get_message(self):
        """Returns message"""
        return self._message

    def get_message_id(self):
        """Returns message_id from message"""
        return self._message.message_id

    def get_ack_id(self):
        """Returns message acknowledgement id"""
        return self._ack_id

    def get_message_eventtype(self):
        """Returns message eventtype by extracting from message attributes"""
        event_type = ""
        if self._message.attributes.get("eventType"):
            event_type = self._message.attributes.get("eventType")
        return event_type

    def get_message_data(self):
        """Returns data from message"""
        data = ""
        if self._message.data:
            data = self._message.data
        return data

    def get_created(self):
        """Returns created"""
        return self._created

    def get_expires(self):
        """Returns created"""
        return self._expires

    def set_expires(self, expires):
        """Sets the expires of this object

        Args:
            expires: time to expire
        """
        self._expires = expires

    def is_expired(self):
        """Returns if message is expired or not"""
        return self._now() > self._expires

    def has_elapsed(self):
        """Checks whether message near to expire and require to extend the deadline"""
        elapse = self._now() + 100
        return elapse > self._expires

    def done(self):
        """Sets message processing is completed"""
        self._is_done = True

    def is_done(self):
        """Returns whether message processing is completed or not"""
        return self._is_done

    def acknowledge(self):
        """Sets message is acknowledged"""
        self._is_acknowledged = True

    def is_acknowledged(self):
        """Returns whether messages is acknowledged or not"""
        return self._is_acknowledged

    def skip_message(self):
        """Skip the message"""
        self._is_done = True
        self._is_acknowledged = True

    def _now(self):
        """Returns current time"""
        return time.time()


class StorageBucketAgent(object):
    """Agent class for the storage bucket Client operations"""

    def __init__(
        self, storage_client, sourcetypes, input_sourcetype, profile, google_project
    ):
        """Initialise agent object

        Args:
            storage_client: storage Client object
            sourcetypes: dict of sourcetypes
            input_sourcetype: sourcetype configured in the input
            profile: Configured Account name
            google_project: Configured project
        """
        self._storage_client = storage_client
        self._sourcetypes = sourcetypes
        self._input_sourcetype = input_sourcetype
        self._profile = profile
        self._google_project = google_project

    def get_object_details(self, record):
        """Get bucket object details for data ingestion

        Args:
            record: Dict containing bucket object details from pubsub message

        Returns:
            string: sourcetype for the bucket object events based on file type
            string: source for the bucket events
            string: file extension
        """
        bucket_name = record.get("bucket_name")
        object_name = record.get("object_name")

        source = "{}:{}:{}:{}".format(
            self._profile,
            self._google_project,
            bucket_name,
            object_name,
        )

        file_extension = self.file_extension(object_name)

        sourcetype = self._input_sourcetype
        if (
            self._sourcetypes.get("default") == DEFAULT_SOURCETYPE
            and file_extension in self._sourcetypes
        ):
            sourcetype = self._sourcetypes.get(file_extension)

        return sourcetype, source, file_extension

    def get_blob(self, bucket_name, object_name):
        """Get blob object from bucket

        Args:
            bucket_name: Bucket name
            object_name: file object name

        Returns:
            Blob: Blob object from the provided file name
        """
        bucket = self._storage_client.bucket(bucket_name)
        blob = bucket.get_blob(object_name)
        return blob

    def file_extension(self, object_name):
        """Get extension of the file

        Args:
            object_name: File name which is a path along with name in the pubsub message

        Returns:
            string: extension of the file
        """
        file_extension = pathlib.Path(object_name).suffix[1:]
        if not file_extension:
            logger.debug(f"{object_name} object does not have an extension.")
        return file_extension


class PubSubAgent(object):
    """Agent class for the PubSub SubscriberClient operations"""

    def __init__(
        self,
        pubsub_client,
        subscription,
        message_batch_size,
    ):
        """Initialise PubSubAgent class

        Args:
            pubsub_client: PubSub SubscriberClient
            subscription: Subscription path
            message_batch_size: Messafe batch size to pull messages
        """
        self._pubsub_client = pubsub_client
        self._subscription = subscription
        self._message_batch_size = message_batch_size
        self._ack_deadline = self._get_subscription_ack_deadline()

    def _get_subscription_ack_deadline(self):
        """Get message acknowledge deadline configured in the Cloud subscription

        Returns:
            int: acknowledge deadline
        """
        request = g_pubsub_v1.GetSubscriptionRequest(
            subscription=self._subscription,
        )
        response = self._pubsub_client.get_subscription(request=request)
        return response.ack_deadline_seconds

    def get_subscription_ack_deadline(self):
        "Returns acknowledge deadline"
        return self._ack_deadline

    def pull_messages(self):
        """Pull messages from the pubsub subscription

        Returns:
            list: List of Message objects
        """
        response = self._pubsub_client.pull(
            request={
                "subscription": self._subscription,
                "max_messages": self._message_batch_size,
            }
        )

        messages = []
        created = self._now()
        if len(response.received_messages) > 0:
            for received_message in response.received_messages:
                message = Message(received_message, created, self._ack_deadline)
                messages.append(message)

        return messages

    def renew_ack_deadline(self, ack_ids):
        """Renew message acknowledge deadline in the case
        deadline is near to expire

        Args:
            ack_ids: List of ack ids
        """
        try:
            self._pubsub_client.modify_ack_deadline(
                request={
                    "subscription": self._subscription,
                    "ack_ids": ack_ids,
                    "ack_deadline_seconds": ACK_DEADLINE_SECONDS,
                }
            )
        except Exception as exc:
            logger.error(f"Error while modifying the message ack deadline {exc}")

    def acknowledge(self, ack_ids):
        """Acknowledge pubsub messages

        Args:
            ack_ids: List of ack ids
        """
        try:
            self._pubsub_client.acknowledge(
                request={"subscription": self._subscription, "ack_ids": ack_ids}
            )
        except Exception as exc:
            logger.error(
                f"Error while acknowledging message {exc}. It may result in possible duplication."
            )

    def _now(self):
        """Returns current time."""
        return time.time()


class PubSubBasedBucketAdapter(object):
    """Adapter class which works as bridge between BatchExecutor, PubSubAgent, StorageAgent, EventWriter and other classes operations"""

    def __init__(
        self,
        app,
        config,
        pubsub_agent,
        storage_bucket_agent,
        event_writer,
    ):
        """Initialise adapter class

        Args:
            app: SimpleCollectorV1 object
            config: SimpleCollectorV1.ConfigManager object
            pubsub_agent: PubSubAgent object
            storage_bucket_agent: StorageBucketAgent object
            event_writer: XMLEventWriter object
        """
        self._app = app
        self._config = config
        self._pubsub_agent = pubsub_agent
        self._storage_bucket_agent = storage_bucket_agent
        self._event_writer = event_writer
        self._idle_count = 0
        self._now = time.time
        self._messages = []

        self._is_processing = False
        self.thread_lock = threading.Lock()

    def is_aborted(self):
        """Checks if app is aborted or not."""
        return self._app.is_aborted()

    def discover(self):
        """Method used by BatchExecutor to spawn Jobs

        Yields:
            Job: yields Job object which runs in child thread
        """
        while True:
            if self._is_processing:
                time.sleep(1)
                continue

            logger.info("Started fetching messages.")
            self._messages = self._pubsub_agent.pull_messages()
            logger.info(
                f"Pulled messages for processing. messages={len(self._messages)}"
            )

            if self._should_exit(self._messages):
                yield BatchExecutorExit(True)

            if self._messages:
                self._is_processing = True

                # Start another thread to extend message deadline and ack message
                t = threading.Thread(
                    target=self._manage_messages_renew_and_ack, daemon=True
                )
                t.start()

            yield [Job(message) for message in self._messages]

    def _manage_messages_renew_and_ack(self):
        """Method which runs in separate thread to renew and ack messages in the current message batch"""
        while self._is_processing and not self.is_aborted():
            ack_ids = []
            renew_ack_ids = []

            ack_messages = []
            renew_messages = []
            is_in_progress = False
            for message in self._messages:
                if not message.is_done():
                    is_in_progress = True
                    if message.has_elapsed():
                        # extend messages ack if <= 100 sec
                        renew_messages.append(message)
                        renew_ack_ids.append(message.get_ack_id())
                elif message.is_done() and not message.is_acknowledged():
                    # ack messages which are processed
                    ack_messages.append(message)
                    ack_ids.append(message.get_ack_id())
                    is_in_progress = True

            if not is_in_progress:
                self._is_processing = False
                if self._messages:
                    logger.info(f"All messages processed in the current batch.")
            else:
                if renew_ack_ids:
                    ttl = self._now() + ACK_DEADLINE_SECONDS
                    self._pubsub_agent.renew_ack_deadline(renew_ack_ids)
                    for renew_msg in renew_messages:
                        with self.thread_lock:
                            renew_msg.set_expires(ttl)
                    logger.debug(
                        f"Extended deadline for {len(renew_ack_ids)} messages."
                    )

                if ack_ids:
                    self._pubsub_agent.acknowledge(ack_ids)
                    for ack_msg in ack_messages:
                        ack_msg.acknowledge()
                    logger.debug(f"Acknowledged {len(ack_ids)} messages.")

                time.sleep(1.0)
        return 0

    def do(self, job, session):  # pylint: disable=invalid-name
        """Do method implementation used by BatchExecutor"""
        with logging.LogContext(**job.brief):
            self._process(job.message)

    def _process(self, message):  # pylint: disable=inconsistent-return-statements
        """Method to process pubsub message and ingest blob files

        Args:
            message: Message object
        """
        try:
            if message.is_expired():
                message.skip_message()
                return logger.warning(
                    f"Visibility timeout has expired. Message will be re-pulled at a later time. message_id={message.get_message_id()}"
                )

            try:
                record = self._parse(message)
            except Exception as ex:
                # Set the message as done so it gets acknowledged and doesn't appear in the future
                message.done()
                logger.warning(f"{str(ex)}")
                return logger.warning(
                    f"Acknowledged unrecognized message.",
                    message_id={message.get_message_id()},
                )

            (
                sourcetype,
                source,
                file_extension,
            ) = self._storage_bucket_agent.get_object_details(record)

            logger.debug(
                f"File details.",
                bucket=record.get("bucket_name"),
                file=record.get("object_name"),
                file_extension=file_extension,
                sourcetype=sourcetype,
                source=source,
            )
            blob = self._storage_bucket_agent.get_blob(
                record.get("bucket_name"), record.get("object_name")
            )
            if not blob:
                logger.warn(
                    f"Unable to find file.",
                    bucket={record.get("bucket_name")},
                    blob={record.get("object_name")},
                )
                message.skip_message()
                return
            self._ingest_file(
                blob,
                record.get("object_name"),
                sourcetype,
                source,
                file_extension,
            )
            logger.info(
                f"Events successfully ingested.", file=record.get("object_name")
            )
            if message.is_expired():
                logger.warning(
                    "File has been ingested beyond the visibility timeout. It may result in possible duplication.",
                    file=record.get("object_name"),
                )

            message.done()
        except Exception as exc:  # pylint: disable=broad-except
            # Skip the message in case of any error so that it reappears again after acknowledgement deadline.This ensures ingestion is not blocked for other messages.
            message.skip_message()
            logger.critical(
                "An error occurred while processing the message hence skipping it. Message will be re-pulled at a later time.",
                exc_info=True,
            )
            return exc

    def _parse(self, message):
        """Parses message

        Args:
            message: Message object

        Raises:
            ValueError: Error if eventtype is not 'OBJECT_FINALIZE'
            ValueError: Error if unable to parse the JSON data in the message
            ValueError: Error if invalid pubsub notification

        Returns:
            dict: Dict containing bucket file details from the message
        """
        # ignore messages whose eventType is not 'OBJECT_FINALIZE'
        event_type = message.get_message_eventtype()
        if not event_type or event_type.upper() != "OBJECT_FINALIZE":
            raise ValueError(
                f"Invalid message eventType. message_id={message.get_message_id()}, event_type={event_type}"
            )

        data = message.get_message_data()
        try:
            data = json.loads(data)
        except Exception as exe:
            raise ValueError(
                f"Failed to parse the payload. Invalid JSON string in the payload. message_id={message.get_message_id()}"
            )

        # check whether valid storage bucket notification or not
        bucket_name = data.get("bucket")
        object_name = data.get("name")
        if not bucket_name and not object_name:
            raise ValueError(
                f"Invalid storage bucket notification. message_id={message.get_message_id()}"
            )

        record = {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "self_link": data.get("selfLink"),
            "size": data.get("size"),
            "etag": data.get("etag"),
        }

        return record

    def _ingest_file(self, blob, file_name, sourcetype, source, file_extension):
        """Ingest file data

        Args:
            blob: Blob object for the file
            file_name: File object name
            sourcetype: Sourcetype for this file ingestion
            source: source of the file
            file_extension: file extension
        """
        csv_parser = None
        if file_extension == "csv":
            csv_parser = CSVParser(DEFAULT_SPLIT_TOKEN, logger)

        blob_size = blob.size
        end = -1

        is_download_completed = False
        while is_download_completed is False:
            # create a temp file object
            blob_contents = io.BytesIO()

            start = end + 1
            # if blob is smaller than chunk size, ingesting in one download
            # if its a large file, ingest in chunks
            end = (
                start + DEFAULT_CHUNK_SIZE
                if start + DEFAULT_CHUNK_SIZE < blob_size
                else blob_size
            )

            try:
                logger.debug(
                    f"Ingesting file {file_name} - chunk: start: {start}, end: {end}"
                )
                blob.download_to_file(blob_contents, start=start, end=end)

                if end >= blob_size:
                    logger.debug(f"This is the last chunk for {file_name}")
                    is_download_completed = True
            except Exception as e:
                logger.error(f"Exception {e}")
                is_download_completed = True

            metadata = {
                "source": source,
                "sourcetype": sourcetype,
            }

            blob_contents.seek(0)
            volume = 0
            if file_extension == "csv":
                # events = []
                for event in csv_parser.parse_csv_line(blob_contents):
                    volume += self._event_writer.write_events(
                        [json.dumps(event)], **metadata
                    )
            else:
                b_content = blob_contents.read().decode("utf-8")
                volume += self._write_fileobj(
                    b_content, is_download_completed, **metadata
                )

            logger.debug("Sent data for indexing.", size=volume, file=file_name)

    def _write_fileobj(self, file_chunk, completed=False, **kwargs):
        """Method to write file objects when downloading the file in chunks

        Args:
            file_chunk: Downloaded file chunk
            completed: Whether complete file downloaded or not

        Returns:
            int: volume of data ingested
        """
        volume = 0
        metadata = self._event_writer._compose_event_metadata(kwargs)
        for chunk in self._event_writer._read_multiple_lines(file_chunk):
            volume += len(chunk)
            data = self._event_writer._render_element("data", chunk)
            data = self._event_writer._CHUNK_TEMPLATE.format(
                data=data, done="", **metadata
            )
            self._event_writer._write(data)

        if completed:
            eos = self._event_writer._CHUNK_TEMPLATE.format(
                data="", done="<done/>", **metadata
            )
            self._event_writer._write(eos)
        return volume

    def _should_exit(self, messages):
        """Check whether exit the input after 3 retries when no new messages to process

        Args:
            messages: Pulled messages

        Returns:
            bool: Should continue or exit
        """
        if not messages:
            # sleep for 1, 4 & 9 seconds between respective retry
            sleep_sec = (self._idle_count + 1) ** 2
            self._idle_count += 1
            if self._idle_count >= EXIT_ON_IDLE:
                return True
            time.sleep(sleep_sec)
            return False
        self._idle_count = 0
        return False

    def allocate(self):
        """Implementation required by BatchExecutor"""
        pass

    def done(self, job, result):
        """Implementation required by BatchExecutor"""
        pass


class PubSubBasedBucketInput(object):
    """Class to provide configuration to start data collection"""

    def __init__(self, stanza):
        """Class initialization

        Args:
            stanza: provides input stanza details
        """
        self._kind = stanza.kind
        self._name = stanza.name
        self._args = stanza.content
        self._start_time = int(time.time())
        self._google_project = None

    @property
    def name(self):
        """name property

        Returns:
            name: returns name of the input
        """
        return self._name

    @property
    def start_time(self):
        """start_time property

        Returns:
            time: returns time
        """
        return self._start_time

    @property
    def project_name(self):
        """project_name property

        Returns:
            name: returns name of the project
        """
        return self._google_project

    def _extract_arguments(self, parser):
        """Parses args based on the details provided in the parser

        Args:
            parser: StanzaParser object with list of fields to parse

        Returns:
            Arguments: returns object of Arguments with extracted fields
        """
        return parser.parse(self._args)

    def _extract_params(self):
        """Extract common fields for the input"""
        parser = StanzaParser(
            [
                StringField("google_credentials_name", rename="profile"),
                StringField("google_project", required=True),
                StringField("google_subscriptions", required=True),
                StringField("sourcetype", default=DEFAULT_SOURCETYPE),
            ]
        )
        params = self._extract_arguments(parser)
        return params

    def _create_event_writer(self, app):
        """Method to create event_writer

        Args:
            app: app object

        Returns:
            XMLEventWriter: returns event_wrtier object
        """
        stanza = self._kind + "://" + self._name
        parser = StanzaParser(
            [
                StringField("index"),
                StringField("host"),
                StringField("stanza", fillempty=stanza),
                StringField("sourcetype", default=DEFAULT_SOURCETYPE),
            ]
        )
        metadata = self._extract_arguments(parser)
        try:
            if metadata.host == "$decideOnStartup":
                metadata.host = platform.node()
        except:
            logger.warning("Error while getting platform")
        return app.create_event_writer(None, **vars(metadata))

    def _create_subscription(self, project, subscriptions):
        """Creates Subscription Path from the project and subscription

        Args:
            project: project from the input configuration
            subscriptions: subscription from the input configuration

        Returns:
            string: formatted subscription path
        """
        subscription = f"projects/{project}/subscriptions/{subscriptions}"
        return subscription

    def _create_pubsub_client(self, credentials):
        """Create PubSub Subscriber Client

        Args:
            credentials: google Credentials object

        Returns:
            SubscriberClient: object of pubsub subscriber client
        """
        pubsub_client = pubsub_v1.SubscriberClient(credentials=credentials)
        return pubsub_client

    def _create_pubsub_agent(self, pubsub_client, subscription):
        """Creates object of PubSubAgent

        Args:
            pubsub_client: object of SubscriberClient
            subscription: subscription path created from project and subscription

        Returns:
            PubSubAgent: object of PubSubAgent
        """
        parser = StanzaParser(
            [
                IntegerField("message_batch_size", default=10, lower=1),
            ]
        )
        args = self._extract_arguments(parser)
        agent = PubSubAgent(
            pubsub_client,
            subscription,
            args.message_batch_size,
        )
        return agent

    def _create_storage_client(self, credentials):
        """Method to create storage Client

        Args:
            credentials: google Credentials object

        Returns:
            Client: object of storage.Client
        """
        storage_client = storage.Client(
            credentials=credentials, project=self.project_name
        )
        return storage_client

    def _create_storage_bucket_agent(
        self, storage_client, sourcetype, sourcetypes, profile, google_project
    ):
        """_summary_

        Args:
            storage_client: object of storage.Client
            sourcetypes: Dict of sourcetypes
            profile: Name of configured Account
            google_project: Project selected in the Input configuration

        Returns:
            StorageBucketAgent: object of StorageBucketAgent
        """
        agent = StorageBucketAgent(
            storage_client, sourcetypes, sourcetype, profile, google_project
        )
        return agent

    def _create_credentials(self, config, profile):
        """Create google Credentials object from the provided Account configuration

        Args:
            config: SimpleCollectorV1.ConfigManager object
            profile: Name of configured Account

        Returns:
            Credentials: object of Credentials
        """
        scopes = [
            "https://www.googleapis.com/auth/pubsub",
            "https://www.googleapis.com/auth/cloud-platform.read-only",
        ]
        factory = CredentialFactory(config)
        return factory.load(profile, scopes)

    def _setup_sourcetypes(self, sourcetype):
        """Create Dict of sourcetypes based on the filetypes

        Args:
            sourcetype: default sourcetype provided in the Input configuration

        Returns:
            dict: Dict of sourcetypes
        """
        sourcetypes = {
            "csv": "google:gcp:buckets:csvdata",
            "xml": "google:gcp:buckets:xmldata",
            "json": "google:gcp:buckets:jsondata",
            "default": sourcetype,
        }
        return sourcetypes

    def _create_batch_executor(self):
        """Method to create batch executor from number of threads

        Returns:
            BatchExecutor: BatchExecutor object by providing number of threads
        """
        parser = StanzaParser(
            [
                IntegerField(
                    "number_of_threads",
                    default=10,
                    lower=1,
                    upper=10,
                ),
            ]
        )
        args = self._extract_arguments(parser)
        return BatchExecutor(number_of_threads=args.number_of_threads)

    @LogWith(datainput=name, start_time=start_time)
    @LogExceptions(
        logger, "Data input was interrupted by an unhandled exception.", lambda e: -1
    )
    def run(self, app, config):
        """Method to create configuration objects and start data collection

        Args:
            app: SimpleCollectorV1 object
            config: SimpleCollectorV1.ConfigManager object

        Returns:
            false: returns 0 to exit data collection
        """
        settings = Settings.load(config)
        settings.setup_log_level()

        params = self._extract_params()
        self._google_project = params.google_project

        event_writer = self._create_event_writer(app)

        sourcetype = params.sourcetype
        sourcetypes = self._setup_sourcetypes(sourcetype)

        credentials = self._create_credentials(config, params.profile)

        # Setup proxy env variables for SDKs for this process
        proxy_uri = settings.make_proxy_uri()
        tacommon.setup_env_proxy(None, logger, proxy_uri)

        subscription = self._create_subscription(
            params.google_project, params.google_subscriptions
        )
        pubsub_client = self._create_pubsub_client(credentials)
        pubsub_agent = self._create_pubsub_agent(
            pubsub_client,
            subscription,
        )

        storage_client = self._create_storage_client(credentials)
        storage_bucket_agent = self._create_storage_bucket_agent(
            storage_client,
            sourcetype,
            sourcetypes,
            params.profile,
            params.google_project,
        )

        executor = self._create_batch_executor()
        adapter = PubSubBasedBucketAdapter(
            app, config, pubsub_agent, storage_bucket_agent, event_writer
        )
        executor.run(adapter)

        return 0


def modular_input_run(app, config):
    """Executed by SimpleCollectorV1 and entry point of data collection

    Args:
        app: SimpleCollectorV1 object
        config: SimpleCollectorV1.ConfigManager object

    Returns:
        callback method: returns call method which will be executed
    """
    inputs = app.inputs()
    datainput = PubSubBasedBucketInput(inputs[0])
    return datainput.run(app, config)


def main():
    """main Function called from input initiation"""
    arguments = {
        "google_credentials_name": {"title": "The name of Google service account"},
        "google_project": {"title": "The Google project ID"},
        "google_subscriptions": {"title": "List of subscriptions' names"},
    }
    SimpleCollectorV1.main(
        modular_input_run,
        title="Google Cloud Pub/Sub Based Bucket",
        use_single_instance=False,
        arguments=arguments,
    )
