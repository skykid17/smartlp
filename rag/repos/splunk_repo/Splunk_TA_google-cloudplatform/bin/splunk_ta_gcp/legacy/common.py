# pylint: skip-file
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import print_function

import datetime
import os.path as op
import sys
import time
import json
from builtins import range

import pytz
import splunk_ta_gcp.legacy.consts as ggc
from splunk_ta_gcp.common.credentials import CredentialFactory
import splunktalib.common.util as scutil
import splunktalib.file_monitor as fm
import splunktalib.modinput as mi
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient import discovery
from httplib2 import Http, ProxyInfo, socks
from pyrfc3339 import parse as rfc3339_parse
from splunksdc import logging
from splunktalib.common.util import is_true
import json

import splunk_ta_gcp.legacy.config as gconf
from splunk_ta_gcp.common.settings import is_host_ipv6
from splunk_ta_gcp import set_log_level
import requests
import os
from solnlib.splunkenv import get_splunk_host_info
from solnlib import log

LOG_FORMAT = (
    "%(asctime)s +0000 log_level=%(levelname)s, pid=%(process)d, tid=%(threadName)s, "
    "file=%(filename)s, func_name=%(funcName)s, code_line_no=%(lineno)d | %(message)s"
)


NO_PROXY = "localhost,127.0.0.1,0.0.0.0,localaddress"

_EPOCH_TIME = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)


def validate_config():
    """
    Validate inputs.conf
    """

    return 0


def usage():
    """
    Print usage of this binary
    """

    hlp = "%s --scheme|--validate-arguments|-h"
    print(hlp % sys.argv[0], file=sys.stderr)
    sys.exit(1)


def print_scheme(title, description):
    """
    Feed splunkd the TA's scheme
    """

    print(
        """
    <scheme>
    <title>{title}</title>
    <description>{description}</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>
    <use_single_instance>true</use_single_instance>
    <endpoint>
      <args>
        <arg name="name">
          <title>Unique name which identifies this data input</title>
        </arg>
        <arg name="placeholder">
          <title>placeholder</title>
        </arg>
      </args>
    </endpoint>
    </scheme>""".format(
            title=title, description=description
        )
    )


def main(scheme_printer, run):
    args = sys.argv
    if len(args) > 1:
        if args[1] == "--scheme":
            scheme_printer()
        elif args[1] == "--validate-arguments":
            sys.exit(validate_config())
        elif args[1] in ("-h", "--h", "--help"):
            usage()
        else:
            usage()
    else:
        # sleep 5 seconds here for KV store ready
        time.sleep(5)
        run()


def setup_signal_handler(loader, logger):
    """
    Setup signal handlers
    @data_loader: data_loader.DataLoader instance
    """

    def _handle_exit(signum, frame):
        logger.info("Exit signal received, exiting...")
        loader.tear_down()

    scutil.handle_tear_down_signals(_handle_exit)


def get_file_change_handler(loader, logger):
    def reload_and_exit(changed_files):
        logger.info("Conf file(s)=%s changed, exiting...", changed_files)
        loader.tear_down()

    return reload_and_exit


def get_configs(ConfCls, modinput_name, logger):
    conf = ConfCls()
    tasks = conf.get_tasks()

    if not tasks:
        logger.debug(
            "Data collection for %s is not fully configured. "
            "Do nothing and quit the TA.",
            modinput_name,
        )
        return None, None

    return conf.metas, tasks


def get_modinput_configs():
    modinput = sys.stdin.read()
    return mi.parse_modinput_configs(modinput)


def sleep_until(interval, condition):
    """
    :interval: integer
    :condition: callable to check if need break the sleep loop
    :return: True when during sleeping condition is met, otherwise False
    """

    for _ in range(interval):
        time.sleep(1)
        if condition():
            return True
    return False


def get_app_path(absolute_path):
    marker = op.join(op.sep, "etc", "apps")
    start = absolute_path.rfind(marker)
    if start == -1:
        start = 0
    end = absolute_path.find("bin", start)
    if end == -1:
        return None
    # strip the tail
    end = end - 1
    path = absolute_path[:end]
    return path


