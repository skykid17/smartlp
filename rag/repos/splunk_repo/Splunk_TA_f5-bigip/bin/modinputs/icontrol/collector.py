##
## SPDX-FileCopyrightText: 2024 Splunk, Inc.
## SPDX-License-Identifier: LicenseRef-Splunk-8-2021
##
##
import json
import sys

import splunk
import splunk_ta_f5_utility as common_utility
from checkpoint import Checkpointer, CheckpointFeeder
from data_collector import DataCollector
from solnlib import conf_manager, utils
from solnlib.hec_config import HECConfig
from splunktaucclib.rest_handler.error import RestError

TA_NAME = "Splunk_TA_f5-bigip"
F5SERVER_CONF = "f5_servers"
F5TEMPLATE_CONF = "f5_templates_ts"


class Input:
    """
    Provides the Inputs details.
    """

    SPLITTER = "|"

    def __init__(self, input_item, logger):
        self.input_item = self.curate(input_item)
        self.logger = logger

    def curate(self, input_item):
        servers = input_item["servers"]
        templates = input_item["templates"]
        input_item["templates"] = templates.split(self.SPLITTER)
        input_item["servers"] = servers.split(self.SPLITTER)
        input_item["splunk_host"] = input_item.get("splunk_host")
        return input_item


class ServerManager:
    """
    Provides the Server details.
    """

    def __init__(self, servers, logger):
        self.server_names = servers
        self.logger = logger

    def get_servers(self, session_key):
        server_list = []
        for server_name in self.server_names:
            try:
                server_obj = Server(self.logger).server_obj(server_name, session_key)
            except ValueError as ve:
                self.logger.error(ve)
                continue
            server_list.append(server_obj)
        if not server_list:
            sys.exit(1)

        return server_list


class TemplateManager:
    """
    Provide the template related details
    """

    def __init__(self, templates, logger):
        self.template_names = templates
        self.logger = logger

    def get_templates(self, session_key):
        template_list = []
        for template_name in self.template_names:
            try:
                template_obj = Template(self.logger).template_obj(
                    template_name, session_key
                )
            except ValueError as ve:
                self.logger.error(ve)
                continue
            template_list.append(template_obj)
        if not template_list:
            sys.exit(1)
        return template_list


class Server:
    """
    Provide the server details
    """

    def __init__(self, logger):
        self.server_ = {}
        self.logger = logger

    def server_obj(self, server_name, session_key):
        if not bool(self.server_):
            server_detail = ServerHandler(server_name, session_key).get_server()
            self.server_[server_name] = server_detail
            if self.server_[server_name].get("account_password") is None:
                self.logger.error(
                    "account_password is not provided, it is mandatory. we cannot proceed further without account_password."  # noqa: E501
                )
                raise ValueError(
                    "Stopping data collection process for {} server due to not having enough information......".format(
                        server_name
                    )
                )
            if self.server_[server_name].get("account_name") is None:
                self.logger.error(
                    "account_name is not provided, it is mandatory. we cannot proceed further without account_name."
                )
                raise ValueError(
                    "Stopping data collection process for {} server due to not having enough information......".format(
                        server_name
                    )
                )
            if self.server_[server_name].get("f5_bigip_url") is None:
                self.logger.error(
                    "f5_bigip_url is not provided, it is mandatory. we cannot proceed further without f5_bigip_url."
                )
                raise ValueError(
                    "Stopping data collection process for {} server due to not having enough information......".format(
                        server_name
                    )
                )
        return self.server_


class Template:
    """
    Provide the template details
    """

    def __init__(self, logger):
        self.template_ = {}
        self.logger = logger

    def template_obj(self, template_name, session_key):
        if not bool(self.template_):
            template_detail = TemplateHandler(template_name, session_key).get_template()
            self.template_[template_name] = template_detail
            if self.template_[template_name].get("content") is None:
                self.logger.error(
                    "content is not provided, it is mandatory. we cannot proceed further without content."
                )
                raise ValueError(
                    "Stopping data collection process for {} template due to not having enough information......".format(  # noqa: E501
                        template_name
                    )
                )
        return self.template_


