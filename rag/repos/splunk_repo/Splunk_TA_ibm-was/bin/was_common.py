#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import logging
import os.path as op
import os
import re

import was_consts as c

_LOGGER = logging.getLogger(c.was_log)


def discover_was_install_dir(interactive=False):
    msg = (
        "WebSphere installation directory is not provided. "
        "Doing installation folder discovery."
    )

    if interactive:
        print(msg)

    _LOGGER.info(msg)
    if os.name == "nt":
        default_dirs = ("C:\\Program Files (x86)\\", "C:\\Program Files\\")
    else:
        default_dirs = ("/opt/",)

    for d in default_dirs:
        loc = op.join(d, "IBM", "WebSphere", "AppServer")
        if op.exists(loc):
            msg = "Found installation location at {}".format(loc)
            if interactive:
                print(msg)
            _LOGGER.info(msg)
            return loc

    msg = "Failed to discover the WebSphere installation dir"
    if interactive:
        print(msg)

    _LOGGER.error(msg)
    return None


def discover_log_viewer_cmds(config):
    """
    @config: dict like object which contains:
    {
        was_install_dir: "/opt/IBM/WebSphere",
        excluded_profiles: xxx,
        start_date: in "MM/dd/yy" format or the "MM/dd/yy H:m:s:S" format,
        level: INFO or other level,
        min_level: INFO or other level,
        max_level: INFO or other level,
        session_key: splunkd session key,
        server_uri: splunkd server uri,
        checkpoint_dir: modinput ckpt dir,
    }
    @return: a list of logViewer commands with full path
    """

    # FIXME, another thread to monitor log viewer
    if not config[c.was_install_dir]:
        config[c.was_install_dir] = discover_was_install_dir()

    if not config[c.was_install_dir]:
        return []

    if config[c.was_install_dir].rstrip("/").endswith("AppServer"):
        profile_dir = op.join(config[c.was_install_dir], "profiles")
    else:
        profile_dir = op.join(config[c.was_install_dir], "AppServer", "profiles")

    if not op.exists(profile_dir):
        _LOGGER.warn("Profile dir=%s doesn't exist.", profile_dir)
        return []

    root, profiles, _ = next(os.walk(profile_dir))
    if not profiles:
        _LOGGER.warn("No profiles are found.")
        return []

    cmds = []
    if os.name == "nt":
        log_viewer = "logViewer.bat"
    elif os.name == "posix":
        log_viewer = "logViewer.sh"
    else:
        log_viewer = "logViewer"

    excluded_profiles = config[c.excluded_profiles]
    if excluded_profiles:
        excluded_profiles = [
            excluded_profile.strip()
            for excluded_profile in excluded_profiles.split(",")
        ]
    else:
        excluded_profiles = []

    for profile in profiles:
        if profile in excluded_profiles:
            _LOGGER.info("Exclude profile=%s from HPEL data collection", profile)
            continue

        cmd_w_path = op.join(root, profile, "bin", log_viewer)
        if op.exists(cmd_w_path):
            # traverse the profile's directory to find servers
            profile_root, servers, _ = next(
                os.walk(os.path.join(profile_dir, profile, "servers"))
            )
            _LOGGER.info(
                "Detected following list of servers under profile {} : {}".format(
                    profile, servers
                )
            )
            excluded_servers = config[c.excluded_servers]
            if excluded_servers:
                excluded_servers = [
                    excluded_server.strip()
                    for excluded_server in excluded_servers.split(",")
                ]
            else:
                excluded_servers = []

            for server in servers:
                if profile + ":" + server in excluded_servers:
                    _LOGGER.info(
                        'Excluding server "{}" of profile "{}" for HPEL data collection.'.format(
                            server, profile
                        )
                    )
                    continue
                server_repo_path = os.path.join(profile_dir, profile, "logs", server)
                if op.exists(server_repo_path):
                    cmds.append((cmd_w_path, server_repo_path, server))
        else:
            _LOGGER.info("Didn't find logViewer command for profile=%s", profile)
    return cmds