def get_conf_files(files):
    cur_dir = get_app_path(op.abspath(__file__))
    all_files = []
    all_confs = [ggc.myta_global_settings_conf, ggc.myta_cred_conf] + files
    for f in all_confs:
        all_files.append(op.join(cur_dir, "local", f))
    return all_files


def create_conf_monitor(callback, files):
    return fm.FileMonitor(callback, get_conf_files(files))


def rfc3339_to_seconds(rfc3339_datetime_str):
    timestamp = rfc3339_parse(rfc3339_datetime_str)
    return (timestamp - _EPOCH_TIME).total_seconds()


def fqrn(resource_type, project, resource):
    """Return a fully qualified resource name for Cloud Pub/Sub."""
    return "projects/{}/{}/{}".format(project, resource_type, resource)


def create_google_client(config):
    """
    :param: config
    {
        "proxy_url": xxx,
        "proxy_port": xxx,
        "proxy_username": xxx,
        "proxy_password": xxx,
        "proxy_rdns": xxx,
        "proxy_type": xxx,
        "google_credentials": xxx,
        "google_project": xxx,
        "google_subscriptions": xxx,
        "scopes": xxx,
        "service_name": xxx,
        "version": xxx,
    }
    """

    http = get_http_auth_cred(config)
    return discovery.build(
        config["service_name"], config["version"], http=http, cache_discovery=False
    )


def get_http_auth_cred(config):
    """
    Get credential object and authorise it with http proxy
    """
    credential = CredentialFactory.get_credential(config)
    return authorise_http_credential(config, credential)


def authorise_http_credential(config, credential):
    """
    Authorise the credential with proxy and retrun http
    """
    http = build_http_connection(config, timeout=config.get("pulling_interval", 120))
    return AuthorizedHttp(credential, http=http)


def build_http_connection(config, timeout=120, disable_ssl_validation=False):
    """
    :config: dict like, proxy and account information are in the following
             format {
                 "username": xx,
                 "password": yy,
                 "proxy_url": zz,
                 "proxy_port": aa,
                 "proxy_username": bb,
                 "proxy_password": cc,
                 "proxy_type": http,socks5,
                 "proxy_rdns": 0 or 1,
             }
    :return: Http2.Http object
    """

    proxy_type_to_code = {
        "http": socks.PROXY_TYPE_HTTP,
        "socks5": socks.PROXY_TYPE_SOCKS5,
    }
    if config.get("proxy_type") in proxy_type_to_code:
        proxy_type = proxy_type_to_code[config["proxy_type"]]
    else:
        proxy_type = socks.PROXY_TYPE_HTTP

    proxy_info = None
    if config.get("proxy_url") and config.get("proxy_port"):
        if config.get("proxy_username") and config.get("proxy_password"):
            proxy_info = ProxyInfo(
                proxy_type=proxy_type,
                proxy_host=config["proxy_url"],
                proxy_port=int(config["proxy_port"]),
                proxy_user=config["proxy_username"],
                proxy_pass=config["proxy_password"],
                proxy_rdns=config.get("proxy_rdns", True),
            )
        else:
            proxy_info = ProxyInfo(
                proxy_type=proxy_type,
                proxy_host=config["proxy_url"],
                proxy_port=int(config["proxy_port"]),
                proxy_rdns=config.get("proxy_rdns", True),
            )

    if proxy_info:
        http = Http(
            proxy_info=proxy_info,
            timeout=timeout,
            disable_ssl_certificate_validation=disable_ssl_validation,
        )
    else:
        http = Http(
            timeout=timeout, disable_ssl_certificate_validation=disable_ssl_validation
        )

    if config.get("username") and config.get("password"):
        http.add_credentials(config["username"], config["password"])
    return http


def set_local_time_for_logger():
    """
    time.localtime converts the timestamp to the local time zone.
    This means that the returned values will be adjusted based on the time zone where the code is being run.
    The set_local_time_for_logger function updates the logging time to local timezone
    """
    logging.Formatter.converter = time.localtime


