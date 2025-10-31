##
## SPDX-FileCopyrightText: 2024 Splunk, Inc.
## SPDX-License-Identifier: LicenseRef-Splunk-8-2021
##
##
import json

import splunk_ta_f5_utility as common_utility


class CheckpointFeeder:
    def __init__(
        self, session_key, checkpoint_value, namespace, server_info, splunk_host, logger
    ):
        self.logger = logger
        self.api_call = checkpoint_value.get("api_call")
        self.api_name = checkpoint_value.get("api_name")
        self.global_interval = checkpoint_value.get("global_interval")
        self.splunk_host = splunk_host
        self.hec_protocol = checkpoint_value.get("hec_protocol")
        self.hec_port = checkpoint_value.get("hec_port")
        self.hec_token = checkpoint_value.get("hec_token")
        self.f5_bigip_url = server_info.get("f5_bigip_url")
        self.task_name = namespace
        self.username = server_info.get("username")
        self.password = server_info.get("password")
        self.ssl_value = common_utility.get_ssl_value(
            session_key, "ssl_verify", self.logger
        )


class Checkpointer:
    def __init__(self, session_key, checkpoint_value, logger):
        self.session_key = session_key
        self.checkpoint_value = checkpoint_value
        self.update_checkpoint = False
        self.new_namespaces = []
        self.api_call_state = "enabled"
        self.logger = logger

    def get_checkpoint_value(self, input_name):
        checkpoint_dict = {}
        checkpoint_dict = common_utility.check_if_checkpoint_exist(
            self.session_key, input_name, self.logger
        )
        if checkpoint_dict:
            self.checkpoint_value = json.loads(checkpoint_dict)

    def update_checkpoint_value(
        self,
        input_name,
        api_call,
        api_name,
        namespace,
        global_interval,
        hec_protocol,
        hec_port,
        hec_token,
        state,
        f5_bigip_url,
        input_state,
    ):
        value = {}
        value["api_call"] = api_call
        value["api_name"] = api_name
        value["global_interval"] = global_interval
        value["hec_protocol"] = hec_protocol
        value["hec_port"] = hec_port
        value["hec_token"] = hec_token
        value["state"] = state
        value["f5_bigip_url"] = f5_bigip_url
        self.checkpoint_value[namespace] = value
        self.checkpoint_value["input_state"] = input_state

    def process_checkpoint(self, checkpoint_value, feeder, namespace, state, logger):
        if checkpoint_value.get("input_state") == "enabled":
            try:
                if checkpoint_value.get(namespace):
                    if (
                        feeder.api_call == checkpoint_value[namespace]["api_call"]
                        and feeder.api_name == checkpoint_value[namespace]["api_name"]
                        and feeder.global_interval
                        == checkpoint_value[namespace]["global_interval"]
                        and feeder.hec_port == checkpoint_value[namespace]["hec_port"]
                        and feeder.hec_token == checkpoint_value[namespace]["hec_token"]
                        and checkpoint_value[namespace]["state"] == state
                        and feeder.f5_bigip_url
                        == checkpoint_value[namespace]["f5_bigip_url"]
                    ):
                        logger.info(
                            "All parameters are same for {} namespace. API call skipped.".format(
                                namespace
                            )
                        )
                        self.api_call_state = "disabled"
                        return False
            except Exception as e:
                logger.error(
                    "Error occured while processing the checkpoint: {}".format(e)
                )

        if checkpoint_value.get("input_state") == "disabled":
            if checkpoint_value.get(namespace):
                if checkpoint_value[namespace]["state"] == "disabled":
                    self.api_call_state = "disabled"
                    return False
                if checkpoint_value[namespace]["state"] == "enabled":
                    self.api_call_state = "disabled"
                    return True
            else:
                # If namespace does not exist, no need to make the API Call.
                return False

        if checkpoint_value.get("input_state") == "completed":
            self.api_call_state = "disabled"
            return False

        self.api_call_state = "enabled"
        return True

    def remove_key(self, namespace):
        del self.checkpoint_value[namespace]
