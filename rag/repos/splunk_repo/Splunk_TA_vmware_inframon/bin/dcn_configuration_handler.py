# splunk sdk imports
import splunk.admin as admin
import splunk
import sys
from splunk.clilib.bundle_paths import make_splunkhome_path

# import necessary python packages
import json
import re

# importing rest_utility
from rest_utility import setup_logger, RestError
import rest_utility as ru

# SA imports
sys.path.append(make_splunkhome_path(['etc', 'apps', 'SA-Hydra-inframon', 'bin']))
from hydra_inframon.models import HydraNodeStanza, SplunkStoredCredential

# defining global constants
logger = setup_logger(log_name="dcn_configuration.log",
                      logger_name="dcn_configuration")
local_host_path = splunk.mergeHostPath()
max_worker_process = 30
entity_type = "node"

REQUIRED_ARGS_CREATE = ['username', 'password', 'heads', 'pool_name']
REQUIRED_ARGS_EDIT = ['node', 'username', 'password', 'heads', 'pool_name']


class ConfigApp(admin.MConfigHandler):

    def setup(self):
        """This method is called at every request before handle method is called.
        This is used for adding optional and required arguments for particular requests."""
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in REQUIRED_ARGS_EDIT:
                self.supportedArgs.addReqArg(arg)

        if self.requestedAction == admin.ACTION_CREATE:
            for arg in REQUIRED_ARGS_CREATE:
                self.supportedArgs.addReqArg(arg)

    def handleRemove(self, conf_info):
        """When DELETE request with the target is done, this method is called.
        It expects the path of the DCN to be deleted. """
        try:
            node_path = self.callerArgs.id
            local_session_key = self.getSessionKey()

            node_stanza = HydraNodeStanza.from_name(node_path, "Splunk_TA_vmware_inframon", host_path=local_host_path,
                                                    session_key=local_session_key)

            if node_stanza:
                node_username = node_stanza.user
                pool_name = node_stanza.pool_name
                stored_cred = SplunkStoredCredential.from_name(
                    SplunkStoredCredential.build_name(node_stanza.host, node_username), app="Splunk_TA_vmware_inframon",
                    owner="nobody", host_path=local_host_path,
                    session_key=local_session_key)
                if stored_cred:
                    node_password = stored_cred.clear_password
                    logger.info("Deleting obsolete credential")
                    if not stored_cred.passive_delete():
                        logger.error(
                            "Could not delete obsolete credential it may linger")
                    else:
                        logger.info(
                            "Deleted successfully creds of node {0}:".format(node_stanza.host))
                else:
                    node_password = None

                if not node_stanza.passive_delete():
                    logger.error("[pool={0}]Failed to delete node {1}".format(pool_name, node_path))
                    raise RestError(500, "Failed to delete node {0}".format(node_path))
                else:
                    logger.info("[pool={0}]Successfully deleted node: {1}".format(pool_name, node_path))

                ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)
                # disabling of inputs only takes place when node is successfully deleted.
                # for disabling all the inputs(heads), heads is given as Zero.
                ru.enable_heads_on_dcn(node_username, node_password, 0, local_session_key, node_path, pool_name, logger)

                conf_info["data"]["message"] = "Node: {0} deleted successfully".format(node_path)
                conf_info["data"]["status"] = "200"
            else:
                logger.error(
                    "Failed to find node {0}, cannot delete it".format(node_path))
                raise RestError(404, "Failed to find node {0}".format(node_path))

        except Exception as e:
            logger.exception(e)
            raise e

    def handleCreate(self, conf_info):
        """When POST request is done with the first parameter as 'name' this method is called.
        All the required parameters for this method is settled up in setup() method."""
        try:
            args = self.callerArgs
            node_path = self.callerArgs.id

            local_session_key = self.getSessionKey()

            # getting all the passed arguments
            username = args.get("username")
            password = args.get("password")
            heads = args.get("heads")
            pool_name = args.get("pool_name")

            node_stanza = False

            if node_path:
                node_stanza = HydraNodeStanza.from_name(
                    node_path, "Splunk_TA_vmware_inframon", host_path=local_host_path, session_key=local_session_key)

            # checking if stanza with the given name exist or not, validation only takes place in that case.
            if node_stanza:
                response = {"status": "invalid", "message": "Stanza with the same name already exists.",
                            "credential_validation": False, "addon_validation": False}
            else:
                response = ru.validate_dcn(
                    node_path, username, password, heads, pool_name, local_session_key, logger)

            if response['status'] == "invalid":
                raise RestError(400, str(response['message']))
            else:
                # adding validation response
                conf_info["data"]["validation_status"] = response["status"]
                conf_info["data"]["validation_message"] = response["message"]

                # as fields are valid and it is in list form.
                # node_path is not in list form.
                heads = int(heads[0])
                username = username[0]
                password = password[0]
                pool_name = pool_name[0]

                # saving credentials in passwords.conf
                new_cred = SplunkStoredCredential("Splunk_TA_vmware_inframon", "nobody", username, sessionKey=local_session_key,
                                                  host_path=local_host_path)
                new_cred.realm = node_path
                new_cred.password = password
                new_cred.username = username

                if not new_cred.passive_save():
                    logger.error(
                        "[pool={0}]Failed to save credential for: realm={1} username={2}".format(pool_name, node_path,
                                                                                                 username))
                else:
                    logger.info("[pool={0}]Successfully saved credential for: realm={1} username={2}".format(pool_name,
                                                                                                             node_path,
                                                                                                             username))

                # saving stanza in inframon_hydra_node.conf

                node_stanza = HydraNodeStanza("Splunk_TA_vmware_inframon", "nobody", node_path, sessionKey=local_session_key,
                                              host_path=local_host_path)
                node_stanza.host = node_path
                node_stanza.user = username
                node_stanza.heads = heads
                node_stanza.credential_validation = response['credential_validation']
                node_stanza.addon_validation = response['addon_validation']
                node_stanza.pool_name = pool_name
                node_stanza.last_connectivity_checked = response["last_connectivity_checked"]

                # handling heads on dcn
                ru.enable_heads_on_dcn(username, password, heads, local_session_key, node_path, pool_name, logger)

                if node_stanza.passive_save():
                    # handling inframon_ta_vmware_pool.conf
                    logger.info("[pool={0}]Node stanza:{1} saved successfully.".format(pool_name, node_path))
                    ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)
                    conf_info["data"]["status"] = "200"
                    conf_info["data"]["message"] = "Node stanza:{0} saved successfully.".format(node_path)
                else:
                    logger.error("[pool={0}]Error in saving node stanza: {1}.".format(pool_name, node_path))
                    raise RestError(500, "Error in saving node stanza: {0}.".format(node_path))

        except Exception as e:
            logger.exception(e)
            raise e

    def handleList(self, conf_info):
        """When GET request is done on the endpoint this method is called,
        It returns the details of all the configured DCN in json format."""
        try:

            local_session_key = self.getSessionKey()

            # getting all the stanzas of inframon_hydra_node.conf
            stanzas = HydraNodeStanza.all(sessionKey=local_session_key)
            stanzas = stanzas.filter_by_app("Splunk_TA_vmware_inframon")
            stanzas._owner = "nobody"

            # preparing response from stanza list
            nodes = {str(stanza.host): {"host_path": stanza.host, "username": stanza.user,
                                        "credential_validation": stanza.credential_validation,
                                        "addon_validation": stanza.addon_validation, "heads": stanza.heads,
                                        "pool_name": stanza.pool_name,
                                        "last_connectivity_checked": stanza.last_connectivity_checked.strftime(
                                            "%Y-%m-%dT%H:%M:%S.%f")} for stanza in stanzas}

            conf_info["data"]["nodes"] = json.dumps(nodes)

        except Exception as e:
            logger.exception(e)
            raise e

    def handleEdit(self, conf_info):
        """when POST request is done with the target on endpoint, this method is called.
        All the required parameters for this method is settled up in setup() method."""
        try:
            args = self.callerArgs

            # target_node is node to be edited.
            target_node = self.callerArgs.id
            local_session_key = self.getSessionKey()

            # getting passed arguments.
            # node_path is a node given as a argument to edit.
            node_path = args.get("node")
            username = args.get("username")
            password = args.get("password")
            heads = args.get("heads")
            pool_name = args.get("pool_name")

            # target_node is checked explicitly to not change validate_dcn
            if target_node:
                validated_node_path = re.search(
                    "^\s*https?:\/\/[A-Za-z0-9\.\-_]+:\d+\/?\s*$", target_node)
                if validated_node_path is None:
                    logger.error("Node name passed to edit worker node is not valid.")
                    raise RestError(400, "Node name passed to edit worker node is not valid.")
                else:
                    node_stanza = HydraNodeStanza.from_name(target_node, "Splunk_TA_vmware_inframon", host_path=local_host_path,
                                                            session_key=local_session_key)

            else:
                logger.error("No node name passed to edit, cannot edit nothing!")
                raise RestError(400, "No node name passed to edit, cannot edit nothing!")

            # checking if stanza with the given new name of stanza exists.
            to_node_stanza = HydraNodeStanza.from_name(str(node_path[0]), "Splunk_TA_vmware_inframon", host_path=local_host_path,
                                                       session_key=local_session_key)
            stored_cred = False
            # checking that stanza to be edited must exists and new name provided to edit must not exists
            if not node_stanza:
                response = {"status": "invalid", "message": "No stanza with the given name exists.",
                            "credential_validation": False, "addon_validation": False}
            elif to_node_stanza and str(node_path[0]) != target_node:
                response = {"status": "invalid", "message": "Stanza with the given new name already exists.",
                            "credential_validation": False, "addon_validation": False}
            else:
                # getting credentials of stanza currently being edited.
                logger.info("getting credentials stanza node:{0} currently being edited.".format(node_stanza.host))
                stored_cred = SplunkStoredCredential.from_name(
                    SplunkStoredCredential.build_name(node_stanza.host, node_stanza.user), app="Splunk_TA_vmware_inframon",
                    owner="nobody", host_path=local_host_path, session_key=local_session_key)
                # validating given inputs
                response = ru.validate_dcn(node_path, username, password, heads, pool_name, local_session_key, logger)

            if response["status"] == "invalid":
                conf_info["data"]["message"] = str(response['message'])
                raise RestError(400, str(response['message']))
            else:
                # adding validation response
                conf_info["data"]["validation_status"] = response["status"]
                conf_info["data"]["validation_message"] = response["message"]

                node_path = node_path[0]
                heads = int(heads[0])
                username = username[0]
                password = password[0]
                pool_name = pool_name[0]

                # old password is saved for later use.
                old_password = ""
                if stored_cred:
                    old_password = stored_cred.clear_password

                cred_deleted = False
                node_username = node_stanza.user
                node_password = old_password
                old_pool_name = node_stanza.pool_name

                # first checking if stanza name is changed, in that case
                # old stanza will be deleted and new one will be created.
                if target_node != node_path:
                    logger.info(
                        "[pool=%s]collection node's old_host_path=%s edited will delete existing stanza and "
                        "create new one with new_host_path=%s. also deleting associated credential", old_pool_name,
                        target_node, node_path)

                    if stored_cred:
                        logger.info("Deleting obsolete credential")
                        if stored_cred.passive_delete():
                            cred_deleted = True
                            logger.info("Credential of previous stanza deleted.")
                        else:
                            logger.error(
                                "Could not delete obsolete credential it may linger")
                    else:
                        node_password = None

                    if not node_stanza.passive_delete():
                        logger.error("[pool={0}]Failed to delete node {1}".format(old_pool_name, target_node))
                        raise RestError(500, "Failed to delete node {0}".format(target_node))
                    else:
                        logger.info("[pool={0}]Successfully deleted stanza of node:{1}".format(old_pool_name, target_node))

                    # disabling of inputs only takes place when node is successfully deleted.
                    # For disabling all the inputs(heads), @heads parameter is given as zero.
                    ru.enable_heads_on_dcn(node_username, node_password, 0, local_session_key, target_node, old_pool_name,
                                           logger)

                    logger.info(
                        "[pool={0}]creating new hydra node stanza for host_path={1}".format(pool_name, node_path))
                    node_stanza = HydraNodeStanza(
                        "Splunk_TA_vmware_inframon", "nobody", node_path, sessionKey=local_session_key,
                        host_path=local_host_path)

                # if any of the credentials are changed new cred stanza is created and previous is deleted.
                if node_stanza.user != username or old_password != password:
                    logger.info("[pool={0}]Credentials for node:{1} is changed.".format(pool_name, node_path))
                    # this is for deleting the old creds stanza when username is changed.
                    if not cred_deleted:
                        # prev_cred : previous credentials stanza
                        prev_cred = SplunkStoredCredential.from_name(SplunkStoredCredential.build_name(node_path, str(
                            node_stanza.user)), app="Splunk_TA_vmware_inframon", owner="nobody", host_path=local_host_path,
                                                                     session_key=local_session_key)
                        if prev_cred:
                            if not prev_cred.passive_delete():
                                logger.error("Could not delete outmoded credential for node:{0} ,it may linger".format(
                                    node_path))
                            else:
                                logger.info("Stanza of previous credentials for node:{0} deleted.".format(node_path))

                    new_cred = SplunkStoredCredential("Splunk_TA_vmware_inframon", "nobody", username,
                                                      sessionKey=local_session_key, host_path=local_host_path)
                    new_cred.realm = node_path
                    new_cred.password = password
                    new_cred.username = username

                    if not new_cred.passive_save():
                        logger.error(
                            "[pool={0}]Failed to save credential for: realm={1} username={2}".format(pool_name,
                                                                                                     node_path,
                                                                                                     username))
                    else:
                        logger.info("[pool={0}]New Credentials saved successfully for: realm={1} username={2} .".format(
                            pool_name, node_path,
                            username))

                node_stanza.host = node_path
                node_stanza.user = username
                node_stanza.pool_name = pool_name
                node_stanza.credential_validation = response['credential_validation']
                node_stanza.addon_validation = response['addon_validation']
                node_stanza.last_connectivity_checked = response["last_connectivity_checked"]

                # changing in the inputs of stanza as number of heads is changed.
                if node_stanza.heads != heads:
                    node_stanza.heads = heads
                    ru.enable_heads_on_dcn(username, password, heads, local_session_key, node_path, pool_name, logger)

                if node_stanza.passive_save():
                    ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)
                    if pool_name != old_pool_name:
                        # removing sessions residing on DCN
                        ru.clear_session(node_path, username, password, local_session_key, logger)
                        ru.set_conf_modification_time(old_pool_name, entity_type, local_session_key, logger)
                    logger.info("[pool={0}]Node stanza: {1} edited successfully.".format(pool_name, target_node))
                    conf_info["data"]["status"] = "200"
                    conf_info["data"]["message"] = "Stanza: {0} edited successfully.".format(target_node)
                else:
                    logger.error("[pool={0}]Error in editing node stanza: {1}".format(pool_name, target_node))
                    raise RestError(500, "Error in editing node stanza: {0}".format(target_node))

        except Exception as e:
            logger.exception(e)
            raise e


admin.init(ConfigApp, admin.CONTEXT_APP_AND_USER)
