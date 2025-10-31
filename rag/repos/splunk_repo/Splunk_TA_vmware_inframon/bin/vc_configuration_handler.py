# Core Python Imports
import sys
import json

# Splunkd imports
import splunk
import splunk.admin as admin
from splunk.clilib.bundle_paths import make_splunkhome_path

# TA and SA Imports
sys.path.append(make_splunkhome_path(['etc', 'apps', 'SA-Hydra-inframon', 'bin']))
sys.path.append(make_splunkhome_path(
    ['etc', 'apps', 'Splunk_TA_vmware_inframon', 'bin']))
from hydra_inframon.models import SplunkStoredCredential
from ta_vmware_inframon.models import TAVMwareCollectionStanza, TAVMwareVCenterForwarderStanza

# rest utility imports
import rest_utility as ru
from rest_utility import setup_logger, RestError

# defining global constants
logger = setup_logger(log_name="vcenter_configuration.log",
                      logger_name="vcenter_configuration")
local_host_path = splunk.mergeHostPath()
entity_type = "collection"

REQUIRED_ARGS_CREATE = ['username', 'password', 'collect_vc_logs', 'pool_name']
OPT_ARGS_CREATE = ['vc_splunk_uri', 'vc_splunk_password', 'vc_splunk_username', 'host_include_list', 'host_exclude_list']
REQUIRED_ARGS_EDIT = ['vc', 'username', 'password', 'collect_vc_logs', 'pool_name']
OPT_ARGS_EDIT = ['vc_splunk_uri', 'vc_splunk_password', 'vc_splunk_username', 'host_include_list',
                 'host_exclude_list']


