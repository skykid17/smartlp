#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from logging import Logger
from typing import Dict, Any

import sfdc_utility as su
from abc import ABC, abstractmethod

from sfdc_checkpoint import CheckpointHandler


class BaseSfdcDataCollector(ABC):
    def __init__(self, sfdc_util_ob: su.SFDCUtil, checkpoint_collection_name: str):
        self.sfdc_util_ob: su.SFDCUtil = sfdc_util_ob
        self.logger: Logger = self.sfdc_util_ob.logger
        self.ckpt_handler: CheckpointHandler = CheckpointHandler(
            collection_name=checkpoint_collection_name,
            sfdc_util_ob=self.sfdc_util_ob,
        )
        self.ckpt_data: Dict[str, Any] = {}

    @abstractmethod
    def start(self):
        """Abstract method to start the data collection process.
        This must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def data_collector(self):
        """Abstract method for data collection logic.
        This must be implemented by subclasses.
        """
        pass