class ServerHandler:
    def __init__(self, server_name, session_key):
        self.server_name = server_name
        self.session_key = session_key
        self.server_ = None

    def get_server_info(self):
        cfm = conf_manager.ConfManager(
            self.session_key,
            TA_NAME,
            realm="__REST_CREDENTIAL__#{}#configs/conf-f5_servers".format(TA_NAME),
        )
        cfm_server = cfm.get_conf(F5SERVER_CONF)
        return cfm_server.get(self.server_name)

    def get_server(self):
        if self.server_ is None:
            self.server_ = self.get_server_info()
        return self.server_


class TemplateHandler:
    def __init__(self, template_name, session_key):
        self.template_name = template_name
        self.session_key = session_key
        self.template_ = None

    def get_template_info(self):
        cfm = conf_manager.ConfManager(self.session_key, TA_NAME)
        cfm_template = cfm.get_conf(F5TEMPLATE_CONF)
        return cfm_template.get(self.template_name)

    def get_template(self):
        if self.template_ is None:
            self.template_ = self.get_template_info()
        return self.template_


class IcontrolCollector:
    """
    Collecting the iControl events using Hec tokens.
    """

    def __init__(self, session_key, input_item, checkpoint_operation, logger):
        self.session_key = session_key
        self.f5_items = input_item
        self._input = None
        self._servers = None
        self._templates = None
        self._hec_info = None
        self.checkpoint_operation = checkpoint_operation
        self.logger = logger

    @property
    def input(self):
        """
        Provide the input information
        """
        if self._input is None:
            self._input = Input(self.f5_items, self.logger).input_item
            if self._input.get("hec_name") is None:
                self.logger.error(
                    "hec_name is not provided, it is mandatory. we cannot proceed further without hec_name."
                )
                raise ValueError(
                    "Stopping data collection process due to not having enough information......"
                )
            if self._input.get("servers") is None:
                self.logger.error(
                    "servers is not provided, it is mandatory. we cannot proceed further without servers."
                )
                raise ValueError(
                    "Stopping data collection process due to not having enough information......"
                )
            if self._input.get("templates") is None:
                self.logger.error(
                    "templates is not provided, it is mandatory. we cannot proceed further without templates."
                )
                raise ValueError(
                    "Stopping data collection process due to not having enough information......"
                )
            if self._input.get("splunk_host") is None:
                self.logger.error(
                    "splunk_host is not provided, it is mandatory. we cannot proceed further without splunk_host."
                )
                raise ValueError(
                    "Stopping data collection process due to not having enough information......"
                )

        return self._input

    @property
    def servers(self):
        """
        Provide the servers information.
        """
        if self._servers is None:
            self._servers = ServerManager(self.input.get("servers"), self.logger)
            self._servers = self._servers.get_servers(self.session_key)
        return self._servers

    @property
    def templates(self):
        """
        Provide the template infomration.
        """
        if self._templates is None:
            self._templates = TemplateManager(
                self.input.get("templates"), self.logger
            ).get_templates(self.session_key)
        return self._templates

    @property
    def hec_info(self):
        """
        Provide the hec information.
        """
        if self._hec_info is None:
            try:
                self._hec_info = HECCollector(
                    self.session_key, self.logger
                ).get_hec_configuration(self.input.get("hec_name"))
            except Exception as e:
                self.logger.error(
                    "Getting error while retriving {} hec information".format(
                        self.input.get("hec_name")
                    )
                )
                self.logger.error(e)

        return self._hec_info

    def run(self, get_checkpoint=False):
        """
        Manipulate and Kickoff the iControl data collection.
        """
        try:
            tasks = TaskGen(self, self.logger).tasks
        except ValueError as ve:
            self.logger.error(ve)
            raise ValueError(409, ve)

        input_name = self.input.get("name")
        # Check if data collection is ongoing. If it's ongoing, skip iteration otherwise set the param as collecting
        checkpoint_object = Checkpointer(self.session_key, {}, self.logger)
        checkpoint_object.get_checkpoint_value(input_name)
        current_checkpoint_operation = self.checkpoint_operation
        old_checkpoint_value = {}
        checkpoint_object.get_checkpoint_value(input_name)

        if checkpoint_object.checkpoint_value and get_checkpoint:
            return checkpoint_object.checkpoint_value

        if checkpoint_object.checkpoint_value:
            old_checkpoint_value = checkpoint_object.checkpoint_value
            if old_checkpoint_value.get("data_collection_state") == "collecting":
                self.logger.info(
                    "Data collection is in progress. Hence, skipping the invocation"
                )
                raise RestError(
                    409, "Data collection is in progress. So, try again after sometime."
                )

        old_checkpoint_value["data_collection_state"] = "collecting"
        try:
            encoded_value = common_utility.encode(json.dumps(old_checkpoint_value))
            common_utility.checkpoint_handler(
                self.session_key, input_name, str(encoded_value), self.logger
            )
        except Exception as e:
            self.logger.error(
                "Error while updating data collection state for checkpoint: {}".format(
                    e
                )
            )

        checkpoint_value = {}
        existing_namespace = []
        failed_api_call = []
        checkpoint_object.get_checkpoint_value(input_name)
        if checkpoint_object.checkpoint_value:
            checkpoint_value = checkpoint_object.checkpoint_value
            existing_namespace = [
                key for key in checkpoint_value.keys() if len(key.split(":")) > 1
            ]
            # Update checkpoint operation
            if (
                checkpoint_value.get("input_state") == "completed"
                and self.checkpoint_operation == "enabled"
            ):
                self.logger.info(
                    "Data collection is completed for the disabled API Calls. Please re-enable the input to perform the data collection"  # noqa: E501
                )
                checkpoint_object.remove_key("data_collection_state")
                try:
                    encode_value = common_utility.encode(
                        json.dumps(checkpoint_object.checkpoint_value)
                    )
                    common_utility.checkpoint_handler(
                        self.session_key, input_name, str(encode_value), self.logger
                    )
                except Exception as e:
                    self.logger.error(
                        "Error while updating checkpoint after removing the data_collection_state key: {}".format(
                            e
                        )
                    )
                sys.exit(1)
            if (
                checkpoint_value.get("input_state") == "disabled"
                and self.checkpoint_operation == "enabled"
            ):
                self.checkpoint_operation = "disabled"

        for task in tasks:
            task_object = F5BigIPTasks(
                self.session_key,
                task,
                self.checkpoint_operation,
                checkpoint_object,
                self.logger,
            )
            failed_api_call = task_object.create_objects(failed_api_call)
            template_name = task.task_name.split(":")[2]
            server_name = task.task_name.split(":")[1]
            self.logger.info(
                "Successfully verified/executed the configuration for template: {} for server {}".format(
                    template_name, server_name
                )
            )

        if checkpoint_object.update_checkpoint:
            self.logger.debug(
                "Checkpoint value is: {}".format(checkpoint_object.checkpoint_value)
            )
            # Update the checkpoint
            encode_value = common_utility.encode(
                json.dumps(checkpoint_object.checkpoint_value)
            )
            try:
                common_utility.checkpoint_handler(
                    self.session_key, input_name, str(encode_value), self.logger
                )
            except Exception as e:
                self.logger.error(
                    "Error occured while updating checkpoint: {}".format(e)
                )
        else:
            self.logger.info(
                "No need to update the checkpoint as all the params are same."
            )

        if self.checkpoint_operation in ["enabled", "disabled"] and checkpoint_value:
            new_namespaces = checkpoint_object.new_namespaces
            try:
                diff_namespaces = list(set(existing_namespace) - set(new_namespaces))
            except Exception as e:
                self.logger.error("Error in different namespaces: {}".format(e))
            self.logger.info(
                "The difference in namespaces from the previous call are: {}".format(
                    diff_namespaces
                )
            )

            if diff_namespaces:
                for namespace in diff_namespaces:
                    server_name = namespace.split(":")[1]
                    splunk_host = self._input.get("splunk_host")
                    server_obj = ServerHandler(server_name, self.session_key)
                    server_value = server_obj.get_server_info()
                    server_info = {}
                    if server_value:
                        server_info["username"] = server_value.get("account_name")
                        server_info["password"] = server_value.get("account_password")
                        server_info["f5_bigip_url"] = server_value.get("f5_bigip_url")

                    feeder = CheckpointFeeder(
                        self.session_key,
                        checkpoint_value[namespace],
                        namespace,
                        server_info,
                        splunk_host,
                        self.logger,
                    )
                    data_collector_object = DataCollector(feeder, "false", self.logger)
                    response = data_collector_object.make_api_call(self.logger)
                    if response == 200:
                        # Remove namespace key from the checkpoint.
                        checkpoint_object.remove_key(namespace)
                        try:
                            # Update the checkpoint after deleting the key.
                            encoded_value = common_utility.encode(
                                json.dumps(checkpoint_object.checkpoint_value)
                            )
                            common_utility.checkpoint_handler(
                                self.session_key,
                                input_name,
                                str(encoded_value),
                                self.logger,
                            )
                            self.logger.debug(
                                "Checkpoint after removing the changed key is: {}".format(
                                    checkpoint_object.checkpoint_value
                                )
                            )
                        except Exception as e:
                            self.logger.error(
                                "Error while updating checkpoint after deleting the key: {}".format(
                                    e
                                )
                            )
                    if data_collector_object.failed_api_call:
                        failed_api_call.append(data_collector_object.failed_api_call)

        # For the 1st time at disable input, if all api calls are successful, remove input_state.
        if current_checkpoint_operation == "disabled" and not failed_api_call:
            checkpoint_object.remove_key("input_state")
            try:
                encode_value = common_utility.encode(
                    json.dumps(checkpoint_object.checkpoint_value)
                )
                common_utility.checkpoint_handler(
                    self.session_key, input_name, str(encode_value), self.logger
                )
            except Exception as e:
                self.logger.error(
                    "Error while updating checkpoint after deleting the input_state key: {}".format(
                        e
                    )
                )
        # Check if input_state = completed and disable_api_call and there are no failed_api_call, remove input_state.
        elif (
            checkpoint_object.checkpoint_value.get("input_state") == "completed"
            and self.checkpoint_operation == "disabled"
            and not failed_api_call
        ):
            checkpoint_object.remove_key("input_state")
            try:
                encode_value = common_utility.encode(
                    json.dumps(checkpoint_object.checkpoint_value)
                )
                common_utility.checkpoint_handler(
                    self.session_key, input_name, str(encode_value), self.logger
                )
            except Exception as e:
                self.logger.error(
                    "Error while updating checkpoint after deleting the key: {}".format(
                        e
                    )
                )
        # If operation is disabled and all api calls are successful, update input_state = completed.
        elif self.checkpoint_operation == "disabled" and not failed_api_call:
            checkpoint_object.checkpoint_value["input_state"] = "completed"
            try:
                encode_value = common_utility.encode(
                    json.dumps(checkpoint_object.checkpoint_value)
                )
                common_utility.checkpoint_handler(
                    self.session_key, input_name, str(encode_value), self.logger
                )
            except Exception as e:
                self.logger.error(
                    "Error while updating checkpoint after updating the input state to completed: {}".format(
                        e
                    )
                )

        # Remove data_collection_state from checkpoint
        checkpoint_object.remove_key("data_collection_state")
        try:
            encode_value = common_utility.encode(
                json.dumps(checkpoint_object.checkpoint_value)
            )
            common_utility.checkpoint_handler(
                self.session_key, input_name, str(encode_value), self.logger
            )
        except Exception as e:
            self.logger.error(
                "Error while updating checkpoint after removing the data_collection_state: {}".format(
                    e
                )
            )
        return failed_api_call


