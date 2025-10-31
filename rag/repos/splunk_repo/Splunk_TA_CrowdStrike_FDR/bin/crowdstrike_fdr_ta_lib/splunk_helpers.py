#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import traceback

import solnlib
from solnlib.credentials import CredentialManager, CredentialNotExistException
from solnlib.conf_manager import (
    ConfManager,
    ConfStanzaNotExistException,
    ConfManagerException,
)
from splunklib import binding, client
from splunklib import modularinput as smi

from .constants import SESSION_KEY, SERVER_URI, APP
from .checkpointer import Checkpointer
from .logger_adapter import CSLoggerAdapter
from typing import Optional, Tuple, Callable, Dict, Any

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("splunk_helpers")
)


class ConfHelper:
    def __init__(self, conf_name, app_name, session_key):
        self.conf_name = conf_name
        self.app_name = app_name
        self.session_key = session_key

    def stanza_passwords(self, stanza: str) -> Dict[str, Any]:
        input_type, input_name = stanza.split("://")
        realm = f"__REST_CREDENTIAL__#{self.app_name}#data/inputs/{input_type}"
        creds = CredentialManager(
            session_key=self.session_key, app=self.app_name, realm=realm
        )
        return json.loads(creds.get_password(input_name))

    def __load(
        self, stanza: Optional[str] = None, silent: bool = False
    ) -> Dict[str, Any]:
        try:
            cfm = ConfManager(
                self.session_key,
                self.app_name,
                realm="__REST_CREDENTIAL__#{}#configs/conf-{}".format(
                    self.app_name, self.conf_name
                ),
            )
            try:
                conf = cfm.get_conf(self.conf_name, refresh=True)
                if stanza:
                    return conf.get(stanza, only_current_app=True)
                return conf.get_all(only_current_app=True)
            except ConfStanzaNotExistException as e:
                if not silent:
                    logger.warning(
                        f"No {self.conf_name} configuration information found for stanza {stanza}: {e}"
                    )
            except ConfManagerException as e:
                logger.warning(
                    f"No {self.conf_name} configuration information found: {e}"
                )
        except Exception as e:
            msg = f"Failed to access {self.conf_name} config file: {e}"
            tb = " ---> ".join(traceback.format_exc().split("\n"))
            solnlib.log.log_permission_error(logger, e, msg_before=f"{msg} {tb}")
            raise

        return {}

    def all(self) -> Dict[str, Any]:
        return self.__load()

    def stanza(self, stanza: str) -> Dict[str, Any]:
        return self.__load(stanza=stanza)


def split_single_instance_conf(
    script: smi.Script,
) -> Optional[Tuple[str, Dict[str, Any], str]]:
    scheme = script.get_scheme()
    assert scheme.use_single_instance is False

    inputs = getattr(script, "_input_definition")
    assert inputs

    input_items = []
    for input_name, input_item in inputs.inputs.items():
        input_item["input_stanza"] = input_name
        input_items.append((input_name, input_item))

    if not input_items:
        logger.info(f"{scheme.title}: no configuration provided: {input_items}")
        return

    input_stanza, input_conf = input_items[0]

    return input_stanza, input_conf, inputs.metadata


def use_conf(conf_name: str, alias: Optional[str] = None) -> Callable:
    def use_conf_decorator(fn: Callable) -> Optional[Callable]:
        def use_conf_wrapper(self, *args: Any, **kwargs: Any) -> Optional[Callable]:
            try:
                _, input_conf, metadata = split_single_instance_conf(self)

                helper_conf = dict(
                    conf_name=conf_name,
                    app_name=input_conf[APP],
                    session_key=metadata[SESSION_KEY],
                )

                if isinstance(alias, str):
                    if not alias.isidentifier():
                        raise NameError(
                            f"Argument alias='{alias}' is not a valid name for a variable."
                        )
                    setattr(self, alias, ConfHelper(**helper_conf))
                else:
                    if not conf_name.isidentifier():
                        raise NameError(
                            f"'{conf_name}' is not a valid name for variable. Use 'alias' decorator argument to give alternative name that complies with variable syntax"
                        )
                    setattr(self, conf_name, ConfHelper(**helper_conf))

                return fn(self, *args, **kwargs)
            except Exception as e:
                msg = f"Unexpected error in use_conf decorator: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger, e, "use_conf decorator", msg_before=f"{msg} {tb}"
                )
                raise

        return use_conf_wrapper

    return use_conf_decorator


