#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import logging
import traceback
from builtins import object
from google.cloud.pubsublite import AdminClient
from google.cloud.pubsublite.types import LocationPath
import splunk_ta_gcp.legacy.resource_manager as grm

from splunktaucclib.rest_handler.error import RestError
import grpc

import splunk.admin as admin
import splunk.clilib.cli_common as scc
import splunk_ta_gcp.legacy.common as gwc
from splunk_ta_gcp.common.credentials import CredentialFactory
import splunk_ta_gcp.legacy.config as gconf
import splunk_ta_gcp.legacy.consts as ggc


class GooglePubSubLite(object):
    def __init__(self, logger, config):
        """
        :param: config
        """

        self._logger = logger
        self._config = config

    def get_subscriptions(self):
        """
        return a list of pubsub lite subscriptions
        [
            name: "projects/<project_id>/locations/<region_or_zone>/subscriptions/<name_of_subscription>"
            topic: "projects/<project_id>/locations/<region_or_zone>/topics/<name_of_topic>"
            delivery_config {
                delivery_requirement: <deliver_mode>
            }
        ]
        """

        pubsublite_zone = None
        pubsublite_region = None
        result = []

        project_name = self._config["google_project"]
        location_type = self._config["location"]

        res_mgr = grm.GoogleResourceManager(self._logger, self._config)

        # get the project number from project name
        project_number = res_mgr.get_project_number(project_name)

        if project_number:
            # If regional is selected then get the selected region, and if zonal is selected then get the selected zone
            if location_type == "regional":
                pubsublite_region = self._config["pubsublite_regions"]
                location = pubsublite_region
            else:
                pubsublite_zone = self._config["pubsublite_zones"]
                location = pubsublite_zone
                pubsublite_region = location.rsplit("-", 1)[0]

            # create the location path i.e. projects/<project_id>/locations/<region_or_zone>
            location_path = LocationPath(project_number, location)

            # get credential
            credential = CredentialFactory.get_credential(self._config)

            gwc.setup_env_proxy(self._config, self._logger)

            client = AdminClient(pubsublite_region, credentials=credential)

            try:
                result = client.list_subscriptions(location_path)
            except Exception:
                self._logger.error(
                    "Failed to list PubSub Lite Subscriptions for project=%s, error=%s",
                    project_name,
                    traceback.format_exc(),
                )
                raise RestError(
                    grpc.StatusCode.UNKNOWN,
                    "This location is not supported for PubSub Lite.",
                )

        return result


class GooglePubSubSubscriptions(admin.MConfigHandler):
    valid_params = [
        ggc.google_credentials_name,
        ggc.google_project,
        ggc.location,
        ggc.pubsublite_regions,
        ggc.pubsublite_zones,
    ]

    def setup(self):
        for param in self.valid_params:
            self.supportedArgs.addOptArg(param)

    def handleList(self, conf_info):
        pubsublite_zone = None
        pubsublite_region = None
        location_type = None

        # Get the credential
        if self.callerArgs.get(ggc.google_credentials_name) is not None:
            stanza_name = self.callerArgs[ggc.google_credentials_name][0]
        else:
            return

        config = gconf.get_google_settings(
            scc.getMgmtUri(), self.getSessionKey(), cred_name=stanza_name
        )

        log_file_name = "splunk_ta_google_cloudplatform_rh_inputs_pubsub_lite"

        # Set the logger
        logger = gwc.set_logger(scc.getMgmtUri(), self.getSessionKey(), log_file_name)

        # Get the google project
        if self.callerArgs.get(ggc.google_project) is not None:
            config[ggc.google_project] = self.callerArgs[ggc.google_project][0]
        else:
            return

        # Get the value of location toggle button
        if self.callerArgs.get(ggc.location) is not None:
            location_type = self.callerArgs[ggc.location][0]
            config[ggc.location] = location_type
        else:
            return

        if location_type == "regional":
            # Get the PubSub Region
            if self.callerArgs.get(ggc.pubsublite_regions):
                if self.callerArgs[ggc.pubsublite_regions] and self.callerArgs.get(
                    ggc.pubsublite_regions
                ) != [None]:
                    pubsublite_region = self.callerArgs[ggc.pubsublite_regions][0]

            if pubsublite_region:
                config[ggc.pubsublite_regions] = pubsublite_region
            else:
                return

        else:
            # Get the PubSub Zone
            if self.callerArgs.get(ggc.pubsublite_zones):
                if self.callerArgs[ggc.pubsublite_zones] and self.callerArgs.get(
                    ggc.pubsublite_zones
                ) != [None]:
                    pubsublite_zone = self.callerArgs[ggc.pubsublite_zones][0]

            if pubsublite_zone:
                config[ggc.pubsublite_zones] = pubsublite_zone
            else:
                return

        pubsublite = GooglePubSubLite(logger, config)

        # Get the pub sub lite subscriptions
        subscriptions = [
            sub.name.split("/")[-1] for sub in pubsublite.get_subscriptions()
        ]

        for subscription in subscriptions:
            conf_info[subscription].append("pubsublite_subscriptions", subscription)


def main():
    admin.init(GooglePubSubSubscriptions, admin.CONTEXT_NONE)
