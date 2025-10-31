#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
# flake8: noqa: E402
from future import standard_library

standard_library.install_aliases()
import ipaddress
import urllib.parse
from builtins import object

from splunk_ta_gcp import set_log_level
from splunksdc import log as logging
from splunksdc.config import BooleanField, LogLevelField, StanzaParser, StringField

logger = logging.get_module_logger()


def is_host_ipv6(host: str):
    """Function to validate whether host value is ipv6 or not

    Args:
        host (str): host value

    Returns:
        boolean: True or False
    """
    try:
        if ipaddress.IPv6Address(host):
            return True
    except ipaddress.AddressValueError:
        return False


class Settings(object):
    @classmethod
    def load(cls, config):
        path = "splunk_ta_google/google_settings"
        content = config.load(path, stanza="global_settings", virtual=True)
        parser = StanzaParser([LogLevelField("log_level")])
        general = parser.parse(content)
        content = config.load(
            path, stanza="proxy_settings", virtual=True, clear_cred=True
        )
        parser = StanzaParser(
            [
                BooleanField("proxy_enabled", default=False, rename="enabled"),
                StringField("proxy_type", rename="scheme", default="http"),
                BooleanField("proxy_rdns", rename="rdns", default=False),
                StringField("proxy_url", rename="host"),
                StringField("proxy_port", rename="port"),
                StringField("proxy_username", rename="username"),
                StringField("proxy_password", rename="password"),
            ]
        )
        proxy = parser.parse(content)
        return cls(general, proxy)

    def __init__(self, general, proxy):
        self._general = general
        self._proxy = proxy
        self.is_ipv6 = is_host_ipv6(proxy.host)

    @property
    def proxy(self):
        return self._proxy

    def setup_log_level(self):
        set_log_level(self._general.log_level)

    def make_proxy_uri(self):
        proxy = self._proxy
        if not proxy.enabled:
            return ""

        scheme = proxy.scheme
        if scheme not in ["http", "socks5", "socks5h"]:
            logger.warning("Proxy scheme is invalid", scheme=scheme)
            return ""

        if proxy.rdns:
            if scheme == "socks5":
                scheme = "socks5h"

        if self.is_ipv6:
            endpoint = "[{host}]:{port}".format(host=proxy.host, port=proxy.port)
        else:
            endpoint = "{host}:{port}".format(host=proxy.host, port=proxy.port)

        auth = None
        if proxy.username and len(proxy.username) > 0:
            auth = urllib.parse.quote(proxy.username.encode(), safe="")
            if proxy.password and len(proxy.password) > 0:
                auth += ":"
                auth += urllib.parse.quote(proxy.password.encode(), safe="")

        if auth:
            endpoint = auth + "@" + endpoint

        url = scheme + "://" + endpoint
        return url
