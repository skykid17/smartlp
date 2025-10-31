##
## SPDX-FileCopyrightText: 2024 Splunk, Inc.
## SPDX-License-Identifier: LicenseRef-Splunk-8-2021
##
##
import json
import os
from hashlib import blake2b

import requests

URL = "https://{}/mgmt/shared/telemetry/namespace/{}/declare"


class DataCollector:
    """
    Perform the data collection logic.
    """

    def __init__(self, task, state, logger):
        self.api_call = task.api_call
        self.api_name = task.api_name
        self.global_interval = task.global_interval
        self.splunk_host = task.splunk_host
        self.hec_protocol = task.hec_protocol
        self.hec_port = task.hec_port
        self.hec_token = task.hec_token
        self.server_url = task.f5_bigip_url
        self.task_name = task.task_name.split(":")[0]
        self.username = task.username
        self.password = task.password
        self.enabled = state
        self.server_name = task.task_name.split(":")[1]
        self.failed_api_call = None
        self.ssl_value = task.ssl_value
        self.logger = logger

    def make_api_call(self, logger):
        telemetry_namespace = ":".join(
            [self.task_name, self.server_name, self.api_call, self.api_name]
        )
        data = self.create_json(logger)
        logger.debug("Json Declaration is: {}".format(data))
        namespace_value = telemetry_namespace.encode("utf-8")
        hex_digest = blake2b(digest_size=4)
        hex_digest.update(namespace_value)
        hex_value = hex_digest.hexdigest()
        logger.info(
            "Namespace and it's hex value is: {} {}. Making API call for enable: {}".format(
                telemetry_namespace, hex_value, self.enabled
            )
        )

        f5_url = URL.format(self.server_url, hex_value)
        logger.debug("The endpoint value is: {}".format(f5_url))

        b = requests.session()
        b.auth = (self.username, self.password)
        b.verify = self.ssl_value
        b.headers.update({"Content-Type": "application/json"})
        try:
            response = b.post(f5_url, data=json.dumps(data))
            if response.status_code in [200, 201]:
                logger.info(
                    "API Call successful for namespace {} with status code {}".format(
                        telemetry_namespace, response.status_code
                    )
                )
            else:
                logger.error(
                    "API Call not successful for namespace {}. Status code returned is: {}".format(
                        telemetry_namespace, response.status_code
                    )
                )
                self.failed_api_call = telemetry_namespace
            return response.status_code
        except Exception as e:
            logger.error("Error while making API Call: {}".format(e))
            self.failed_api_call = telemetry_namespace

        return None

    def create_json(self, logger):
        try:
            absolute_path = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(absolute_path, "template_declaration.json")
            file_telemetry = open(file_path, "r")
        except FileNotFoundError as e:
            logger.error("File Not Found: {}".format(e))
        except Exception as e:
            logger.error("Error occured in file opening: {}".format(e))

        file_data = json.load(file_telemetry)

        file_data["Endpoints_Profiles"]["enable"] = self.enabled
        items = file_data["Endpoints_Profiles"]["items"]
        items["apiCallName"]["name"] = self.api_call
        items["apiCallName"]["path"] = self.api_name
        file_data["Custom_System_Poller1"]["interval"] = self.global_interval
        file_data["My_Consumer"]["host"] = self.splunk_host
        file_data["My_Consumer"]["protocol"] = self.hec_protocol
        file_data["My_Consumer"]["port"] = self.hec_port
        file_data["My_Consumer"]["passphrase"]["cipherText"] = self.hec_token

        return file_data
