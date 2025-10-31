#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import traceback
import splunk_ta_gcp.legacy.resource_consts as grc
import splunksdc.log as logging
from splunk_ta_gcp.legacy.resource_data_loader import ResourceDataLoader
from splunk_ta_gcp.legacy.common import create_google_client

BASE_URL = "projects/{}/locations"

logger = logging.get_module_logger()


class KubernetesResourceDataLoader(ResourceDataLoader):
    """
    Data Loader for Resource Metadata Kubernetes Input
    """

    def __init__(self, task_config):
        super(KubernetesResourceDataLoader, self).__init__(task_config, "container")
        self._location = task_config["location_name"]

    def _do_index_data(self):
        if self._api is None:
            logger.error(
                "Unsupported api.",
                api=self._task_config[grc.api],
                ErrorCode="ConfigurationError",
                ErrorDetail="Service is unsupported.",
                datainput=self._task_config[grc.source],
            )
            return
        results = self.fetch_results(self._api)
        self._write_events(results)

    def fetch_locations(self):
        """
        Fetch supported locations
        """
        location_names = list()
        # If no location is specified fetch all
        # supported locations
        if not self._location:
            compute_config = self._task_config
            compute_config["service_name"] = "compute"
            service = create_google_client(compute_config)
            regions = service.regions()
            request = regions.list(project=self._project)
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
        else:
            location_names.extend(self._location.split(","))
        return location_names

    def fetch_cluster_names(self, location):
        """
        Fetch clusters created under specified location
        Argument: "location"
        Type: String
        """
        cluster_names = list()
        parent = f"{BASE_URL.format(self._project)}/{location}"
        request = self._service.projects().locations().clusters().list(parent=parent)
        if request is not None:
            try:
                response = request.execute()
                if response.get("clusters"):
                    names = [item.get("name") for item in response.get("clusters", [])]
                    cluster_names.extend(names)
            except Exception:
                logger.error(traceback.format_exc())
        return cluster_names

    def process_clusters_request(self, parent):
        """
        Request processing for Kubernetes clusters API
        Argument: "parent"
        Type: String
        """
        result = list()
        request = self._service.projects().locations().clusters().list(parent=parent)
        if request is not None:
            try:
                response = request.execute()
                for cluster in response["clusters"]:
                    result.append(cluster)
            except KeyError:
                logger.debug("Found no items in {}".format(self._api))
            except Exception:
                logger.error(traceback.format_exc())
        return result

    def process_clusters_response(self):
        """
        Response processing for Kubernetes clusters API
        """
        result = list()

        # If no location is selected then collect clusters data
        # for all locations
        if not self._location:
            parent = f"{BASE_URL.format(self._project)}/-"
            result.extend(self.process_clusters_request(parent))

        # Collect clusters data for specified locations
        else:
            location_list = self._location.split(",")
            for location in location_list:
                parent = f"{BASE_URL.format(self._project)}/{location}"
                result.extend(self.process_clusters_request(parent))
        return result

    def process_operations_request(self, parent):
        """
        Request processing for Kubernetes operations API
        Argument: "parent"
        Type: String
        """
        result = list()
        request = self._service.projects().locations().operations().list(parent=parent)
        if request is not None:
            try:
                response = request.execute()
                for operation in response["operations"]:
                    result.append(operation)
            except KeyError:
                logger.debug("Found no items in {}".format(self._api))
            except Exception:
                logger.error(traceback.format_exc())
        return result

    def process_operations_response(self):
        """
        Response processing for Kubernetes operations API
        """
        result = list()

        # If no location is selected then collect operations data
        # for all locations
        if not self._location:
            parent = f"{BASE_URL.format(self._project)}/-"
            result.extend(self.process_operations_request(parent))

        # Collect operations data for specified locations
        else:
            location_list = self._location.split(",")
            for location in location_list:
                parent = f"{BASE_URL.format(self._project)}/{location}"
                result.extend(self.process_operations_request(parent))
        return result

    def process_nodepools_response(self):
        """
        Response processing for Kubernetes nodepools API
        """
        result = list()
        location_names = self.fetch_locations()

        for location in location_names:
            cluster_list = self.fetch_cluster_names(location)
            if not cluster_list:
                logger.debug("No clusters found for {} location".format(location))
            else:
                for cluster in cluster_list:
                    parent = f"{BASE_URL.format(self._project)}/{location}/clusters/{cluster}"
                    request = (
                        self._service.projects()
                        .locations()
                        .clusters()
                        .nodePools()
                        .list(parent=parent)
                    )
                    if request is not None:
                        try:
                            response = request.execute()
                            for nodepool in response["nodePools"]:
                                result.append(nodepool)
                        except KeyError:
                            logger.debug("Found no items in {}".format(self._api))
                        except Exception:
                            logger.error(traceback.format_exc())
        return result

    def process_subnetworks_response(self):
        """
        Response processing for Kubernetes Subnetworks API
        """
        result = list()
        parent = "projects/{}".format(self._project)
        request = (
            self._service.projects()
            .aggregated()
            .usableSubnetworks()
            .list(parent=parent)
        )
        while request is not None:
            try:
                response = request.execute()
                for subnetwork in response["subnetworks"]:
                    result.append(subnetwork)
                request = (
                    self._service.projects()
                    .aggregated()
                    .usableSubnetworks()
                    .list_next(previous_request=request, previous_response=response)
                )
            except KeyError:
                logger.debug("Found no items in {}".format(self._api))
                request = (
                    self._service.projects()
                    .aggregated()
                    .usableSubnetworks()
                    .list_next(previous_request=request, previous_response=response)
                )
        return result

    def fetch_results(self, api):
        """
        Gets kubernetes data for specified API
        Arguement : "api"
        Type : String
        """
        result = []
        logger.debug("Starting to fetch data for {}".format(api))

        if api == "clusters":
            result.extend(self.process_clusters_response())
        elif api == "subnetworks":
            result.extend(self.process_subnetworks_response())
        elif api == "nodepools":
            result.extend(self.process_nodepools_response())
        elif api == "operations":
            result.extend(self.process_operations_response())
        logger.debug("Fetching data for {} completed.".format(api))
        return result
