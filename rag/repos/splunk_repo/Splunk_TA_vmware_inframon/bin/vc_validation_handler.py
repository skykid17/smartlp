# splunk sdk imports
import splunk.admin as admin
import splunk
import sys
from splunk.clilib.bundle_paths import make_splunkhome_path

# importing rest_utility
from rest_utility import setup_logger, RestError
import rest_utility as ru

# TA and SA Imports
sys.path.append(make_splunkhome_path(['etc', 'apps', 'SA-Hydra-inframon', 'bin']))
sys.path.append(make_splunkhome_path(['etc', 'apps', 'Splunk_TA_vmware_inframon', 'bin']))

# models import
from hydra_inframon.models import SplunkStoredCredential
from ta_vmware_inframon.models import TAVMwareCollectionStanza

# defining global constants
logger = setup_logger(log_name="vcenter_configuration.log",
                      logger_name="vcenter_configuration")
local_host_path = splunk.mergeHostPath()
entity_type = "collection"

REQ_ARGS_LIST = ['vc', 'check_connection_only']
OPT_ARGS_LIST = ['username', 'password']


class ConfigApp(admin.MConfigHandler):

    def setup(self):
        """This method is called at every request before handle method is called. This is used for adding optional and required arguments for particular requests."""
        if self.requestedAction == admin.ACTION_LIST:
            for arg in REQ_ARGS_LIST:
                self.supportedArgs.addReqArg(arg)

            for arg in OPT_ARGS_LIST:
                self.supportedArgs.addOptArg(arg)

    def handleList(self, conf_info):
        """This method is called at GET request on vc_validation. It expects @vc - vCenter stanza name to validate"""
        try:
            args = self.callerArgs
            vc_path = args.get("vc")
            vc_path = vc_path[0]
            check_connection_flag = args.get("check_connection_only")
            check_connection_flag = check_connection_flag[0]
            local_session_key = self.getSessionKey()

            if not check_connection_flag is None:
                check_connection_flag = True if check_connection_flag == 'true' else False
            else:
                response = {"status": "invalid", "message": "check_connection_only parameter is not valid."}
                raise RestError(400, str(response["message"]))

            if check_connection_flag:
                username = args.get("username")
                password = args.get("password")

                response = ru.validate_vcenter(vc_path, username, password, None, local_session_key, logger, check_connection_only=True)
                
                if response['status'] == "invalid":
                    raise RestError(400, str(response['message']))

                conf_info["data"]["status"] = response["status"]
                conf_info["data"]["message"] = response["message"]
                
            else:
                vc_stanza = TAVMwareCollectionStanza.from_name(vc_path, "Splunk_TA_vmware_inframon", "nobody",
                                                            session_key=local_session_key,
                                                            host_path=local_host_path)

                if vc_stanza:
                    stored_cred = SplunkStoredCredential.from_name(
                        SplunkStoredCredential.build_name(vc_path, vc_stanza.username),
                        app="Splunk_TA_vmware_inframon",
                        owner="nobody", host_path=local_host_path, session_key=local_session_key)

                    password = stored_cred.clear_password
                    username = vc_stanza.username
                    pool_name = vc_stanza.pool_name
                    response = ru.validate_vcenter(vc_path, username, password, pool_name, local_session_key, logger)

                    vc_stanza.last_connectivity_checked = response["last_connectivity_checked"]
                    validation_modified = False

                    if vc_stanza.credential_validation != response["credential_validation"]:
                        validation_modified = True

                    vc_stanza.credential_validation = response["credential_validation"]

                    if not vc_stanza.passive_save():
                        logger.error(
                            "[pool={1}]Failed to update validation status for vc stanza:{0}".format(vc_path,
                                                                                                    pool_name))
                    elif validation_modified:
                        logger.info(
                            "[pool={1}]Successfully updated validation status time for vc stanza:{0} after validation".format(
                                vc_path, pool_name))
                        ru.set_conf_modification_time(pool_name, entity_type, local_session_key, logger)

                    conf_info["data"]["status"] = response["status"]
                    conf_info["data"]["message"] = response["message"]
                    conf_info["data"]["last_connectivity_checked"] = response["last_connectivity_checked"].strftime(
                        "%Y-%m-%dT%H:%M:%S.%f")

                else:
                    logger.error("Stanza for vc:{0} not found while validating.".format(vc_path))
                    conf_info["data"]["status"] = "404"
                    conf_info["data"]["message"] = "Stanza not found."
        except Exception as e:
            logger.exception("Exception occurred:" + str(e))
            raise e


admin.init(ConfigApp, admin.CONTEXT_APP_AND_USER)
