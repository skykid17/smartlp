#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

from datetime import datetime
from random import randint
from logging import LoggerAdapter
from typing import Dict, Any, Tuple


class CSLoggerAdapter(LoggerAdapter):
    input_exec_id = hex(int(f"{datetime.now().microsecond}{randint(0,1000):03}"))[2:]

    def __init__(self, logger: LoggerAdapter, extras: Dict[str, Any] = {}) -> None:
        super(CSLoggerAdapter, self).__init__(logger, extras)

    def process(self, msg: str, kwargs: Any) -> Tuple[str, Any]:
        return f"cs_input_exec_id={self.input_exec_id}, {msg}", kwargs