class F5BigIPTasks:
    """
    This class is used to create thread for each task object.
    """

    def __init__(
        self, session_key, task, checkpoint_operation, checkpoint_object, logger
    ):
        self.session_key = session_key
        self.task = task
        self.checkpoint_operation = checkpoint_operation
        self.checkpoint_object = checkpoint_object
        self.logger = logger

    def create_objects(self, failed_api_call):
        for template in self.task.template.keys():
            self.logger.info("Collecting data for template: {}".format(template))
            for api_info in self.task.template[template].get("api_detail"):
                feeder = Feeder(self.session_key, self.task, api_info, self.logger)
                input_name = self.task.task_name.split(":")[0]
                api_name = feeder.api_name.replace("/", "_")
                namespace = ":".join(
                    [input_name, feeder.server_name, feeder.api_call, api_name]
                )
                try:
                    if self.checkpoint_operation == "enabled":
                        self.checkpoint_object.new_namespaces.append(namespace)
                        if self.checkpoint_object.checkpoint_value:
                            # Check if the params are same as stored in checkpoint.
                            make_api_call = self.checkpoint_object.process_checkpoint(
                                self.checkpoint_object.checkpoint_value,
                                feeder,
                                namespace,
                                "enabled",
                                self.logger,
                            )
                            if not make_api_call:
                                continue

                        data_collector_object = DataCollector(
                            feeder, "true", self.logger
                        )

                        if self.checkpoint_object.api_call_state == "disabled":
                            data_collector_object = DataCollector(
                                feeder, "false", self.logger
                            )

                        response = data_collector_object.make_api_call(self.logger)
                        if response == 200:
                            self.checkpoint_object.update_checkpoint = True
                            try:
                                self.checkpoint_object.update_checkpoint_value(
                                    input_name,
                                    feeder.api_call,
                                    feeder.api_name,
                                    namespace,
                                    feeder.global_interval,
                                    feeder.hec_protocol,
                                    feeder.hec_port,
                                    feeder.hec_token,
                                    "enabled",
                                    feeder.f5_bigip_url,
                                    self.checkpoint_operation,
                                )
                            except Exception as e:
                                self.logger.error(
                                    "Error while updating checkpoint: {}".format(e)
                                )

                        if data_collector_object.failed_api_call:
                            failed_api_call.append(
                                data_collector_object.failed_api_call
                            )

                    if self.checkpoint_operation == "disabled":
                        self.checkpoint_object.new_namespaces.append(namespace)
                        if self.checkpoint_object.checkpoint_value:
                            make_api_call = self.checkpoint_object.process_checkpoint(
                                self.checkpoint_object.checkpoint_value,
                                feeder,
                                namespace,
                                "disabled",
                                self.logger,
                            )
                            if not make_api_call:
                                continue

                        data_collector_object = DataCollector(
                            feeder, "false", self.logger
                        )
                        response = data_collector_object.make_api_call(self.logger)
                        if response == 200:
                            self.checkpoint_object.update_checkpoint = True
                            try:
                                self.checkpoint_object.update_checkpoint_value(
                                    input_name,
                                    feeder.api_call,
                                    feeder.api_name,
                                    namespace,
                                    feeder.global_interval,
                                    feeder.hec_protocol,
                                    feeder.hec_port,
                                    feeder.hec_token,
                                    "disabled",
                                    feeder.f5_bigip_url,
                                    self.checkpoint_operation,
                                )
                            except Exception as e:
                                self.logger.error(
                                    "Error while updating checkpoint: {}".format(e)
                                )
                        if data_collector_object.failed_api_call:
                            failed_api_call.append(
                                data_collector_object.failed_api_call
                            )
                except Exception as e:
                    self.logger.error(
                        "Error occured while creating feeder objects: {}".format(e)
                    )

        return failed_api_call


