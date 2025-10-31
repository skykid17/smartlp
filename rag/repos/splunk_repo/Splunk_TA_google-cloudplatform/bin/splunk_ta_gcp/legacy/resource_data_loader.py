#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import time
import traceback
import splunksdc.log as logging
import splunk_ta_gcp.legacy.resource_consts as grc
from splunk_ta_gcp.legacy.common import create_google_client, get_host_name
import json

logger = logging.get_module_logger()


class ResourceDataLoader(object):
    def __init__(self, task_config, service):
        """
        :task_config: dict object
        {
            "polling_interval": 30,
            "google_api": "ec2_instances" etc,
            "google_zone": "us_east_A" etc,
            "source": xxx,
            "sourcetype": yyy,
            "index": zzz,
        }
        :service: string object
            compute, bucket
        """
        self._task_config = task_config
        self._supported_desc_apis = grc.resource_endpoints.get(service)
        self._api = self._supported_desc_apis.get(self._task_config[grc.api], None)
        self._zone = self._task_config.get(grc.zone, None)
        self._project = self._task_config["google_project"]
        self._event_writer = self._task_config["classic_event_writer"]
        self._host = get_host_name()
        self._task_config["service_name"] = service
        self._task_config["version"] = "v1"
        self._task_config["scopes"] = grc.resource_metadata_supported_scopes.get(
            service
        )
        self._service = (
            create_google_client(self._task_config)
            if service != "vpcaccess"
            else service
        )
        self._stopped = False

    def __call__(self):
        with logging.LogContext(datainput=self._task_config[grc.source]):
            self.index_data()

    def index_data(self):
        """
        Ingests Data to Splunk
        """
        if self._api is not None:
            logger.info(
                "Start collecting resource for api=%s, zone=%s", self._api, self._zone
            )
            try:
                self._do_index_data()
            except Exception:
                logger.exception("Failed to collect resource data for %s.", self._api)
            logger.info(
                "End of collecting resource for api=%s, zone=%s", self._api, self._zone
            )
        else:
            logger.warning(
                self._task_config[grc.api]
                + " seems to be invalid, skipping this input."
            )

    def _write_events(self, results):
        """
        Write events to the splunk.
        """
        task = self._task_config
        events = []
        for result in results:
            result["Project"] = (task["google_project"],)
            result["Credentials"] = task["name"]
            event = self._event_writer.create_event(
                data=json.dumps(result, ensure_ascii=False),
                index=task[grc.index],
                source=task[grc.source],
                host=self._host,
                sourcetype=task[grc.sourcetype],
                time=time.time(),
            )
            events.append(event)
        logger.info("Send data for indexing.", action="index", records=len(events))

        self._event_writer.write_events(events)

    def _do_index_data(self):
        pass

    def get_interval(self):
        """
        returns interval from config.
        """

        return self._task_config[grc.interval]

    def get_props(self):
        """
        returns config.
        """

        return self._task_config

    def stop(self):
        """
        Sets _stopped flag to True
        """
        self._stopped = True
        logger.info(f"Stopping {self._service} GoogleCloudResourceMetadataDataLoader")
