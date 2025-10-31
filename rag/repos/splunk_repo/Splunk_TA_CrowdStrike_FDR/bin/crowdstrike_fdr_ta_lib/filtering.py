#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import re
import traceback

import solnlib

from datetime import datetime
from .constants import (
    SOURCETYPE_AIDMASTER,
    SOURCETYPE_APPINFO,
    SOURCETYPE_EXTERNAL,
    SOURCETYPE_MANAGEDASSETS,
    SOURCETYPE_NOTMANAGED,
    SOURCETYPE_SENSOR,
    SOURCETYPE_SENSOR_ITHR,
    SOURCETYPE_USERINFO,
    SOURCETYPE_ZTHA,
)

from .logger_adapter import CSLoggerAdapter
from typing import Union, Tuple, Optional, Dict, Any

logger = CSLoggerAdapter(
    solnlib.log.Logs().get_logger("splunk_ta_crowdstrike_fdr").getChild("filtering")
)

FILTER_TYPE_DROP = "drop"
FILTER_TYPE_INGEST = "ingest"
SUPPORTED_FILTER_TYPES = (FILTER_TYPE_DROP, FILTER_TYPE_INGEST)

DEVICE_PROP_FILTER_TYPE_SKIP = "skip"
DEVICE_PROP_FILTER_TYPE_ENRICH = "enrich"
SUPPORTED_DEVICE_PROP_FILTER_TYPES = (
    DEVICE_PROP_FILTER_TYPE_SKIP,
    DEVICE_PROP_FILTER_TYPE_ENRICH,
)

PREFIX_PATTERN = re.compile(
    r"(?:"
    r"(?P<data>data)|"
    r"(?P<aidmaster>aidmaster)|"
    r"(?P<managedassets>managedassets)|"
    r"(?P<notmanaged>notmanaged)|"
    r"(?P<userinfo>userinfo)|"
    r"(?P<appinfo>appinfo)"
    r")/"
)

EVENT_REGEX_SENSOR = r'(?:"event_simpleName":\s*"(?P<sensor>\w+)")'
EVENT_REGEX_EXTERNAL = r'(?:"EventType":\s*"(?P<external>\w+)")'
EVENT_REGEX_ZTHA = r'(?:"event_type":\s*"(?P<ztha>\w+)")'

EVENT_PATTERN = re.compile(
    "(?:" + "|".join([EVENT_REGEX_SENSOR, EVENT_REGEX_EXTERNAL, EVENT_REGEX_ZTHA]) + ")"
)

AID_VALUE_PATTERN = re.compile(r'(?:"aid":\s*"(?P<aid>\w+)")')


def from_isoformat(
    sourcetype: str, prop_name: str, event: Dict[str, Any]
) -> Optional[datetime]:
    time_src = event.get(prop_name)
    if not time_src:
        return None

    preprocessed = None
    try:
        preprocessed = time_src.strip().rstrip("zZ")[:26]
        return datetime.fromisoformat(preprocessed)
    except Exception as e:
        logger.warning(
            f"Failed to parse time '{time_src}' (preprocessed '{preprocessed}') as iso formatfor an event of sourcetype {sourcetype} with traceback: {e}"
        )

    return None


def from_timestamp_x1000(
    sourcetype: str, prop_name: str, event: Dict[str, Any]
) -> Optional[datetime]:
    time_src = event.get(prop_name)
    if not time_src:
        return None

    try:
        return datetime.fromtimestamp(float(time_src) / 1000)
    except Exception as e:
        logger.warning(
            f"Failed to parse time '{time_src}' as timestamp %s%3N for an event of sourcetype {sourcetype} with traceback: {e}"
        )

    return None


def from_timestamp(
    sourcetype: str, prop_name: str, event: Dict[str, Any]
) -> Optional[datetime]:
    time_src = event.get(prop_name)
    if not time_src:
        return None

    try:
        return datetime.fromtimestamp(float(time_src))
    except Exception as e:
        logger.warning(
            f"Failed to parse time '{time_src}' as timestamp for an event of sourcetype {sourcetype} with traceback: {e}"
        )

    return None