class ConfigApp(admin.MConfigHandler):

    def setup(self):
        """This method is called at every request before handle method is called.
        This is used for adding optional and required arguments for particular requests."""
        if self.requestedAction == admin.ACTION_CREATE:
            for arg in REQUIRED_ARGS_CREATE:
                self.supportedArgs.addReqArg(arg)

            for arg in OPT_ARGS_CREATE:
                self.supportedArgs.addOptArg(arg)

        if self.requestedAction == admin.ACTION_EDIT:
            for arg in REQUIRED_ARGS_EDIT:
                self.supportedArgs.addReqArg(arg)

            for arg in OPT_ARGS_EDIT:
                self.supportedArgs.addOptArg(arg)

    def handleRemove(self, conf_info):
        """When DELETE request with the target is done, this method is called.
        It expects the name of vcenter to be deleted. """
        try:
            vc_path = self.callerArgs.id
            local_session_key = self.getSessionKey()

            vc_stanza = TAVMwareCollectionStanza.from_name(vc_path, "Splunk_TA_vmware_inframon", "nobody",
                                                           session_key=local_session_key,
                                                           host_path=local_host_path)
            pool_name = ""
            if vc_stanza:
                pool_name = vc_stanza.pool_name
            vc_stanza_deleted = ru.delete_vcenter_stanza(vc_path, local_session_key, logger)

            if vc_stanza_deleted:
                ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)
                conf_info["data"]["status"] = "200"
                conf_info["data"]["message"] = "Stanza Deleted Successfully."
                logger.info("[pool={1}]vCenter stanza for:{0} deleted successfully.".format(vc_path, pool_name))
            else:
                raise RestError(500, "Error while Deleting the Stanza {}.".format(vc_path))

            _ = ru.delete_vcenter_forwarder_stanza(vc_path, local_session_key, pool_name, logger)

        except Exception as e:
            logger.exception(e)
            raise e

    def handleCreate(self, conf_info):
        """When POST request is done with the first parameter as 'name' this method is called.
        All the required parameters for this method is settled up in setup() method."""
        try:
            vc_path = self.callerArgs.id
            args = self.callerArgs
            local_session_key = self.getSessionKey()

            # getting all the passed arguments
            username = args.get("username")
            password = args.get("password")
            pool_name = args.get("pool_name")
            collect_vc_logs = args.get("collect_vc_logs")
            host_include_list = args.get("host_include_list", "")
            host_exclude_list = args.get("host_exclude_list", "")

            host_stanza = False

            if vc_path:
                host_stanza = TAVMwareCollectionStanza.from_name(vc_path, "Splunk_TA_vmware_inframon", "nobody",
                                                                 session_key=local_session_key,
                                                                 host_path=local_host_path)

            if host_stanza:
                response = {"status": "invalid", "message": "Stanza with the same name already exists.",
                            "credential_validation": False}
            else:
                response = ru.validate_vcenter(vc_path, username, password, pool_name, local_session_key, logger)

            if response['status'] == "invalid":
                raise RestError(400, str(response['message']))
            else:
                # Adding validation response
                conf_info["data"]["validate_vcenter_status"] = response["status"]
                conf_info["data"]["validate_vcenter_message"] = response["message"]

                username = username[0]
                password = password[0]
                pool_name = pool_name[0]
                collect_vc_logs = collect_vc_logs[0]

                # string to boolean convert
                collect_vc_logs = True if collect_vc_logs == 'true' else False

                new_cred = SplunkStoredCredential("Splunk_TA_vmware_inframon", "nobody", username, sessionKey=local_session_key,
                                                  host_path=local_host_path)
                logger.info("credential stanza for vCenter:{0} created.".format(vc_path))
                new_cred.realm = vc_path
                new_cred.password = password
                new_cred.username = username

                if not new_cred.passive_save():
                    logger.error(
                        "[pool={2}]Failed to save credential for: realm={0} username={1}".format(vc_path, username,
                                                                                                 pool_name))
                else:
                    logger.info(
                        "[pool={2}]Successfully saved credential for: realm={0} username={1}".format(vc_path, username,
                                                                                                     pool_name))

                vc_stanza = TAVMwareCollectionStanza("Splunk_TA_vmware_inframon", "nobody", vc_path,
                                                     sessionKey=local_session_key,
                                                     host_path=local_host_path)

                vc_stanza.target = [vc_path]
                vc_stanza.target_type = "vc"
                vc_stanza.username = username
                vc_stanza.pool_name = pool_name
                vc_stanza.credential_validation = response["credential_validation"]
                vc_stanza.last_connectivity_checked = response["last_connectivity_checked"]

                # storing host include and exclude list

                if isinstance(host_include_list, list):
                    host_include_list = host_include_list[0]
                if isinstance(host_exclude_list, list):
                    host_exclude_list = host_exclude_list[0]

                host_include_list = str(host_include_list).strip()
                host_exclude_list = str(host_exclude_list).strip()

                vc_stanza.managed_host_includelist = host_include_list if len(host_include_list)>0 else 'None'
                vc_stanza.managed_host_excludelist = host_exclude_list if len(host_exclude_list)>0 else 'None'

                if vc_stanza.passive_save():
                    # handling inframon_ta_vmware_pool.conf
                    ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)
                    conf_info["data"]["save_vcenter_status"] = "200"
                    conf_info["data"]["save_vcenter_message"] = "vCenter Stanza:{0} saved successfully.".format(vc_path)
                    logger.info("[pool={1}]vCenter Stanza:{0} saved successfully.".format(vc_path, pool_name))
                else:
                    raise RestError(500, "Could not save vc_stanza={0}".format(str(vc_stanza)))

                """after successfully save collection stanza"""

                if collect_vc_logs:
                    vc_splunk_uri = args.get("vc_splunk_uri")
                    vc_splunk_username = args.get("vc_splunk_username")
                    vc_splunk_password = args.get("vc_splunk_password")

                    forwarder_stanza = TAVMwareVCenterForwarderStanza.from_name(vc_path, "Splunk_TA_vmware_inframon",
                                                                                host_path=local_host_path,
                                                                                session_key=local_session_key)

                    if forwarder_stanza:
                        response = {"status": "invalid", "message": "Stanza for the same forwarder already exists.",
                                    "credential_validation": False, "addon_validation": False}
                    else:
                        response = ru.validate_vcenter_forwarder(vc_splunk_uri, vc_splunk_username, vc_splunk_password,
                                                                 local_session_key, logger)

                    # Adding forwarder validation response
                    conf_info["data"]["validate_forwarder_status"] = response["status"]
                    conf_info["data"]["validate_forwarder_message"] = response["message"]

                    if response["status"] != "invalid":

                        vc_splunk_uri = vc_splunk_uri[0]
                        vc_splunk_username = vc_splunk_username[0]
                        vc_splunk_password = vc_splunk_password[0]

                        forwarder_cred_stanza = SplunkStoredCredential("Splunk_TA_vmware_inframon", "nobody", vc_splunk_username,
                                                                       sessionKey=local_session_key,
                                                                       host_path=local_host_path)
                        forwarder_cred_stanza.realm = vc_splunk_uri
                        forwarder_cred_stanza.password = vc_splunk_password
                        forwarder_cred_stanza.username = vc_splunk_username

                        if not forwarder_cred_stanza.passive_save():
                            logger.error(
                                "[pool={2}]Failed to save vc splunk forwarder credential for: realm={0} username={1}".format(
                                    vc_splunk_uri, vc_splunk_username, pool_name))
                        else:
                            logger.info(
                                "[pool={2}]Successfully saved vc splunk forwarder credential for: realm={0} username={1}".format(
                                    vc_splunk_uri, vc_splunk_username, pool_name))

                        forwarder_stanza = TAVMwareVCenterForwarderStanza("Splunk_TA_vmware_inframon", "nobody", vc_path,
                                                                          sessionKey=local_session_key,
                                                                          host_path=local_host_path)
                        forwarder_stanza.host = vc_splunk_uri
                        forwarder_stanza.user = vc_splunk_username
                        forwarder_stanza.collect_vc_logs = collect_vc_logs
                        forwarder_stanza.credential_validation = response["credential_validation"]
                        forwarder_stanza.addon_validation = response["addon_validation"]

                        ru.toggle_vc_inputs(vc_splunk_uri, vc_splunk_username, vc_splunk_password, vc_path,
                                            local_session_key, pool_name, logger, disable=False)
                        if not forwarder_stanza.passive_save():
                            conf_info["data"]["save_forwarder_status"] = "500"
                            conf_info["data"][
                                "save_forwarder_message"] = "problem saving the splunk forwarder stanza for vc={0} and vc_splunk_uri={1}, stanza will have to be regenerated.".format(
                                vc_path, vc_splunk_uri)
                            logger.error(
                                "[pool=%s]problem saving the splunk forwarder stanza for vc=%s and vc_splunk_uri=%s, stanza will have to be regenerated.",
                                pool_name, vc_path, vc_splunk_uri)
                        else:
                            conf_info["data"]["save_forwarder_status"] = "200"
                            conf_info["data"][
                                "save_forwarder_message"] = "Splunk forwarder stanza for vc={0} and vc_splunk_uri={1} saved successfully".format(
                                vc_path, vc_splunk_uri)
                            logger.info(
                                "[pool={2}]Splunk forwarder stanza for vc={0} and vc_splunk_uri={1} saved successfully".format(
                                    vc_path, vc_splunk_uri, pool_name))

        except Exception as e:
            logger.exception(e)
            raise e

    def handleList(self, conf_info):
        """When GET request is done on the endpoint this method is called,
        It returns the details of all the configured vCenter in json format."""
        try:
            local_session_key = self.getSessionKey()
            stanzas = TAVMwareCollectionStanza.all(sessionKey=local_session_key)
            vcenters = {}

            for stanza in stanzas:

                key = stanza.target[0]
                val = dict()

                val["target"] = stanza.target[0]
                val["pool_name"] = stanza.pool_name
                val["host_exclude_list"] = stanza.managed_host_excludelist
                val["host_include_list"] = stanza.managed_host_includelist
                val["credential_validation"] = stanza.credential_validation
                val["username"] = stanza.username
                val["last_connectivity_checked"] = stanza.last_connectivity_checked.strftime("%Y-%m-%dT%H:%M:%S.%f")

                forwarder_stanza = TAVMwareVCenterForwarderStanza.from_name(stanza.target[0], "Splunk_TA_vmware_inframon",
                                                                            "nobody", session_key=local_session_key,
                                                                            host_path=local_host_path)

                if forwarder_stanza:
                    val["collect_vc_logs"] = forwarder_stanza.collect_vc_logs
                    if forwarder_stanza.collect_vc_logs:
                        val["forwarder_uri"] = forwarder_stanza.host
                        val["forwarder_username"] = forwarder_stanza.user
                        val["forwarder_credential_validation"] = forwarder_stanza.credential_validation
                        val["forwarder_addon_validation"] = forwarder_stanza.addon_validation
                else:
                    val["collect_vc_logs"] = False
                    val["forwarder_uri"] = ""
                    val["forwarder_username"] = ""
                    val["forwarder_credential_validation"] = ""
                    val["forwarder_addon_validation"] = ""

                vcenters.update({key: val})

            conf_info["data"]["vcenters"] = json.dumps(vcenters)
        except Exception as e:
            logger.exception(e)
            raise e

    def handleEdit(self, conf_info):
        """when POST request is done with the target on endpoint, this method is called.
            All the required parameters for this method is settled up in setup() method."""
        try:
            args = self.callerArgs
            target_vc_path = self.callerArgs.id
            local_session_key = self.getSessionKey()

            to_vc_path = args.get("vc")
            username = args.get("username")
            password = args.get("password")
            pool_name = args.get("pool_name")
            collect_vc_logs = args.get("collect_vc_logs")
            host_include_list = args.get("host_include_list", "")
            host_exclude_list = args.get("host_exclude_list", "")

            target_vc_stanza = TAVMwareCollectionStanza.from_name(target_vc_path, "Splunk_TA_vmware_inframon", "nobody",
                                                                  session_key=local_session_key,
                                                                  host_path=local_host_path)

            to_vc_stanza = TAVMwareCollectionStanza.from_name(str(to_vc_path[0]), "Splunk_TA_vmware_inframon", "nobody",
                                                              session_key=local_session_key,

                                                              host_path=local_host_path)
            stored_cred = None
            if not target_vc_stanza:
                response = {"status": "invalid", "message": "No vc stanza with the given name exists.",
                            "credential_validation": False}
            elif to_vc_stanza and str(to_vc_path[0]) != target_vc_path:
                response = {"status": "invalid", "message": "Stanza with the given new name already exists.",
                            "credential_validation": False}

            else:
                # getting credentials of stanza currently being edited.
                logger.info("Getting credentials of stanza being edited.")
                stored_cred = SplunkStoredCredential.from_name(
                    SplunkStoredCredential.build_name(target_vc_path, target_vc_stanza.username),
                    app="Splunk_TA_vmware_inframon",
                    owner="nobody", host_path=local_host_path, session_key=local_session_key)

                response = ru.validate_vcenter(to_vc_path, username, password, pool_name, local_session_key, logger)

            if response['status'] == "invalid":
                raise RestError(400, str(response['message']))
            else:
                # Adding validation response
                conf_info["data"]["validate_vcenter_status"] = response["status"]
                conf_info["data"]["validate_vcenter_message"] = response["message"]

                to_vc_path = to_vc_path[0]
                username = username[0]
                password = password[0]
                pool_name = pool_name[0]
                collect_vc_logs = collect_vc_logs[0]

                # string to boolean convert
                collect_vc_logs = True if collect_vc_logs == 'true' else False

                # old password is saved for to disable input in case.
                old_password = ""
                if stored_cred:
                    old_password = stored_cred.clear_password

                old_pool_name = target_vc_stanza.pool_name
                vc_deleted = False
                vc_forwarder_deleted = False

                # first checking if stanza name is changed,
                # in that case old stanza will be deleted and new one will be created.

                if to_vc_path != target_vc_path:
                    logger.info(
                        "[pool={2}]vc path is changed, It will delete existing stanza with target={0} and create new stanza with path: {1}".format(
                            target_vc_path, to_vc_path, pool_name))

                    vc_deleted = ru.delete_vcenter_stanza(target_vc_path, local_session_key, logger)

                    ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)

                    vc_forwarder_deleted = ru.delete_vcenter_forwarder_stanza(target_vc_path, local_session_key,
                                                                              pool_name, logger)
                    to_vc_stanza = TAVMwareCollectionStanza("Splunk_TA_vmware_inframon", "nobody", to_vc_path,
                                                            sessionKey=local_session_key,
                                                            host_path=local_host_path)

                # here will be the code of disabling the inputs
                logger.info("delete status vc:{0} vc_forwarder:{1}".format(vc_deleted, vc_forwarder_deleted))
                if to_vc_stanza.username != username or old_password != password:
                    logger.info(
                        "[pool={0}]Credentials of vCenter:{1} changed.creating new credential stanza.".format(pool_name,
                                                                                                              to_vc_path))
                    # this is for deleting the old creds stanza when username/password is changed.
                    if not vc_deleted:
                        logger.info("Deleting credential stanza as old credentials changed.")
                        prev_cred = SplunkStoredCredential.from_name(
                            SplunkStoredCredential.build_name(target_vc_path, str(target_vc_stanza.username)),
                            app="Splunk_TA_vmware_inframon", owner="nobody",
                            host_path=local_host_path, session_key=local_session_key)
                        if prev_cred:
                            if not prev_cred.passive_delete():
                                logger.error("Could not delete outmoded credential it may linger")
                            else:
                                logger.info("Stanza of previous credentials deleted.")

                    new_cred = SplunkStoredCredential("Splunk_TA_vmware_inframon", "nobody", username,
                                                      sessionKey=local_session_key,
                                                      host_path=local_host_path)
                    logger.info("[pool={1}]cred stanza for vCenter:{0} created.".format(to_vc_path, pool_name))
                    new_cred.realm = to_vc_path
                    new_cred.password = password
                    new_cred.username = username

                    if not new_cred.passive_save():
                        logger.error(
                            "Failed to save credential for: realm={0} username={1}".format(to_vc_path, username))
                    else:
                        logger.info("New Credentials saved successfully for: realm={0} username={1}".format(to_vc_path,
                                                                                                            username))

                to_vc_stanza.target = [to_vc_path]
                to_vc_stanza.target_type = "vc"
                to_vc_stanza.username = username
                to_vc_stanza.pool_name = pool_name
                to_vc_stanza.credential_validation = response["credential_validation"]
                to_vc_stanza.last_connectivity_checked = response["last_connectivity_checked"]

                if isinstance(host_include_list, list):
                    host_include_list = host_include_list[0]
                if isinstance(host_exclude_list, list):
                    host_exclude_list = host_exclude_list[0]

                host_include_list = str(host_include_list).strip()
                host_exclude_list = str(host_exclude_list).strip()

                to_vc_stanza.managed_host_includelist = host_include_list if len(host_include_list) > 0 else 'None'
                to_vc_stanza.managed_host_excludelist = host_exclude_list if len(host_exclude_list) > 0 else 'None'

                if to_vc_stanza.passive_save():
                    ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)
                    if pool_name != old_pool_name:
                        logger.info(
                            "[pool={1}][pool={2}] Pool name is changed for vCenter: {0} from:{1} to:{2}".format(
                                to_vc_path, old_pool_name,
                                pool_name))
                        ru.set_conf_modification_time(old_pool_name, entity_type, local_session_key, logger)
                    conf_info["data"]["edit_vcenter_status"] = "200"
                    conf_info["data"]["edit_vcenter_message"] = "vCenter Stanza:{0} edited successfully.".format(to_vc_path)
                    logger.info("[pool={1}]vCenter Stanza:{0} edited successfully.".format(to_vc_path, pool_name))
                else:
                    logger.error("[pool={1}]Could not Edit vc_stanza={0}".format(str(to_vc_stanza), pool_name))
                    raise RestError(500, "Could not Edit vc_stanza={0}".format(str(to_vc_stanza)))

                # handling forwarder stuff
                if collect_vc_logs:
                    vc_splunk_uri = args.get("vc_splunk_uri")
                    vc_splunk_username = args.get("vc_splunk_username")
                    vc_splunk_password = args.get("vc_splunk_password")

                    forwarder_stanza = TAVMwareVCenterForwarderStanza.from_name(to_vc_path, "Splunk_TA_vmware_inframon",
                                                                                host_path=local_host_path,
                                                                                session_key=local_session_key)
                    spl_old_password = ""
                    spl_stored_cred = None

                    if not forwarder_stanza:
                        logger.info("No forwarder stanza found for vCenter:{0}, creating new one.".format(to_vc_path))
                        forwarder_stanza = TAVMwareVCenterForwarderStanza("Splunk_TA_vmware_inframon", "nobody", to_vc_path,
                                                                          sessionKey=local_session_key,
                                                                          host_path=local_host_path)
                    else:
                        # getting credentials of previous forwarder stanza,
                        # It could be needed for disable the inputs on vCenter splunk forwarder
                        logger.info(
                            "Getting credential stanza for forwarder:{0}. ".format(forwarder_stanza.host))
                        spl_stored_cred = SplunkStoredCredential.from_name(
                            SplunkStoredCredential.build_name(forwarder_stanza.host, forwarder_stanza.user),
                            app="Splunk_TA_vmware_inframon", owner="nobody", host_path=local_host_path,
                            session_key=local_session_key)

                        if spl_stored_cred:
                            spl_old_password = spl_stored_cred.clear_password

                    response = ru.validate_vcenter_forwarder(vc_splunk_uri, vc_splunk_username, vc_splunk_password,
                                                             local_session_key, logger)

                    # Adding forwarder validation response
                    conf_info["data"]["validate_forwarder_status"] = response["status"]
                    conf_info["data"]["validate_forwarder_message"] = response["message"]

                    if response["status"] != "invalid":
                        vc_splunk_uri = vc_splunk_uri[0]
                        vc_splunk_username = vc_splunk_username[0]
                        vc_splunk_password = vc_splunk_password[0]

                        if forwarder_stanza.user != vc_splunk_username or spl_old_password != vc_splunk_password:

                            if spl_stored_cred and spl_stored_cred.passive_delete():
                                logger.error("Stanza of prev credentials deleted.")
                            else:
                                logger.error("Previous credentials of forwarder stanza is not deleted. It may linger.")

                            forwarder_cred_stanza = SplunkStoredCredential("Splunk_TA_vmware_inframon", "nobody",
                                                                           vc_splunk_username,
                                                                           sessionKey=local_session_key,
                                                                           host_path=local_host_path)
                            forwarder_cred_stanza.realm = vc_splunk_uri
                            forwarder_cred_stanza.password = vc_splunk_password
                            forwarder_cred_stanza.username = vc_splunk_username

                            if not forwarder_cred_stanza.passive_save():
                                logger.error(
                                    "[pool={2}]Failed to save vc splunk forwarder credential: realm={0} username={1}".format(
                                        vc_splunk_uri, vc_splunk_username, pool_name))
                            else:
                                logger.info("[pool={1}]New cred stanza for forwarder:{0} saved.".format(vc_splunk_uri,
                                                                                                        pool_name))

                        # disabling inputs on previous vCenter forwarder when forwarder uri is changed.
                        if spl_old_password and forwarder_stanza.host != vc_splunk_uri:
                            ru.toggle_vc_inputs(forwarder_stanza.host, forwarder_stanza.user, spl_old_password,
                                                to_vc_path,
                                                local_session_key, pool_name, logger, disable=True)

                        forwarder_stanza.host = vc_splunk_uri
                        forwarder_stanza.user = vc_splunk_username
                        forwarder_stanza.collect_vc_logs = collect_vc_logs
                        forwarder_stanza.credential_validation = response["credential_validation"]
                        forwarder_stanza.addon_validation = response["addon_validation"]
                        ru.toggle_vc_inputs(vc_splunk_uri, vc_splunk_username, vc_splunk_password, to_vc_path,
                                            local_session_key, pool_name, logger, disable=False)

                        if not forwarder_stanza.passive_save():
                            conf_info["data"]["edit_forwarder_status"] = "500"
                            conf_info["data"]["edit_forwarder_message"] = "Problem editing the Forwarder stanza for vc={0}".format(to_vc_path)
                            logger.error(
                                "[pool=%s]problem saving the splunk forwarder stanza for vc=%s and vc_splunk_uri=%s, stanza will have to be regenerated.",
                                pool_name, to_vc_path, vc_splunk_uri)
                        else:
                            conf_info["data"]["edit_forwarder_status"] = "200"
                            conf_info["data"]["edit_forwarder_message"] = "Forwarder stanza for vc={0} edited successfully".format(to_vc_path)
                            logger.info(
                                "[pool={2}]Splunk forwarder stanza for vc={0} and vc_splunk_uri={1} saved successfully".format(
                                    to_vc_path, vc_splunk_uri, pool_name))
                else:
                    logger.info("Collect_vc_logs is false, deleting existing stanza.")
                    _ = ru.delete_vcenter_forwarder_stanza(to_vc_path, local_session_key, pool_name,
                                                           logger)

        except Exception as e:
            logger.exception(e)
            raise e


admin.init(ConfigApp, admin.CONTEXT_APP_AND_USER)