def process_vpc_access_request(auth_http_object, url, api):
    """
        Sends a VPC access request using the provided authentication HTTP object to the specified URL and API
        and process the response for the same.

    Args:
        auth_http_object: The authentication HTTP object to be used for the request.
        url (str): The URL to which the VPC access request should be sent.
        api (str): The API name or endpoint being accessed.

    Returns:
        The response from the VPC access request.
    """
    response_data = {}
    request_url = url
    result = list()
    while True:
        response, content = auth_http_object.request(url)
        data = content.decode("utf-8")
        response_data = json.loads(data)
        if "error" in response_data:
            error_code = response_data["error"]["code"]
            error_message = response_data["error"]["message"]
            raise Exception(f"Request failed with error {error_code}: {error_message}")
        if response_data.get(api):
            for obj in response_data[api]:
                result.append(obj)
        if "nextPageToken" in response_data:
            next_page_token = response_data["nextPageToken"]
            url = f"{request_url}?pageToken={next_page_token}"
        else:
            break
    return result


def configure_log_level_from_file(server_uri, session_key):
    """
    Method to fetch the log level configured at the global_settings.conf file and set the log level accordingly

    Args:
        server_uri (str): server uri
        session_key (str): session key
    """

    log_level = "INFO"

    if server_uri and session_key:
        global_settings_stanza = gconf.get_global_settings(server_uri, session_key)
        if global_settings_stanza:
            log_level = global_settings_stanza[ggc.global_settings][ggc.log_level]

    set_log_level(log_level)


def make_proxy_uri(config, logger):
    """
    Make proxy url from the given proxy settings.

    :param proxy_enabled: True if Proxy config is enabled. False otherwise
    :param proxy_settings: Proxy metadata

    :return: Proxy URI
    """
    try:
        uri = None
        scheme = config.get("proxy_type")
        if scheme not in ["http", "socks5", "socks5h"]:
            logger.warning(f"Proxy scheme is invalid. scheme={scheme}")
            return ""

        if config.get("proxy_rdns"):
            if scheme == "socks5":
                scheme = "socks5h"

        if config.get("proxy_url") and scheme:
            uri = config["proxy_url"]
            if is_host_ipv6(uri):
                uri = f"[{uri}]"
            if config.get("proxy_port"):
                uri = "{}:{}".format(uri, config.get("proxy_port"))
            if config.get("proxy_username") and config.get("proxy_password"):
                uri = "{}://{}:{}@{}/".format(
                    config["proxy_type"],
                    requests.compat.quote_plus(str(config["proxy_username"])),
                    requests.compat.quote_plus(str(config["proxy_password"])),
                    uri,
                )
            else:
                uri = "{}://{}".format(scheme, uri)

    except Exception as exc:
        logger.error(f"Error while making proxy URI. {exc}")

    return uri


def setup_env_proxy(config, logger, proxy_uri=None):
    """Setup proxy environment variables for SDKs if required.
    This environment variables will only affect the current process

    Args:
        config: Dict of proxy configuration details
        logger: logger
        proxy_uri: Use proxy_uri if config is not available
    """
    if not proxy_uri and config and is_true(config.get("proxy_enabled")):
        proxy_uri = make_proxy_uri(config, logger)

    # Setup proxy
    if proxy_uri:
        logger.info(f"Proxy is enabled.")
        # Splunk's local network calls throws error if NO_PROXY is not set.
        os.environ["no_proxy"] = NO_PROXY
        os.environ["NO_PROXY"] = NO_PROXY

        os.environ["http_proxy"] = proxy_uri
        os.environ["HTTP_PROXY"] = proxy_uri

        os.environ["https_proxy"] = proxy_uri
        os.environ["HTTPS_PROXY"] = proxy_uri
    else:
        logger.info(f"Proxy is disabled.")


def set_logger(server_uri, session_key, filename):
    """
    This function sets up a logger with configured log level.
    :param filename: Name of the log file
    :return logger: logger object
    """
    log_level = "INFO"

    if server_uri and session_key:
        global_settings_stanza = gconf.get_global_settings(server_uri, session_key)

        if global_settings_stanza:
            log_level = global_settings_stanza[ggc.global_settings][ggc.log_level]

    # To keep consistent log format across all the inputs
    log.Logs.set_context(log_format=LOG_FORMAT)

    logger = log.Logs().get_logger(filename)
    logger.setLevel(log_level)
    return logger


def get_host_name() -> str:
    """
    Returns host name of current machine
    """
    server_name, _ = get_splunk_host_info()
    return server_name
