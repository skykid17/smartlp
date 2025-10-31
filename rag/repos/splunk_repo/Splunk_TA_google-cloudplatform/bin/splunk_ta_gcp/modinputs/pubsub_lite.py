#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test
import json
import time
import traceback
from solnlib.modular_input import event_writer
import sys
import signal
import os
import splunk_ta_gcp.legacy.resource_manager as grm
from google.cloud.pubsublite.types import FlowControlSettings
from concurrent import futures
from google.cloud.pubsublite.cloudpubsub import SubscriberClient
from google.pubsub_v1 import PubsubMessage
import concurrent
import threading

IDLE_CONN_TIMEOUT = 600


class GoogleCloudPubSubLite(object):
    """
    The class responsible for fetching Pub/Sub Lite Subscriptions' messages and its ingestion.

    """

    def __init__(self, logger, session_key, config):
        """
        Args:
            logger (Any): Logger object for logging in file.
            session_key (Any): Session key for the particular modular input.
            config (Any): this contains the global setting stanza , proxy setting
        """
        self.logger = logger
        self.session_key = session_key
        self.config = config
        self.source = None
        self.collected_events = 0
        self.streaming_pull_future = None
        self.is_pull_messages = True
        self.ew = event_writer.ClassicEventWriter()
        self.timeout_event = threading.Event()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        # for windows machine
        if os.name == "nt":
            signal.signal(signal.SIGBREAK, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """
        Handle sigterm gracefully
        """
        if self.streaming_pull_future:
            self.streaming_pull_future.cancel()
        self.is_pull_messages = False
        self.logger.info("Received SIGTERM, modular input is exiting gracefully")
        sys.exit(0)

    def get_pubsub_lite_subscriptions(self, input_items):
        """
        Retrieves Pub/Sub Lite subscriptions for the given project, region or zone.

        Args:
            input_items (list): A list of input items to retrieve Pub/Sub Lite subscriptions for.

        Returns:
            list: A list of Pub/Sub Lite subscriptions associated with the input items.
        """
        project_number = None

        project_id = input_items.get("google_project")
        location_type = input_items.get("location")
        pubsublite_region = input_items.get("pubsublite_regions")
        pubsublite_zone = input_items.get("pubsublite_zones")
        subscription = input_items.get("pubsublite_subscriptions")

        res_mgr = grm.GoogleResourceManager(self.logger, self.config)

        # get the project number from project name
        project_number = res_mgr.get_project_number(project_id)

        # if there is not project number then we'll not able to make path hence return
        if not project_number:
            return project_number

        if location_type == "regional":
            location = pubsublite_region
        else:
            location = pubsublite_zone

        return f"projects/{project_number}/locations/{location}/subscriptions/{subscription}"

    def get_flow_control_settings(self, messages_outstanding, bytes_outstanding):
        """
        Retrieves the flow control settings for the Pub/Sub Lite subscriptions.

        Returns:
            dict: A dictionary containing the flow control settings for the Pub/Sub Lite subscriptions.
                The dictionary includes the following keys:
                - 'messages_outstanding': The maximum number of outstanding messages allowed per partition.
                - 'bytes_outstanding': The maximum size of outstanding messages allowed per partition in bytes.
        """
        # Configure when to pause the message stream for more incoming messages based on the
        # maximum size or number of messages that a single-partition subscriber has received,
        # whichever condition is met first.

        return FlowControlSettings(
            # outstanding messages. Must be >0.
            messages_outstanding=messages_outstanding,
            # Must be greater than the allowed size of the largest message (1 MiB).
            bytes_outstanding=bytes_outstanding * 1024 * 1024,
        )

    def index_pubsub_lite_data(self, message_data):
        """
        Indexes the Pub/Sub Lite messages.

        Args:
            input_items (dict): Input Payload.
        """
        try:
            event = self.ew.create_event(
                data=message_data,
                index=self.index,
                sourcetype=self.sourcetype,
                source=self.source,
            )

            self.ew.write_events([event])

            self.collected_events += 1

            if self.collected_events == 10000:
                self.logger.info(
                    "Successfully ingested {0} events and continuing".format(
                        self.collected_events
                    )
                )
                self.collected_events = 0

        except Exception as ex:
            self.logger.error("Error occurred while indexing the data: {0}".format(ex))
            raise ex

    def collect_pubsub_lite_messages(self, message: PubsubMessage):
        """
        Callback method that collect incoming Pub/Sub messages.

        Args:
            message (PubsubMessage): The received PubsubMessage object.

        Returns:
            None

        Raises:
            Any custom exceptions that may occur during the processing of the message.
        """
        try:
            # set the timeout_event when message received so it reset the idle connection timeout
            self.timeout_event.set()

            message_data = message.data.decode("utf-8")

            self.logger.debug(
                "Received message with messageID: {}".format(message.message_id)
            )

            # index the data
            self.index_pubsub_lite_data(message_data)

            # Acknowledge the message so that the same message won't appear in the subscription while fetching the messages
            message.ack()

            self.logger.debug(
                "Message successfully written and acknowledged with messageID: {}".format(
                    message.message_id
                )
            )

        except Exception as ex:
            self.logger.error("Error occurred from callback method: {0}".format(ex))

    def make_default_thread_pool_executor(self, thread_count):
        """
        Create a default ThreadPoolExecutor with the specified number of threads.

        Args:
            thread_count (int): The number of threads to create in the ThreadPoolExecutor.

        Returns:
            ThreadPoolExecutor: A ThreadPoolExecutor instance with the specified number of threads.
        """
        # Python 2.7 and 3.6+ have the thread_name_prefix argument, which is useful
        # for debugging.
        executor_kwargs = {}
        if sys.version_info[:2] >= (3, 6):
            executor_kwargs["thread_name_prefix"] = "CallbackThread"
        return concurrent.futures.ThreadPoolExecutor(
            max_workers=thread_count, **executor_kwargs
        )

    def terminate_on_idle_timeout(self, timeout):
        """Sends the SIGTERM if no messages are received until the idle connection timeout."""
        while self.timeout_event.wait(timeout):
            self.timeout_event.clear()

        self.logger.info("Idle timeout reached, restarting the input")
        os.kill(os.getpid(), signal.SIGTERM)

    def get_pubsub_lite_data(self, input_items, credentials):
        """
        Retrieves data from Pub/Sub Lite using the specified source and credentials.

        Args:
            input_items: The input items to process.
            source: field which will be use in the indexing the data.
            credentials: The credentials to use for authentication.
        """

        try:
            self.index = input_items.get("index")
            self.sourcetype = input_items.get("sourcetype")

            self.logger.info("Started retrieving the Pub/Sub lite subscription")

            # Get the subscription list
            subscription = self.get_pubsub_lite_subscriptions(input_items)
            self.source = subscription

            if not subscription:
                self.logger.info("No subscription has retrieved")
                return

            self.logger.info("Retrieved the Pub/Sub Lite subscription")

            messages_outstanding = int(input_items.get("messages_outstanding"))
            bytes_outstanding = int(input_items.get("bytes_outstanding"))

            # Set the flow control setting
            per_partition_flow_control_settings = self.get_flow_control_settings(
                messages_outstanding, bytes_outstanding
            )

            self.logger.info("Set the flow control setting")
            self.logger.debug(
                "Flow control setting: {0}".format(per_partition_flow_control_settings)
            )

            thread_count = int(input_items.get("number_of_threads"))

            executor = self.make_default_thread_pool_executor(thread_count)

            # If there is no message till idle timeout then restart the input
            thread_timeout = threading.Thread(
                target=self.terminate_on_idle_timeout, args=(IDLE_CONN_TIMEOUT,)
            )
            thread_timeout.daemon = True
            thread_timeout.start()

            # SubscriberClient() must be used in a `with` block or have __enter__() called before use.
            with SubscriberClient(
                credentials=credentials, executor=executor
            ) as subscriber_client:

                actual_workers = executor._max_workers
                self.logger.info(
                    "Actual number of worker threads: {0}".format(actual_workers)
                )

                while self.is_pull_messages:
                    self.streaming_pull_future = subscriber_client.subscribe(
                        subscription,
                        callback=self.collect_pubsub_lite_messages,
                        per_partition_flow_control_settings=per_partition_flow_control_settings,
                    )

                    self.logger.info(
                        "Listening for messages on {0}".format(str(subscription))
                    )

                    try:
                        self.streaming_pull_future.result()
                    except concurrent.futures.TimeoutError:
                        self.logger.error("TimeoutError: Operation timed out")
                    except Exception:
                        self.logger.error(
                            "Error occurred while listening the messages: {0}".format(
                                traceback.format_exc()
                            )
                        )
                    finally:
                        self.streaming_pull_future.cancel()
                        self.is_pull_messages = False
                        break

        except Exception as e:
            raise e
