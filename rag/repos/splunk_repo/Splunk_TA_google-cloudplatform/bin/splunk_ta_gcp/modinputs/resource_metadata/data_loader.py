#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import traceback
import splunksdc.log as logging
from splunk_ta_gcp.legacy.resource_data_loader import ResourceDataLoader

import splunk_ta_gcp.legacy.resource_consts as grc

logger = logging.get_module_logger()


class ComputeResourceDataLoader(ResourceDataLoader):
    """
    Data Loader for Resource Metadata Input
    """

    def __init__(self, task_config):
        super(ComputeResourceDataLoader, self).__init__(task_config, "compute")

    def _do_index_data(self):
        if self._api is None or (self._zone is None and self._api != "firewalls"):
            logger.error(
                "Unsupported api or Zone.",
                api=self._task_config[grc.api],
                zone=self._task_config[grc.zone],
                ErrorCode="ConfigurationError",
                ErrorDetail="Service is unsupported.",
                datainput=self._task_config[grc.source],
            )
            return

        results = self.fetch_results(self._api, self._zone)
        self._write_events(results)

    def fetch_results(self, api, zone):
        """
        Gets resource metadata for specified Google Cloud API
        Arguement : "api"
        Type : String
        Arguement : "zone"
        Type : String
        """

        logger.debug("Starting to fetch data for {}".format(api))

        # Assiging the API method of discovery.Resource Object to method_to_call
        method_to_call = getattr(self._service, api)()

        # Calling list of method_to_call
        # firewalls api does not require zone parameter
        if api == "firewalls":
            request = method_to_call.list(project=self._project)
        else:
            request = method_to_call.list(project=self._project, zone=zone)

        result = []
        while request is not None:
            try:
                response = request.execute()
                for instance in response["items"]:
                    result.append(instance)
                request = method_to_call.list_next(
                    previous_request=request, previous_response=response
                )
            except KeyError:
                logger.info("Found no items in {}".format(api))
                request = method_to_call.list_next(
                    previous_request=request, previous_response=response
                )
        logger.debug("Fetching data for {} completed.".format(api))
        return result
