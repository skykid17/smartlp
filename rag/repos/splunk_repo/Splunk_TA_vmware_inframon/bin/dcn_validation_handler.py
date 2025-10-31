# splunk sdk imports
import splunk.admin as admin
import splunk
import sys
from splunk.clilib.bundle_paths import make_splunkhome_path

# importing rest_utility
from rest_utility import setup_logger
import rest_utility as ru

# SA imports
sys.path.append(make_splunkhome_path(['etc', 'apps', 'SA-Hydra-inframon', 'bin']))
from hydra_inframon.models import HydraNodeStanza, SplunkStoredCredential

# defining global constants
logger = setup_logger(log_name="dcn_configuration.log",
                      logger_name="dcn_configuration")
local_host_path = splunk.mergeHostPath()
entity_type = "node"

REQUIRED_ARGS_LIST = ['node']


class ConfigApp(admin.MConfigHandler):

    def setup(self):
        """This method is called at every request before handle method is called.
        This is used for adding optional and required arguments for particular requests."""
        if self.requestedAction == admin.ACTION_LIST:
            for arg in REQUIRED_ARGS_LIST:
                self.supportedArgs.addOptArg(arg)

    def handleList(self, conf_info):
        """When GET request is done on the endpoint dcn_validation, this method is called,
        It returns the validation status of given DCN"""
        try:
            args = self.callerArgs
            local_session_key = self.getSessionKey()
            node_path = args.get("node")
            node_path = node_path[0]

            node_stanza = HydraNodeStanza.from_name(
                node_path, "Splunk_TA_vmware_inframon", host_path=local_host_path, session_key=local_session_key)

            if node_stanza:
                stored_cred = SplunkStoredCredential.from_name(
                    SplunkStoredCredential.build_name(node_stanza.host, node_stanza.user), app="Splunk_TA_vmware_inframon",
                    owner="nobody", host_path=local_host_path, session_key=local_session_key)

                password = stored_cred.clear_password
                username = node_stanza.user
                heads = node_stanza.heads
                pool_name = node_stanza.pool_name

                response = ru.validate_dcn(node_path, username, password, str(heads), pool_name, local_session_key,
                                           logger)

                validation_modified = False
                if node_stanza.credential_validation != response['credential_validation'] or \
                        node_stanza.addon_validation != response['addon_validation']:
                    validation_modified = True

                node_stanza.credential_validation = response['credential_validation']
                node_stanza.addon_validation = response['addon_validation']
                node_stanza.last_connectivity_checked = response["last_connectivity_checked"]

                if not node_stanza.passive_save():
                    logger.error("[pool={0}]Failed to update validation status for node stanza:{1}".format(pool_name, node_path))
                elif validation_modified:
                    logger.info(
                        "[pool={1}]Successfully updated connectivity checked time for dcn stanza:{0} after validation".format(
                            node_path, pool_name))
                    ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)

                conf_info["data"]["status"] = response["status"]
                conf_info["data"]["message"] = response["message"]
                conf_info["data"]["last_connectivity_checked"] = response["last_connectivity_checked"].strftime(
                    "%Y-%m-%dT%H:%M:%S.%f")
            else:
                conf_info["data"]["status"] = "404"
                conf_info["data"]["message"] = "Stanza not found."
                logger.error("Stanza for dcn:{0} not found while validating.".format(node_path))
        except Exception as e:
            logger.exception(e)
            raise e


admin.init(ConfigApp, admin.CONTEXT_APP_AND_USER)
