#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import import_declare_test  # isort: skip # noqa: F401
import re
import socket
import sys

from snow_consts import GENERAL_EXCEPTION
from snow_utility import get_unique_id, add_ucc_error_logger
import snow_event_base as seb
import splunk.clilib.cli_common as com
import splunk.Intersplunk as si
from traceback import format_exc
from solnlib import utils


class SnowEventStream(seb.SnowEventBase):
    def __init__(self):
        # set session key
        self.sessionkey = self._set_session_key()

        self.settings = {}

        # read input
        self.res = self._set_events()
        # no events found
        if not self.res:
            sys.exit(0)

        self.splunk_host = ""

        # get account name
        for event in self.res:
            self.account = event.get("account", None)
            if self.account:
                break
        if not self.account:
            self._handle_error(
                'Field "account" is required by ServiceNow for creating events'
            )
        self.invocation_id = get_unique_id()
        super(SnowEventStream, self).__init__()
        # get default splunk_url
        self.splunk_url = self._set_splunk_url()

    def _get_events(self):
        return self.res

    def _set_events(self):
        return si.readResults(sys.stdin, self.settings, True)

    def _set_session_key(self):
        """
            When called as custom search script, splunkd feeds the following
            to the script as a single line
            'authString:<auth><userId>admin</userId><username>admin</username>\
                <authToken><32_character_long_uuid></authToken></auth>'
        """
        import urllib.parse

        session_key = sys.stdin.readline()
        m = re.search("authToken>(.+)</authToken", session_key)
        if m:
            session_key = m.group(1)
        session_key = urllib.parse.unquote(session_key.encode("ascii").decode("ascii"))
        session_key = session_key.encode().decode("utf-8")
        return session_key

    def _get_session_key(self):
        return self.sessionkey

    def _handle_error(self, msg="Failed to create ticket."):
        si.parseError(msg)

    def _set_splunk_url(self):
        try:
            config = com.getMergedConf("alert_actions") or {}
            hostname = config.get("email", {}).get("hostname", "") or ""
            # We get hostname in case of cloud environment as stack URL
            # hostname = https://snow-test-noah2.stg.splunkcloud.com:443
            pattern = r"https?:\/\/((?:\d{1,3}\.){3}\d{1,3}|\[[a-fA-F0-9:]+\]|[a-zA-Z0-9\.-]+)(:\d+)?(\/[^\s]*)?"
            match = re.search(pattern, hostname)
            host = ""
            # host = match.group(1)
            if match:
                host = match.group(1)
            if host:
                splunk_url = hostname
            else:
                KEY_WEB_SSL = "enableSplunkWebSSL"
                isWebSSL = utils.is_true(com.getWebConfKeyValue(KEY_WEB_SSL))
                webPrefix = isWebSSL and "https://" or "http://"
                port = com.getWebConfKeyValue("httpport")
                host = socket.gethostname()
                splunk_url = "{}{}:{}".format(webPrefix, host, port)
            self.logger.debug(
                f"Setting splunk_url as {splunk_url} and splunk_host as {host}."
            )
            self.splunk_host = host
            return "{}/app/{}/@go?sid={}".format(
                splunk_url,
                self.settings.get("namespace", ""),
                self.settings.get("sid", ""),
            )
        except Exception as exc:
            msg = (
                "Error occured while generating splunk_url. Setting splunk_url to localhost. "
                "Error: {}".format(format_exc)
            )
            add_ucc_error_logger(
                logger=self.logger,
                logger_type=GENERAL_EXCEPTION,
                exception=exc,
                msg_before=msg,
            )
            return "http://localhost:8000/app/{}/@go?sid={}".format(
                self.settings.get("namespace", ""), self.settings.get("sid", "")
            )

    def _prepare_data(self, event):
        event.update({"url": self.splunk_url})
        event.update({"hostname": self.splunk_host})
        return super(SnowEventStream, self)._prepare_data(event)


def main():
    handler = SnowEventStream()
    handler.handle()


if __name__ == "__main__":
    main()
