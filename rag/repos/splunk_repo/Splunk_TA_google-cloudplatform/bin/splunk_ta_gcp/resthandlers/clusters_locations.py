#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import logging

import googleapiclient.discovery
import splunk.admin as admin
import splunk.clilib.cli_common as scc
import splunk_ta_gcp.legacy.config as gconf
import splunk_ta_gcp.legacy.consts as ggc
import splunktalib.common.pattern as scp
from splunk_ta_gcp.legacy.common import create_google_client
from splunktalib.common import util

logger = logging.getLogger()

util.remove_http_proxy_env_vars()


class GoogleKubernetesLocations(admin.MConfigHandler):
    valid_params = [ggc.google_credentials_name, ggc.google_project]

    def setup(self):
        for param in self.valid_params:
            self.supportedArgs.addOptArg(param)

    @scp.catch_all(logger)
    def handleList(self, conf_info):
        logger.info("start listing google locations")
        for required in self.valid_params:
            if not self.callerArgs or not self.callerArgs.get(required):
                logger.error('Missing "%s"', required)
                raise Exception('Missing "{}"'.format(required))

        stanza_name = self.callerArgs[ggc.google_credentials_name][0]
        config = gconf.get_google_settings(
            scc.getMgmtUri(), self.getSessionKey(), cred_name=stanza_name
        )

        project = self.callerArgs[ggc.google_project][0]
        config[ggc.google_project] = project
        config.update(
            {
                "service_name": "compute",
                "version": "v1",
                "scopes": ["https://www.googleapis.com/auth/compute"],
            }
        )
        compute = create_google_client(config)

        regions = compute.regions()
        location_names = list()
        request = regions.list(project=project)
        while request:
            response = request.execute()
            region_names = []
            for item in response.get("items", []):
                region_name = item.get("name", "")
                region_names.append(region_name)
                zones = item.get("zones", [])
                zone_names = list()
                for zone in zones:
                    result = zone.split("/")[-1]
                    zone_names.append(result)
                location_names.extend(zone_names)
            location_names.extend(region_names)
            request = regions.list_next(
                previous_request=request, previous_response=response
            )

        for location_name in location_names:
            conf_info[location_name].append("locations", location_name)
        logger.info("end of listing google locations")


def main():
    admin.init(GoogleKubernetesLocations, admin.CONTEXT_NONE)
