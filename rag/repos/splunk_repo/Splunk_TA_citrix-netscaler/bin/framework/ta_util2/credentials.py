#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

"""
Handles credentials related stuff
"""

import logging
from urllib import response
import urllib.parse

import defusedxml.minidom as xdm
import ta_util2.log_files as log_files
import ta_util2.rest as rest
import ta_util2.xml_dom_parser as xdp

_LOGGER = logging.getLogger(log_files.ta_util_conf)


class CredentialManager:
    """
    Credential related interfaces
    """

    _log_template = "Failed to %s user credential for %s, app=%s"

    def __init__(self, session_key, splunkd_uri="https://localhost:8089"):
        self._session_key = session_key
        self._splunkd_uri = splunkd_uri

    @staticmethod
    def get_session_key(username, password, splunkd_uri="https://localhost:8089"):
        """
        Get session key by using login username and passwrod
        @return: session_key if successful, None if failed
        """

        eid = "".join((splunkd_uri, "/services/auth/login"))
        postargs = {
            "username": username,
            "password": password,
        }

        response = rest.splunkd_request(eid, None, method="POST", data=postargs)

        if response and response.status_code not in (200, 201):
            return None

        xml_obj = xdm.parseString(response.content)
        session_nodes = xml_obj.getElementsByTagName("sessionKey")
        return session_nodes[0].firstChild.nodeValue

    def update(self, realm, user, password, app, owner="nobody"):
        """
        Update the password for a user and realm.
        @return: True if successful, False if failure
        """

        self.delete(realm, user, app, owner)
        return self.create(realm, user, password, app, owner)

    def create(self, realm, user, password, app, owner="nobody"):
        """
        Create a new stored credential.
        """

        payload = {
            "name": user,
            "password": password,
            "realm": realm,
        }

        endpoint = self._get_endpoint(realm, user, app, owner)
        response = rest.splunkd_request(
            endpoint, self._session_key, method="POST", data=payload
        )
        if response and response.status_code in (200, 201):
            return True
        return False

    def delete(self, realm, user, app, owner="nobody"):
        """
        Delete the encrypted entry
        @return: True for success, False for failure
        """

        endpoint = self._get_endpoint(realm, user, app, owner)
        response = rest.splunkd_request(endpoint, self._session_key, method="DELETE")
        if response and response.status_code in (200, 201):
            return True
        return False

    def get_all_passwords(self):
        """
        @return: a list of dict when successful, None when failed.
        the dict at least contains
        {
            "realm": xxx,
            "username": yyy,
            "clear_password": zzz,
        }
        """

        endpoint = "{}/services/storage/passwords?count=0&offset=0".format(
            self._splunkd_uri
        )
        response = rest.splunkd_request(endpoint, self._session_key, method="GET")
        if response and response.status_code in (200, 201) and response.content:
            return xdp.parse_conf_xml_dom(response.content)

    def get_clear_password(self, realm, user, app, owner="nobody"):
        """
        @return: clear password for specified realm and user
        """

        return self._get_credentials(realm, user, app, owner, "clear_password")

    def get_encrypted_password(self, realm, user, app, owner="nobody"):
        """
        @return: encyrpted password for specified realm and user
        """

        return self._get_credentials(realm, user, app, owner, "encr_password")

    def _get_credentials(self, realm, user, app, owner, prop):
        """
        @return: clear or encrypted password for specified realm, user
        """

        endpoint = self._get_endpoint(realm, user, app, owner)
        response = rest.splunkd_request(endpoint, self._session_key, method="GET")
        if response and response.status_code in (200, 201) and response.content:
            password = xdp.parse_conf_xml_dom(response.content)[0]
            return password[prop]
        return None

    @staticmethod
    def _build_name(realm, user):
        return urllib.parse.quote(
            "".join(
                (
                    CredentialManager._escape_string(realm),
                    ":",
                    CredentialManager._escape_string(user),
                    ":",
                )
            )
        )

    @staticmethod
    def _escape_string(string_to_escape):
        """
        Splunk secure credential storage actually requires a custom style of
        escaped string where all the :'s are escaped by a single \.  # noqa
        But don't escape the control : in the stanza name.
        """

        return string_to_escape.replace(":", "\\:").replace("/", "%2F")

    def _get_endpoint(self, realm, user, app, owner):
        if not owner:
            owner = "-"

        if not app:
            app = "-"

        realm_user = self._build_name(realm, user)
        rest_endpoint = "{}/servicesNS/{}/{}/storage/passwords/{}".format(
            self._splunkd_uri, owner, app, realm_user
        )
        return rest_endpoint
