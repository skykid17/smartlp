#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import platform
from datetime import datetime

import botocore
import solnlib

from .constants import (
    SOURCETYPE_TO_INDEX_PROP_NAME,
    DEFAULT_EVENT_ENCODING,
    SERVER_HOST,
)
from .filtering import build_filter_set
from .logger_adapter import CSLoggerAdapter
from typing import Union, Optional, Dict, Any
from splunklib import modularinput as smi

logger = CSLoggerAdapter(
    solnlib.log.Logs()
    .get_logger("splunk_ta_crowdstrike_fdr")
    .getChild("config_builders")
)


class CrowdStrikeAddonConfigError(Exception):
    pass


def build_ignore_before(input_props: Dict[str, Any]) -> Dict[str, Any]:
    ignore_before = {}
    sqs_ignore = (input_props.get("aws_sqs_ignore_before") or "").strip()
    try:
        if sqs_ignore:
            sqs_ignore = datetime.strptime(sqs_ignore, "%Y-%m-%d %H:%M")
            ignore_before["aws_sqs_ignore_before"] = sqs_ignore.timestamp()
    except ValueError as ve:
        solnlib.log.log_exception(
            logger,
            ve,
            "AWS SQS Error",
            msg_before=f"Failed to parse SQS age datetime threshold '{sqs_ignore}' with the error: '{ve}'",
        )
    return ignore_before