class Feeder:
    def __init__(self, session_key, task, api_info, logger):
        self.api_call, self.api_name, self.global_interval = self.curate_template(
            api_info
        )
        (
            self.hec_protocol,
            self.hec_port,
            self.hec_token,
        ) = self.curate_hec_info(task.hec_info)
        (
            self.server_name,
            self.username,
            self.password,
            self.f5_bigip_url,
        ) = self.curate_server(task.server)
        self.task_name = task.task_name
        self.logger = logger
        self.splunk_host = task.inputs.get("splunk_host")
        self.ssl_value = common_utility.get_ssl_value(
            session_key, "ssl_verify", self.logger
        )

    def curate_template(self, api_info):
        return api_info.split(",")

    def curate_hec_info(self, hec_info):
        return (
            hec_info.get("hec_protocol"),
            hec_info.get("hec_port"),
            hec_info.get("token"),
        )

    def curate_server(self, server_info):
        for server_name in server_info.keys():
            return (
                server_name,
                server_info[server_name].get("account_name"),
                server_info[server_name].get("account_password"),
                server_info[server_name].get("f5_bigip_url"),
            )


class TaskGen:
    """
    Gnerate tasks from provided collector.
    """

    def __init__(self, collector, logger):
        self.collector = collector
        self._tasks = None
        self.logger = logger

    @property
    def tasks(self):
        if self._tasks is None:
            self._tasks = self.generate_tasks()
        return self._tasks

    def generate_tasks(self):
        tasks = []
        for server in self.collector.input["servers"]:
            for template in self.collector.input["templates"]:
                task_name = "{}:{}:{}".format(
                    self.collector.input["name"], server, template
                )
                task = Task(task_name, self.logger)
                task.build_task(self.collector)
                tasks.append(task)

        return tasks


