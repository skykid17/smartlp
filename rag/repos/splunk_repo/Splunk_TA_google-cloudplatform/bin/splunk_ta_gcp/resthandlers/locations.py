#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import logging
import splunk.admin as admin
import splunk.clilib.cli_common as scc
import splunk_ta_gcp.legacy.config as gconf
import splunk_ta_gcp.legacy.consts as ggc
import splunktalib.common.pattern as scp
from splunktalib.common import util
from splunk_ta_gcp.legacy.common import get_http_auth_cred, process_vpc_access_request

VPC_ACCESS_URL = "https://vpcaccess.googleapis.com/v1/projects/{}/locations"

logger = logging.getLogger()

util.remove_http_proxy_env_vars()


class GoogleLocations(admin.MConfigHandler):
    valid_params = [ggc.google_credentials_name, ggc.google_project]

    def setup(self):
        for param in self.valid_params:
            self.supportedArgs.addOptArg(param)

    @scp.catch_all(logger)
    def handleList(self, conf_info):
        logger.info("start listing google subscriptions")
        for required in self.valid_params:
            if not self.callerArgs or not self.callerArgs.get(required):
                logger.error('Missing "%s"', required)
                raise Exception('Missing "{}"'.format(required))

        stanza_name = self.callerArgs[ggc.google_credentials_name][0]
        project = self.callerArgs[ggc.google_project][0]
        config = gconf.get_google_settings(
            scc.getMgmtUri(), self.getSessionKey(), cred_name=stanza_name
        )
        config.update(
            {
                "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
            }
        )

        auth_http = get_http_auth_cred(config)
        url = VPC_ACCESS_URL.format(project)
        location_names = list()
        result = process_vpc_access_request(auth_http, url, "locations")
        locations = [item["locationId"] for item in result]
        location_names.extend(locations)
        for location_name in location_names:
            conf_info[location_name].append("locations", location_name)


def main():
    admin.init(GoogleLocations, admin.CONTEXT_NONE)
