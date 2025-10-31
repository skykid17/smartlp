#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import traceback
from builtins import object

import splunk_ta_gcp.legacy.common as gwc
import splunk_ta_gcp.legacy.consts as ggc
from googleapiclient.errors import HttpError
from . import consts as gmc

MONITOR_SCOPES = [
    "https://www.googleapis.com/auth/monitoring",
    "https://www.googleapis.com/auth/cloud-platform",
]


def get_pagination_results(service, req, key):
    all_results = []
    if req is None:
        return all_results

    result = req.execute(num_retries=3)
    if result and result.get(key):
        all_results.extend(result[key])

    if "nextPageToken" in result:
        while 1:
            req = service.list_next(req, result)
            if not req:
                break

            result = req.execute(num_retries=3)
            if result and result.get(key):
                all_results.extend(result[key])
            else:
                break

    return all_results


class GoogleCloudMonitor:
    def __init__(self, logger, config):
        """
        :param: config
        {
            "proxy_url": xxx,
            "proxy_port": xxx,
            "proxy_username": xxx,
            "proxy_password": xxx,
            "proxy_rdns": xxx,
            "proxy_type": xxx,
            "google_credentials": xxx,
        }
        """

        self._config = config
        self._config["scopes"] = MONITOR_SCOPES
        self._config["service_name"] = "monitoring"
        if not self._config.get("version"):
            self._config["version"] = gmc.cm_api_ver_3
        self._logger = logger
        self._client = gwc.create_google_client(self._config)

    def monitored_projects(self, project_name):
        """
        This method used to get the list of monitored projects for scopeMetrics
        It should only be called when API version is - "v1"
        """
        projects = []
        try:
            resp = (
                self._client.locations()
                .global_()
                .metricsScopes()
                .get(name=f"locations/global/metricsScopes/{project_name}")
                .execute()
            )
            monitored_projects = resp.get("monitoredProjects", [])
            for project in monitored_projects:
                path = project.get("name")
                name = path.split("/")[-1]
                projects.append(name)
        except HttpError as ge:
            message = f"Error while fetching scope metrics for project={project_name}."
            if ge.status_code == 403:
                permission_error = "The caller does not have permission"
                if permission_error not in ge.error_details:
                    self._logger.error(f"{message} Reason: {ge.error_details}")
            else:
                self._logger.error(f"{message} Reason: {ge.error_details}")
                raise
        except Exception:
            self._logger.error(
                "Failed to list Google scope projects for " "project=%s, error=%s",
                project_name,
                traceback.format_exc(),
            )
            raise

        return projects

    def list_metrics(self, params):
        """
        :params: dict like object
        {
        "google_project": xxx,
        "google_metrics": xxx,
        "oldest": "2016-01-16T00:00:00-00:00",
        "youngest": "2016-02-16T00:00:00-00:00",
        ...
        }
        return:
        """

        project_name = params[ggc.google_project]
        metric = params[gmc.google_metrics]
        monitored_project = params[gmc.monitored_project]
        self._logger.info(
            "Collect data for project=%s, metric=%s, win=[%s, %s], mon_project=%s",
            project_name,
            metric,
            params[gmc.oldest],
            params[gmc.youngest],
            monitored_project,
        )

        _filter = (
            f'metric.type="{metric}" resource.label.project_id={monitored_project}'
        )
        try:
            resource = self._client.projects().timeSeries()
            request = resource.list(
                name="projects/" + project_name,
                filter=_filter,
                interval_startTime=params["oldest"],
                interval_endTime=params["youngest"],
            )
            return get_pagination_results(resource, request, "timeSeries")
        except Exception:
            self._logger.error(
                "Failed to list Google metric for project=%s, metric=%s, mon_project=%s "
                "error=%s",
                params["google_project"],
                params["google_metrics"],
                monitored_project,
                traceback.format_exc(),
            )
            raise

    def write_metrics(self, metrics):
        pass

    def metric_descriptors(self, project_name):
        """
        return a list of metric_descriptor
        {
        "name": "appengine.googleapis.com/http/server/dos_intercept_count",
        "project": "1002621264351",
        "labels": [
            {
                 "key": "appengine.googleapis.com/module"
            },
            {
                 "key": "appengine.googleapis.com/version"
            },
            {
                 "key": "cloud.googleapis.com/location"
            },
            {
                 "key": "cloud.googleapis.com/service"
            }
        ],
        "typeDescriptor": {
            "metricType": "delta",
            "valueType": "int64"
        },
        "description": "Delta count of ... to prevent DoS attacks.",
        }
        """

        try:
            resource = self._client.projects().metricDescriptors()
            request = resource.list(name="projects/" + project_name)
            return get_pagination_results(resource, request, "metricDescriptors")
        except HttpError as e:
            if e.resp.status == 403:
                self._logger.error(
                    "Daily limit exceeded. Try again later. " "project=%s, error=%s",
                    project_name,
                    traceback.format_exc(),
                )
                raise ValueError("Daily limit exceeded. Try again later.")
            raise
        except Exception:
            self._logger.error(
                "Failed to list Google metric descriptors for " "project=%s, error=%s",
                project_name,
                traceback.format_exc(),
            )
            raise
