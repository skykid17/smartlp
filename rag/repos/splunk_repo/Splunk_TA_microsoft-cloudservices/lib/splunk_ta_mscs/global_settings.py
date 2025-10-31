#!/usr/bin/python
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from __future__ import annotations

from attr import define, field, validators
from cattr import structure


def unsigned_int(default):
    return field(validator=validators.gt(0), default=default)


def int_in_range(min, max, default):
    return field(validator=[validators.ge(min), validators.le(max)], default=default)


@define
class GlobalSettings:
    worker_threads_num: int = int_in_range(1, 100, 10)
    query_entities_page_size: int = int_in_range(100, 10000, 1000)
    event_cnt_per_item: int = int_in_range(10, 1000, 100)
    query_end_time_offset: int = int_in_range(20, 600, 180)
    get_blob_batch_size: int = int_in_range(10000, 1000000, 120000)
    http_timeout: int = unsigned_int(120)

    @classmethod
    def from_dict(cls, config: dict) -> GlobalSettings:
        if not isinstance(config, dict):
            raise ValueError("Global settings config is not a dict")

        return structure(config, cls)
