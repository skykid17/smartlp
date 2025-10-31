#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import json
import traceback
import splunk_ta_gcp.legacy.resource_consts as grc
import splunksdc.log as logging
from splunk_ta_gcp.legacy.resource_data_loader import ResourceDataLoader
from splunk_ta_gcp.resthandlers.locations import VPC_ACCESS_URL
from splunk_ta_gcp.legacy.common import get_http_auth_cred
from splunk_ta_gcp.legacy.common import process_vpc_access_request

logger = logging.get_module_logger()


class VpcAccessResourceDataLoader(ResourceDataLoader):
    """
    Data Loader for Resource Metadata VPC Access Input
    """

    def __init__(self, task_config):
        super(VpcAccessResourceDataLoader, self).__init__(task_config, "vpcaccess")
        self._location = task_config["location_name"]
        self._http_auth = None

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
        self._http_auth = self.build_http(self._task_config)
        results = self.fetch_results(self._api)
        self._write_events(results)

    @property
    def _get_http_auth(self):
        return self._http_auth

    def build_http(self, config):
        """
        Constructs object for making authenticated requests
        """
        return get_http_auth_cred(config)

    def prepare_response(self, api):
        """
        Process response of vpcaccess api endpoint
        Arguement : "api"
        Type : String
        """
        response_result = list()
        if api == "locations":
            requesturl = VPC_ACCESS_URL.format(self._project)
            response_result.extend(self.process_request(requesturl))
        else:
            location_names = self.fetch_locations()
            for location in location_names:
                requesturl = f"{VPC_ACCESS_URL.format(self._project)}/{location}/{api}"
                response_result.extend(self.process_request(requesturl))
        return response_result

    def fetch_locations(self):
        """
        Retrieve supported locations
        """
        location_names = list()
        auth_http = self._get_http_auth
        if not self._location:
            url = VPC_ACCESS_URL.format(self._project)
            try:
                result = process_vpc_access_request(auth_http, url, "locations")
            except Exception:
                logger.error(traceback.format_exc())
                return []

            locations = [item["locationId"] for item in result]
            location_names.extend(locations)
        else:
            location_list = self._location.split(",")
            location_names.extend(location_list)
        return location_names

    def process_request(self, requesturl):
        """
        Process request of vpcaccess API endpoint
        Argument: "requesturl"
        Type: String
        """

        result = list()
        auth_http = self._get_http_auth
        url = requesturl
        try:
            result = process_vpc_access_request(auth_http, url, self._api)
        except Exception:
            logger.error(traceback.format_exc())
            return []
        return result

    def fetch_results(self, api):
        """
        Gets resource metadata vpc access data for specified Google Cloud API
        Argument: "api"
        Type: String
        """
        result = []
        logger.debug("Starting to fetch data for {}".format(api))
        result.extend(self.prepare_response(api))
        logger.debug("Fetching data for {} completed.".format(api))
        return result
