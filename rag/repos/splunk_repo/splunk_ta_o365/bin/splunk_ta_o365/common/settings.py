#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import urllib.parse
import requests
import time
from splunksdc import logging
from splunksdc.config import (
    StanzaParser,
    StringField,
    BooleanField,
    LogLevelField,
)
from splunk_ta_o365 import set_log_level
from solnlib import conf_manager

APP_NAME = "splunk_ta_o365"


logger = logging.get_module_logger()


class SSLCert:
    """
    This class is use to read the splunk_ta_o365_ssl_cert.
    """

    @classmethod
    def load(cls, session_key: str):
        """Function to load sslCertSettings stanza from splunk_ta_o365_ssl_cert

        Args:
            session_key(str): Splunk Session Key

        Returns:
            SSLCert: Object of SSLCert
        """
        conf_name = "splunk_ta_o365_ssl_cert"
        stanza = "sslCertSettings"
        cfm = conf_manager.ConfManager(session_key, APP_NAME)
        conf = cfm.get_conf(conf_name)
        stanza_content = conf.get(stanza_name=stanza, only_current_app=True)
        return cls(stanza_content)

    def __init__(self, settings: dict):
        self._settings = settings

    def get_ca_cert_path(self):
        """Get ca_certs_path values from self._settings object

        Returns:
            str: value of ca_certs_path
        """
        return self._settings.get("ca_certs_path")


class Proxy:
    """
    This class is use to load proxy settings.
    """

    @staticmethod
    def _wipe(settings: dict):
        """Remove the password from settings and return the proxy sesstings

        Args:
            settings (dict): Proxy settings dict

        Returns:
            dict: Proxy dict without password
        """
        params = vars(settings).copy()
        del params["password"]
        return params

    @classmethod
    def load(cls, session_key: str):
        """Function to load proxy settings from conf file.

        Args:
            session_key (str): Splunk session key

        Returns:
            Proxy: Object of Proxy
        """
        conf_name = "splunk_ta_o365_settings"
        stanza = "proxy"
        retry = 0

        while True:
            cfm = conf_manager.ConfManager(
                session_key,
                APP_NAME,
                realm=f"__REST_CREDENTIAL__#{APP_NAME}#configs/conf-{conf_name}",
            )
            conf = cfm.get_conf(conf_name)
            stanza_content = conf.get(stanza_name=stanza, only_current_app=True)
            parser = StanzaParser(
                [
                    BooleanField("proxy_enabled", rename="enabled"),
                    StringField("host"),
                    StringField("port"),
                    StringField("username"),
                    StringField("password"),
                    BooleanField("is_conf_migrated"),
                ]
            )
            settings = parser.parse(stanza_content)

            # checking host if proxy is configured or not, if not, then skip checking conf_migrated flag
            if not settings.host or settings.is_conf_migrated:
                break
            if retry == 4:
                break
            retry += 1
            logger.info("Waiting for Proxy Conf migration to be completed")
            time.sleep(60)

        logger.info("Load proxy settings success.", **cls._wipe(settings))
        return cls(settings, session_key)

    def __init__(self, settings: dict, session_key: str):
        self._settings = settings
        self._session_key = session_key

    def _make_url(self, scheme: str):
        """Function to make url for proxy settings

        Args:
            scheme (str): type of proxy. http or https

        Returns:
            str: Proxt URL
        """
        settings = self._settings
        endpoint = f"{settings.host}:{settings.port}"
        auth = None
        if settings.username and len(settings.username) > 0:
            auth = urllib.parse.quote(settings.username.encode(), safe="")
            if settings.password and len(settings.password) > 0:
                auth += ":"
                auth += urllib.parse.quote(settings.password.encode(), safe="")

        if auth:
            endpoint = auth + "@" + endpoint

        url = scheme + "://" + endpoint
        return url

    def create_requests_session(self):
        """Function to create request session to pull data for the Add-on

        Returns:
            session: Session object.
        """
        ca_certs_path = SSLCert.load(self._session_key).get_ca_cert_path()
        session = requests.Session()
        if self._settings.enabled:
            server_uri = self._make_url("http")
            session.proxies.update({"http": server_uri, "https": server_uri})
            if ca_certs_path:
                session.verify = ca_certs_path
        return session


class Logging:
    @classmethod
    def load(cls, config):
        content = config.load("splunk_ta_o365_settings", stanza="logging")
        parser = StanzaParser([LogLevelField("log_level", default="WARNING")])
        settings = parser.parse(content)
        return cls(settings)

    def __init__(self, settings):
        self._settings = settings

    def apply(self):
        set_log_level(self._settings.log_level)