def build_filter_config(
    input_props: Dict[str, Any], cs_filters: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    event_filter_name = input_props.get("cs_event_filter_name")
    if not event_filter_name:
        return dict(cs_event_filter=None)

    logger.debug(
        f"looking up for CS selected filter: {event_filter_name} in {cs_filters}"
    )
    cs_filters_info = cs_filters.get(event_filter_name)
    if not cs_filters_info:
        raise CrowdStrikeAddonConfigError(
            f"Unknown CrowdStrike event filter name is selected: '{event_filter_name}'"
        )

    filter = build_filter_set(**cs_filters_info)
    return dict(cs_event_filter=(filter[0], tuple(filter[1])) if filter else None)


def build_device_field_filter_config(
    input_props: Dict[str, Any], cs_filters: Dict[str, Any]
) -> Dict[str, Any]:
    event_filter_name = input_props.get("cs_device_field_filter_name")
    if not event_filter_name:
        return dict(filter_type=None, filter_value=None)

    logger.debug(
        f"looking up selected device field filter: {event_filter_name} in {cs_filters}"
    )

    cs_filters_info = cs_filters.get(event_filter_name)
    if not cs_filters_info:
        raise CrowdStrikeAddonConfigError(
            f"Unknown CrowdStrike device field filter name is selected: '{event_filter_name}'"
        )

    return dict(
        filter_type=cs_filters_info["filter_type"],
        filter_value=[s.strip() for s in cs_filters_info["filter_value"].split(",")],
    )


def build_sourcetype_indexes(input_props: Dict[str, Any]) -> Dict[str, Any]:
    sourcetype_indexes = {}
    for sourcetype, index_prop in SOURCETYPE_TO_INDEX_PROP_NAME.items():
        index = input_props.get(index_prop) or input_props["index"]
        sourcetype_indexes[sourcetype] = index
    return {"sourcetype_indexes": sourcetype_indexes}


def build_input_run_config(
    input_props: Dict[str, Any],
    metadata: Dict[str, Any],
    cs_filters: Dict[str, Any],
    ew: smi.EventWriter,
) -> Dict[str, Any]:

    input_config = dict(
        event_writer=ew,
        input_stanza=input_props["input_stanza"],
        collect_external=input_props.get("collect_external_events") == "1",
        collect_ztha=input_props.get("collect_ztha_events") == "1",
        collect_aidmaster=input_props.get("collect_inventory_aidmaster") == "1",
        collect_managedassets=input_props.get("collect_inventory_managedassets") == "1",
        collect_notmanaged=input_props.get("collect_inventory_notmanaged") == "1",
        collect_appinfo=input_props.get("collect_inventory_appinfo") == "1",
        collect_userinfo=input_props.get("collect_inventory_userinfo") == "1",
        cs_event_encoding=input_props.get("cs_event_encoding")
        or DEFAULT_EVENT_ENCODING,
        cs_ithr_type=input_props.get("cs_ithr_type"),
        server_host=metadata.get(SERVER_HOST) or platform.node(),
    )

    if input_props["host"] == "$decideOnStartup":
        input_config["host"] = input_config["server_host"]
    else:
        input_config["host"] = input_props["host"]

    if input_props.get("checkpoint_type"):
        input_config["checkpoint_type"] = input_props["checkpoint_type"]
    else:
        input_config["checkpoint_type"] = "sqs"

    input_config.update(build_sourcetype_indexes(input_props))
    input_config.update(build_ignore_before(input_props))
    input_config.update(build_filter_config(input_props, cs_filters))

    return input_config


def extract_aws_credentials(
    sqs_session_name: str, fdr_aws_collection: Dict[str, Any]
) -> Dict[str, Any]:
    sqs_session_info = fdr_aws_collection.get(sqs_session_name)
    if not sqs_session_info:
        raise CrowdStrikeAddonConfigError("Unknown FDR AWS collection name is selected")

    return dict(
        region_name=sqs_session_info["aws_region"],
        aws_access_key_id=sqs_session_info["aws_access_key_id"],
        aws_secret_access_key=sqs_session_info["aws_secret_access_key"],
    )


def build_s3bucket_scan_config(
    input_props: Dict[str, Any], fdr_aws_collection: Dict[str, Any]
) -> Dict[str, Any]:

    aws_config = dict(bucket=input_props["aws_bucket"])

    sqs_session_name = input_props.get("aws_collection")
    if not sqs_session_name:
        raise CrowdStrikeAddonConfigError("AWS FDR collection name is not selected")

    aws_config["s3_creds"] = extract_aws_credentials(
        sqs_session_name, fdr_aws_collection
    )

    return aws_config


def build_aws_run_config(
    input_props: Dict[str, Any], fdr_aws_collection: Dict[str, Any]
) -> Dict[str, Any]:

    aws_config = dict(
        sqs_url=input_props["aws_sqs_url"],
        visibility_timeout=int(input_props["aws_sqs_visibility_timeout"]),
        max_number_of_messages=1,
    )

    sqs_session_name = input_props.get("aws_collection")
    if not sqs_session_name:
        raise CrowdStrikeAddonConfigError("AWS FDR collection name is not selected")

    aws_config["sqs_creds"] = extract_aws_credentials(
        sqs_session_name, fdr_aws_collection
    )

    aws_config["s3_creds"] = aws_config["sqs_creds"].copy()

    return aws_config


def build_consumer_config(
    input_props: Dict[str, Any], metadata: Dict[str, Any], ew: smi.EventWriter
) -> Dict[str, Any]:
    input_config = dict(
        event_writer=ew,
        input_stanza=input_props["input_stanza"],
        manager=input_props["manager"],
        cs_ithr_type=input_props.get("cs_ithr_type"),
        server_host=metadata.get(SERVER_HOST) or platform.node(),
    )

    if input_props["host"] == "$decideOnStartup":
        input_config["host"] = input_config["server_host"]
    else:
        input_config["host"] = input_props["host"]

    return input_config


def build_shared_config(input_props: Dict[str, Any]) -> Dict[str, Any]:
    shared_config = dict(
        aws_collection=input_props["aws_collection"],
        collect_external=input_props.get("collect_external_events") == "1",
        collect_ztha=input_props.get("collect_ztha_events") == "1",
        cs_event_encoding=input_props.get("cs_event_encoding")
        or DEFAULT_EVENT_ENCODING,
        cs_ithr_type=input_props.get("cs_ithr_type"),
        cs_event_filter_name=input_props.get("cs_event_filter_name"),
        cs_device_field_filter_name=input_props.get("cs_device_field_filter_name"),
    )

    shared_config.update(build_sourcetype_indexes(input_props))

    return shared_config


def build_proxy_connecton_string(
    proxy_settings: Dict[str, Any], safe: bool = False
) -> Optional[str]:
    if proxy_settings.get("proxy_enabled") != "1":
        return None

    proxy_type = proxy_settings.get("proxy_type")
    proxy_url = proxy_settings.get("proxy_url")
    proxy_port = proxy_settings.get("proxy_port")
    proxy_username = proxy_settings.get("proxy_username")
    proxy_password = proxy_settings.get("proxy_password")

    proxy_creds = ""
    if proxy_username:
        proxy_creds += proxy_username
        if proxy_password:
            proxy_creds += ":" + proxy_password
        proxy_creds += "@"

    if safe:
        return f"{proxy_type}://*****:*****@{proxy_url}:{proxy_port}"

    return f"{proxy_type}://{proxy_creds}{proxy_url}:{proxy_port}"


def build_aws_proxy_config(ta_settings: Dict[str, Any]) -> Dict[str, Any]:
    config_proxy = ta_settings.get("proxy")

    connection_string = build_proxy_connecton_string(config_proxy)
    if connection_string is None:
        logger.info("AWS proxy is disabled, aws_proxy=disabled")
        return {}

    proxies = {"http": connection_string, "https": connection_string}

    logger.info(
        f"AWS proxy is enabled, aws_proxy={build_proxy_connecton_string(config_proxy, safe=True)}"
    )

    return {"config": botocore.config.Config(proxies=proxies)}


def build_crowdstrike_api_connection_config(
    input_props: Dict[str, Any], ta_settings: Dict[str, Any]
) -> Dict[str, Any]:
    config_proxy = ta_settings.get("proxy")
    config = dict(
        base_url=input_props["api_base_url"],
        client_id=input_props["api_client_id"],
        client_secret=input_props["api_client_secret"],
        proxy=build_proxy_connecton_string(config_proxy),
    )

    log_config = config.copy()
    log_config["client_secret"] = "*****"
    log_config["proxy"] = build_proxy_connecton_string(config_proxy, safe=True)
    logger.info(f"Crowdstrike API connection config {log_config}")

    return config
