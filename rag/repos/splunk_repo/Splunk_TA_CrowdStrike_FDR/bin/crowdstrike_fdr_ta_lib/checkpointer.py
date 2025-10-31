#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

from .kvstore_collection import KVStoreCollection
from typing import Union, Optional


class Checkpointer(KVStoreCollection):
    def __init__(
        self, app: str, server_uri: str, token: str, collection_name: str
    ) -> None:
        super(Checkpointer, self).__init__(server_uri, token, app, collection_name)
        if not self.check_collection_exists():
            self.create_collection()
            self.define_collection_schema(
                {
                    "field.checkpoint_name": "string",
                    "field.checkpoint_value": "string",
                }
            )

    def get(
        self, checkpoint_name: str, default_value: Optional[str] = None
    ) -> Optional[str]:
        res = self.search_records({"checkpoint_name": checkpoint_name})
        if not res:
            return default_value
        return res[0]["checkpoint_value"]

    def set(
        self, checkpoint_name: str, checkpoint_value: Union[str, int, float]
    ) -> None:
        res = self.search_records({"checkpoint_name": checkpoint_name})
        data = {
            "checkpoint_name": checkpoint_name,
            "checkpoint_value": checkpoint_value,
        }
        if res:
            self.update_record(res[0]["_key"], data)
        else:
            self.create_record(data)
