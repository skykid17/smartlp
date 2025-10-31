#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import googleapiclient
import splunk.admin as admin
import splunk.clilib.cli_common as scc
import splunk_ta_gcp.legacy.config as gconf
import splunk_ta_gcp.legacy.consts as ggc
import splunk_ta_gcp.modinputs.cloud_monitor.wrapper as gmw
import splunk_ta_gcp.modinputs.cloud_monitor.consts as gmc
import splunk_ta_gcp.legacy.common as gwc
import traceback
from splunktalib.common import util


util.remove_http_proxy_env_vars()


class GoogleMonitorProjects(admin.MConfigHandler):
    valid_params = [ggc.google_credentials_name, ggc.google_project]

    def setup(self):
        for param in self.valid_params:
            self.supportedArgs.addOptArg(param)

    def handleList(self, conf_info):
        log_file_name = "splunk_ta_google_cloudplatform_rh_monitored_projects"
        # Setup the logger
        logger = gwc.set_logger(scc.getMgmtUri(), self.getSessionKey(), log_file_name)

        logger.info("Start of listing google monitored projects")
        if not self.callerArgs or not self.callerArgs.get(ggc.google_credentials_name):
            logger.error("Missing Google credentials")
            raise Exception("Missing Google credentials")

        stanza_name = self.callerArgs[ggc.google_credentials_name][0]
        project = self.callerArgs[ggc.google_project][0]
        logger.info(self.callerArgs[ggc.google_credentials_name])
        config = gconf.get_google_settings(
            scc.getMgmtUri(), self.getSessionKey(), cred_name=stanza_name
        )
        config["version"] = gmc.cm_api_ver_1
        gcp_mon = gmw.GoogleCloudMonitor(logger, config)
        try:
            projects = gcp_mon.monitored_projects(project)
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403:
                projects = [config[ggc.google_credentials]["project_id"]]
            else:
                logger.error(
                    f"An error occurred during listing google monitored projects {traceback.format_exc()}"
                )
                raise e
        except Exception as e:
            logger.error(
                f"An error occurred during listing google monitored projects {traceback.format_exc()}"
            )
            raise e
        conf_info["All"].append("monitored_projects", "All")
        for project in projects:
            conf_info[project].append("monitored_projects", project)
        logger.info("End of listing google monitored projects")


def main():
    admin.init(GoogleMonitorProjects, admin.CONTEXT_NONE)