def get_sourcetype_based_time_extractors() -> Dict[str, Any]:
    mapping = {
        SOURCETYPE_AIDMASTER: lambda x: from_timestamp(SOURCETYPE_AIDMASTER, "Time", x),
        SOURCETYPE_APPINFO: lambda x: from_timestamp(SOURCETYPE_APPINFO, "_time", x),
        SOURCETYPE_EXTERNAL: lambda x: from_timestamp_x1000(
            SOURCETYPE_EXTERNAL, "UTCTimestamp", x
        ),
        SOURCETYPE_MANAGEDASSETS: lambda x: from_timestamp(
            SOURCETYPE_MANAGEDASSETS, "_time", x
        ),
        SOURCETYPE_NOTMANAGED: lambda x: from_timestamp(
            SOURCETYPE_NOTMANAGED, "_time", x
        ),
        SOURCETYPE_SENSOR: lambda x: from_timestamp_x1000(
            SOURCETYPE_SENSOR, "timestamp", x
        ),
        SOURCETYPE_SENSOR_ITHR: lambda x: from_timestamp_x1000(
            SOURCETYPE_SENSOR_ITHR, "timestamp", x
        ),
        SOURCETYPE_USERINFO: lambda x: from_timestamp(SOURCETYPE_USERINFO, "_time", x),
        SOURCETYPE_ZTHA: lambda x: from_isoformat(SOURCETYPE_ZTHA, "modified_time", x),
    }

    return mapping


def prefix_based_sourcetype(
    prefix: str, input_config: Dict[str, Any]
) -> Optional[Tuple[bool, Optional[str]]]:
    res = PREFIX_PATTERN.search(prefix)
    if res is None:
        return False, None

    if res.group("aidmaster"):
        return input_config["collect_aidmaster"], SOURCETYPE_AIDMASTER

    if res.group("managedassets"):
        return input_config["collect_managedassets"], SOURCETYPE_MANAGEDASSETS

    if res.group("notmanaged"):
        return input_config["collect_notmanaged"], SOURCETYPE_NOTMANAGED

    if res.group("appinfo"):
        return input_config["collect_appinfo"], SOURCETYPE_APPINFO

    if res.group("userinfo"):
        return input_config["collect_userinfo"], SOURCETYPE_USERINFO

    if res.group("data"):
        return True, None


def event_based_sourcetype(event: str, input_config: Dict[str, Any]) -> Tuple:
    res = EVENT_PATTERN.search(event)
    if res is None:
        return False, None

    if res.group("ztha"):
        return input_config["collect_ztha"], SOURCETYPE_ZTHA

    if res.group("external"):
        return input_config["collect_external"], SOURCETYPE_EXTERNAL

    if input_config.get("cs_ithr_type") == "inventory":
        sensor_sourcetype = SOURCETYPE_SENSOR_ITHR
    else:
        sensor_sourcetype = SOURCETYPE_SENSOR

    event_simple_name = res.group("sensor")

    filter_info = input_config.get("cs_event_filter")
    if not isinstance(filter_info, (tuple, list)):
        return True, sensor_sourcetype

    filter_type, event_names = filter_info

    if filter_type == FILTER_TYPE_INGEST:
        return event_simple_name in event_names, sensor_sourcetype

    if filter_type == FILTER_TYPE_DROP:
        return event_simple_name not in event_names, sensor_sourcetype

    return True, sensor_sourcetype


def build_filter_set(
    filter_type: str, filter_value: str, **ignore: Any
) -> Optional[Tuple]:
    if filter_type not in SUPPORTED_FILTER_TYPES:
        return None

    event_name_set = {n.strip() for n in filter_value.split() if n.strip()}
    if not event_name_set:
        return None

    return filter_type, event_name_set


def build_filter_pattern(filter_type: str, filter_value: str, **ignore: Any):
    normalized_names = [n.strip() for n in filter_value.split() if n.strip()]
    if not normalized_names:
        return None

    regext_filter = "|".join(normalized_names)

    try:
        if filter_type == FILTER_TYPE_INGEST:
            return re.compile(
                rf'(?:.*"event_simpleName"\s*:\s*"(?:{regext_filter})".*)'
            )
        if filter_type == FILTER_TYPE_DROP:
            return re.compile(
                rf'(?!.*"event_simpleName"\s*:\s*"(?:{regext_filter})".*)'
            )

        logger.warning(
            "build_filter_pattern: unsupported filter type "
            + f"'{filter_type}', expected '{FILTER_TYPE_INGEST}' "
            + f"or '{FILTER_TYPE_DROP}'"
        )
        return None

    except Exception as e:
        msg = f"build_filter_pattern error: {e}"
        tb = " ---> ".join(traceback.format_exc().split("\n"))
        solnlib.log.log_exception(
            logger, e, "Build Filter Pattern Error", msg_before=f"{msg} {tb}"
        )
        return None
