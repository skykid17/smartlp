##
## SPDX-FileCopyrightText: 2024 Splunk, Inc.
## SPDX-License-Identifier: LicenseRef-Splunk-8-2021
##
##
import import_declare_test  # isort: skip # noqa: F401

import os
import sys
import json
import jira_cloud_issue_helper
import traceback


class AlertActionWorkerJira_Cloud_Issue_alert:
    def __init__(self):
        try:
            if len(sys.argv) > 1 and sys.argv[1] == "--execute":
                self.payload = json.loads(sys.stdin.read())
                jira_cloud_issue_helper.JiraCloudIssueHelper(
                    self.payload
                ).jira_cloud_alert_action()
        except Exception:
            return traceback.format_exc()


if __name__ == "__main__":
    AlertActionWorkerJira_Cloud_Issue_alert()
