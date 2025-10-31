#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import base64
from builtins import object
from datetime import datetime, timedelta

import splunk_ta_gcp.legacy.consts as ggc
from splunk_ta_gcp.common.checkpoint import KVStoreCheckpoint
import splunktalib.state_store as sss

from . import consts as gmc

metric_date_fmt = "%Y-%m-%dT%H:%M:%S"


def add_timezone(metric_date_str):
    if not metric_date_str.endswith("-00:00"):
        metric_date_str = "{}-00:00".format(metric_date_str)
    return metric_date_str


def strip_off_timezone(metric_date_str):
    pos = metric_date_str.rfind("-00:00")
    if pos > 0:
        metric_date_str = metric_date_str[:pos]
    return metric_date_str


def strp_metric_date(metric_date_str):
    metric_date_str = strip_off_timezone(metric_date_str)
    return datetime.strptime(metric_date_str, metric_date_fmt)


def strf_metric_date(metric_date):
    mdate = datetime.strftime(metric_date, metric_date_fmt)
    return "{}-00:00".format(mdate)


def calculate_youngest(oldest, polling_interval, now, win=86400):
    """
    return (youngest, done)
    """

    win = max(polling_interval, win)
    youngest = oldest + timedelta(seconds=win)
    done = False
    if youngest >= now:
        youngest = now
        done = True

    return youngest, done


class GoogleCloudMonitorCheckpointer(object):
    def __init__(self, config):
        self._config = config
        self._filename = "{stanza_name}|{metric_name}".format(
            stanza_name=config[ggc.name], metric_name=config[gmc.google_metrics]
        )
        self._key = base64.b64encode(self._filename.encode("utf-8"))
        self._store = sss.get_state_store(
            config,
            config[ggc.appname],
            collection_name=ggc.google_cloud_monitor,
            use_kv_store=config.get(ggc.use_kv_store),
        )
        self._is_ckpt_available = True
        self._state = self._get_state()

    @property
    def checkpoint_filename(self):
        return self._filename

    @property
    def is_ckpt_available(self):
        """
        If checkpoint file available in the directory
        """
        return self._is_ckpt_available

    @is_ckpt_available.setter
    def is_ckpt_available(self, value):
        self._is_ckpt_available = value

    def _get_state(self):
        state = self._store.get_state(self._key.decode("utf-8"))
        if not state:
            self._is_ckpt_available = False
        return state

    def oldest(self, key):
        return self._state.get(key)

    def delete(self):
        """
        Delete checkpoint file if available
        """
        self._store.delete_state(self._key.decode("UTF-8"))


class CloudMonitorKVStore(KVStoreCheckpoint):
    """
    Handle Kvstore related task for cloudmonitor input
    """

    def __init__(self, collection_name, service, fields={}):
        super().__init__(collection_name, service, fields)

    def batch_save(self, checkpoint_key, oldest_time):
        """
        Batch save checkpoint information for the given list of dictionaries.
        The function uses "batch_save" to insert or update the existing checkpoint.
        *Note -> using "batch_save" because this method will also perform update task
        if key exist
        """
        oldest_time = strip_off_timezone(oldest_time)
        data = {
            "_key": checkpoint_key,
            gmc.oldest: oldest_time,
        }
        super().batch_save([data])