def use_checkpointer(collection_name: str, alias: Optional[str] = None) -> Callable:
    def use_checkpointer_decorator(fn: Callable) -> Callable:
        def use_checkpointer_wrapper(self, *args: Any, **kwargs: Any) -> Callable:
            try:
                _, input_conf, metadata = split_single_instance_conf(self)

                kvstore_conf = dict(
                    app=input_conf[APP],
                    token=metadata[SESSION_KEY],
                    server_uri=metadata[SERVER_URI],
                    collection_name=collection_name,
                )

                if isinstance(alias, str):
                    if not alias.isidentifier():
                        raise NameError(
                            f"Argument alias='{alias}' is not a valid name for a variable."
                        )
                    setattr(self, alias, Checkpointer(**kvstore_conf))
                else:
                    if not collection_name.isidentifier():
                        raise NameError(
                            f"'{collection_name}' is not a valid name for variable. Use 'alias' decorator argument to give alternative name that complies with variable syntax"
                        )
                    setattr(self, collection_name, Checkpointer(**kvstore_conf))

                return fn(self, *args, **kwargs)
            except Exception as e:
                msg = f"Unexpected error in use_checkpointer decorator: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger, e, "Checkpointer Error", msg_before=f"{msg} {tb}"
                )
                raise

        return use_checkpointer_wrapper

    return use_checkpointer_decorator


def unpack_single_instance_input_conf(resolve_passwords: bool = False) -> Callable:
    def unpack_single_instance_input_conf_decorator(fn: Callable) -> Callable:
        def unpack_single_instance_input_conf_wrapper(
            self, *args: Any, **kwargs: Any
        ) -> Optional[Callable]:
            try:
                scheme = self.get_scheme()
                assert (
                    scheme.use_single_instance is False
                ), "modinput scheme use_single_instance should be False to work with this decorator"

                inputs = getattr(self, "_input_definition")
                assert (
                    inputs
                ), "modinput script instance should have non empty _input_definition attribute"

                input_items = []
                for input_name, input_item in inputs.inputs.items():
                    input_items.append((input_name, input_item))

                if not input_items:
                    logger.info(
                        f"{self.__class__.__name__}.{fn.__name__}: no configuration provided."
                    )
                    return

                input_stanza, input_conf = input_items[0]

                if resolve_passwords:
                    app_name = input_conf[APP]
                    session_key = inputs.metadata[SESSION_KEY]

                    input_type, input_name = input_stanza.split("://")
                    realm = f"__REST_CREDENTIAL__#{app_name}#data/inputs/{input_type}"
                    creds = CredentialManager(
                        session_key=session_key, app=app_name, realm=realm
                    )

                    passwords = json.loads(creds.get_password(input_name))
                    input_conf.update(passwords)
                    logger.info(f"Successfully retrieved passwords for {input_stanza}")

                kwargs["stanza"] = input_stanza
                kwargs["config"] = input_conf
                kwargs["metadata"] = inputs.metadata

                return fn(self, *args, **kwargs)
            except Exception as e:
                msg = f"Unexpected error in use_checkpointer decorator: {e}"
                tb = " ---> ".join(traceback.format_exc().split("\n"))
                solnlib.log.log_exception(
                    logger, e, "Checkpointer Error", msg_before=f"{msg} {tb}"
                )
                raise

        return unpack_single_instance_input_conf_wrapper

    return unpack_single_instance_input_conf_decorator


class CSScriptHelper:
    def get_app_stanza_passwords(self, app_name: str, stanza: str) -> Dict[str, Any]:
        input_type, input_name = stanza.split("://")
        realm = f"__REST_CREDENTIAL__#{app_name}#data/inputs/{input_type}"
        session_key = getattr(self, "_input_definition").metadata[SESSION_KEY]
        creds = CredentialManager(session_key=session_key, app=app_name, realm=realm)
        return json.loads(creds.get_password(input_name))

    def load_config(
        self,
        app_name: str,
        conf_name: str,
        conf_friendly_name: str,
        session_key: Optional[str] = None,
        stanza: Optional[str] = None,
        silent: bool = False,
    ) -> Dict[str, Any]:
        if not session_key:
            session_key = getattr(self, "_input_definition").metadata[SESSION_KEY]

        try:
            cfm = ConfManager(
                session_key,
                app_name,
                realm="__REST_CREDENTIAL__#{}#configs/conf-{}".format(
                    app_name, conf_name
                ),
            )
            try:
                conf = cfm.get_conf(conf_name, refresh=True)
                if stanza:
                    return conf.get(stanza, only_current_app=True)
                return conf.get_all(only_current_app=True)
            except ConfStanzaNotExistException as e:
                if not silent:
                    logger.warning(
                        f"No {conf_friendly_name} configuration information found for stanza {stanza}: {e}"
                    )
            except ConfManagerException as e:
                logger.warning(
                    f"No {conf_friendly_name} configuration information found: {e}"
                )
        except Exception as e:
            msg = f"Failed to access {conf_friendly_name} config file: {e}"
            tb = " ---> ".join(traceback.format_exc().split("\n"))
            solnlib.log.log_permission_error(logger, e, msg_before=f"{msg} {tb}")
        return {}


def validate_connection_info(connection_info: Dict[str, Any]) -> bool:
    try:
        client.connect(**connection_info)
    except binding.AuthenticationError:
        return False
    except Exception as e:
        msg = f"validate_connection_info unexpected error: {e}"
        tb = " ---> ".join(traceback.format_exc().split("\n"))
        solnlib.log.log_connection_error(logger, e, msg_before=f"{msg} {tb}")
        msg = (
            "Splunk connection details validation failed for "
            "{host}:{port}, please check TA logs for details"
        )
        raise Exception(msg.format(**connection_info)) from e

    return True
