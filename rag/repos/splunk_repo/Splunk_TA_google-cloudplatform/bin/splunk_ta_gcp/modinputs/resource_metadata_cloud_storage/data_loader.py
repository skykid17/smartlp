#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import traceback
import splunk_ta_gcp.legacy.resource_consts as grc
import splunksdc.log as logging
from splunk_ta_gcp.legacy.resource_data_loader import ResourceDataLoader


logger = logging.get_module_logger()


class StorageResourceDataLoader(ResourceDataLoader):
    """
    Data Loader for Resource Metadata Cloud Storage Input
    """

    def __init__(self, task_config):
        super(StorageResourceDataLoader, self).__init__(task_config, "storage")
        self._bucket = task_config["bucket_name"]

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

    def fetch_objects(self, bucket):
        """
        Gets list of objects under specified bucket
        """
        objects = self._service.objects()
        object_names = list()
        request = objects.list(bucket=bucket)

        while request:
            try:
                response = request.execute()
                if response.get("items"):
                    names = [item.get("name") for item in response.get("items", [])]
                    object_names.extend(names)
                request = objects.list_next(
                    previous_request=request, previous_response=response
                )
            except Exception:
                logger.error(traceback.format_exc())
                request = None
        return object_names

    def fetch_results(self, api):
        """
        Gets resource metadata storage data for specified Google Cloud API
        Arguement : "api"
        Type : String
        """
        result = []
        logger.debug("Starting to fetch data for {}".format(api))

        # Assiging the API method of discovery.Resource Object to method_to_call
        method_to_call = getattr(self._service, api)()

        if api == "buckets":
            request = method_to_call.list(project=self._project)
            result.extend(self.process_result(request, method_to_call, api))

        elif api == "objectAccessControls":
            bucket_list = self._bucket.split(",")
            for bucket in bucket_list:
                object_list = self.fetch_objects(bucket)
                if not object_list:
                    logger.debug("No objects found for {} bucket".format(bucket))
                if object_list:
                    for obj in object_list:
                        request = method_to_call.list(bucket=bucket, object=obj)
                        result.extend(self.process_result(request, method_to_call, api))
        else:
            bucket_list = self._bucket.split(",")
            for bucket in bucket_list:
                request = method_to_call.list(bucket=bucket)
                result.extend(self.process_result(request, method_to_call, api))
        return result

    def process_result(self, request, method_to_call, api):
        """
        Process response of storage API endpoint
        """
        result = []
        if hasattr(method_to_call, "list_next"):
            while request is not None:
                try:
                    response = request.execute()
                    for instance in response["items"]:
                        result.append(instance)
                    request = method_to_call.list_next(
                        previous_request=request, previous_response=response
                    )
                except KeyError:
                    logger.debug("Found no items in {}".format(api))
                    request = method_to_call.list_next(
                        previous_request=request, previous_response=response
                    )
                except Exception:
                    logger.error(traceback.format_exc())
                    request = None
        else:
            try:
                response = request.execute()
                for instance in response["items"]:
                    result.append(instance)
            except KeyError:
                logger.debug("Found no items in {}".format(api))
            except Exception:
                logger.error(traceback.format_exc())

        logger.debug("Fetching data for {} completed.".format(api))
        return result