class Task:
    """
    Creating task object.
    """

    def __init__(self, task_name, logger):
        self.server = None
        self.template = None
        # We can do better here, currently input detail is duplicating in task object
        self.inputs = None
        self.task_name = task_name
        self.logger = logger

    def build_task(self, collector):
        input_name, server_name, template_name = self.task_name.split(":")
        self.logger.info(
            "Building task for input name:{}, server_name:{}, template_name:{}".format(
                input_name, server_name, template_name
            )
        )
        self.inputs = collector.input
        for server_detail in collector.servers:
            if server_detail.get(server_name):
                self.server = server_detail
                break

        for template_detail in collector.templates:
            if template_detail.get(template_name):
                global_interval = self.get_global_interval(server_name)
                api_detail = self.decode_template(template_detail, template_name)
                curated_api_details = []
                for api in api_detail:
                    api_splitter = self.api_splitter(api, global_interval)
                    if api_splitter is None:
                        self.logger.error(
                            "Skipping the following API for not following API templates, Each template record must be of the form: <API Name>,<API Call>,<interval value>"  # noqa: E501
                        )
                        continue
                    else:
                        curated_api_details.append(api_splitter)
                template_detail[template_name].update(
                    {"api_detail": curated_api_details}
                )
                self.template = template_detail
                break

        self.hec_info = collector.hec_info
        self.add_key("task", self.inputs, self.inputs)

    def api_splitter(self, api, global_interval):
        api_split = api.split(",")[:3]
        if len(api_split) < 2 or len(api_split) > 3:
            return None
        try:
            if len(api_split) == 2:
                api_split.append(str(global_interval))
                return ",".join(api_split)
            if int(api_split[2]):
                return ",".join(api_split)
        except ValueError:
            self.logger.error(
                "Please provide the integer value for the api : {}".format(api)
            )
            return None

    def get_global_interval(self, server_name):
        if self.server[server_name].get("interval"):
            global_interval = self.server[server_name].get("interval")
        else:
            global_interval = self.inputs.get("interval")

        return global_interval

    def add_key(self, name, value, dictionary):
        dictionary[name] = value
        return dictionary

    def decode_template(self, template, template_name):
        api_list = []
        data = template.get(template_name)
        if data.get("content"):
            decoded_value = common_utility.decode(data["content"])
            api_list_values = decoded_value.split("\n")
            api_list = [value for value in api_list_values if len(value.split("/")) > 2]

        return api_list


class HECCollector:
    """
    Provide the interface for HEC related operation.
    """

    def __init__(self, session_key, logger):
        self.hec = HECConfig(session_key)
        self.logger = logger

    def get_hec_configuration(self, hec_name):
        """
        Provides the hec details.
        """
        import socket  # noqa: F401

        hec_port = splunk.getDefault("port")  # noqa: F841
        hec_info = self.hec.get_input(hec_name)
        hec_details = self.hec.get_settings()
        protocol = "https" if utils.is_true(hec_details.get("enableSSL")) else "http"
        hec_info.update({"hec_protocol": protocol})
        hec_info.update({"hec_port": hec_details.get("port")})

        return hec_info
