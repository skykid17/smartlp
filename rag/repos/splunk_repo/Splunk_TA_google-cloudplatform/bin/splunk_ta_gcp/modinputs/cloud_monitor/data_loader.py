#
#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import json
import threading
import time
import traceback
import re
from builtins import object
from datetime import datetime, timedelta
import urllib.parse

import splunk_ta_gcp.legacy.common as tacommon
import splunk_ta_gcp.legacy.consts as ggc
import splunk_ta_gcp.legacy.resource_manager as grm
from splunksdc import log as logging
from splunklib.client import Service

from . import checkpointer as ckpt
from . import consts as gmc
from . import wrapper as gmw

logger = logging.get_module_logger()


class GoogleCloudMonitorDataLoader(object):
    def __init__(self, config):
        """
        :config: dict object
        {
            "appname": xxx,
            "use_kv_store": xxx,
            "proxy_url": xxx,
            "proxy_port": xxx,
            "proxy_username": xxx,
            "proxy_password": xxx,
            "proxy_rdns": xxx,
            "proxy_type": xxx,
            "google_credentials": xxx,
            "google_project": xxx,
            "google_metric": xxx,
            "index": xxx,
        }
        """

        interval = int(config.get(ggc.polling_interval, 120))
        config[ggc.polling_interval] = interval
        if not config.get(gmc.oldest):
            aweek_ago = datetime.utcnow() - timedelta(days=7)
            config[gmc.oldest] = ckpt.strf_metric_date(aweek_ago)

        self._config = config
        self._source = "{project}:{metric}".format(
            project=self._get_google_project,
            metric=self._get_google_metric,
        )
        self._event_writer = None
        self._checkpoint = None
        self._initialize_collection()
        self._store = ckpt.GoogleCloudMonitorCheckpointer(config)
        self._lock = threading.Lock()
        self._stopped = False
        self._monitored_project = None
        self._checkpoint_info = None
        self._host_name = tacommon.get_host_name()

    def get_interval(self):
        return self._config[ggc.polling_interval]

    def get_props(self):
        return self._config

    def stop(self):
        self._stopped = True
        logger.info("Stopping GoogleCloudMonitorDataLoader")

    def __call__(self):
        self.index_data()

    def index_data(self):
        if self._lock.locked():
            logger.info(
                "Last time of data collection for project=%s, " "metric=%s is not done",
                self._get_google_project,
                self._get_google_metric,
            )
            return

        if self._event_writer is None:
            self._event_writer = self._config[ggc.event_writer]

        with self._lock:
            self._do_index()

    def _do_index(self):
        msg = "collecting data for datainput={}, project={}, metric={}".format(
            self._config[ggc.name],
            self._get_google_project,
            self._get_google_metric,
        )
        logger.info("Start {}".format(msg))
        try:
            self._do_safe_index()
        except Exception:
            logger.error("Failed of {}, error=%s".format(msg), traceback.format_exc())
        logger.info("End of {}".format(msg))

    def _do_safe_index(self):
        mon = self._get_cloud_monitor_obj(gmc.cm_api_ver_3)
        monitored_projects = self._get_monitored_projects()
        for mon_project in monitored_projects:
            self._monitored_project = mon_project
            params = self._initialise_params()
            checkpoint_id = self._get_checkpoint_id()
            polling_interval = self.get_interval()
            oldest = self._get_oldest(checkpoint_id)
            self._update_collection_if_fileckpt(checkpoint_id, oldest)
            now = datetime.utcnow()
            self._config["cm_checkpoint_id"] = checkpoint_id
            done, win = False, int(self._config.get("cm_win", 86400))
            while not done and not self._stopped:
                youngest, done = ckpt.calculate_youngest(
                    oldest, polling_interval, now, win
                )
                params[gmc.oldest] = ckpt.strf_metric_date(oldest)
                params[gmc.youngest] = ckpt.strf_metric_date(youngest)
                metrics = mon.list_metrics(params)
                if metrics:
                    latest = self._write_events(metrics)
                    if not latest:
                        oldest = youngest
                    else:
                        seconds = tacommon.rfc3339_to_seconds(latest)
                        oldest = datetime.utcfromtimestamp(seconds)
                        oldest += timedelta(seconds=1)

                    self._save_checkpoint_info(
                        checkpoint_id, ckpt.strf_metric_date(oldest)
                    )
                else:
                    # Sleep 2 seconds to avoid tight loop to consume API rate
                    time.sleep(2)
                    if (now - youngest).total_seconds() > win:
                        oldest += timedelta(seconds=win)
                        self._save_checkpoint_info(
                            checkpoint_id, ckpt.strf_metric_date(oldest)
                        )
                        logger.info("Progress to %s", oldest)
                    elif (youngest - oldest).total_seconds() >= win:
                        oldest += timedelta(seconds=win // 2)
                        self._save_checkpoint_info(
                            checkpoint_id, ckpt.strf_metric_date(oldest)
                        )
                        logger.info("Progress to %s", oldest)

        self._delete_ckpt_file()

    def _update_collection_if_fileckpt(self, checkpoint_id, oldest):
        """
        Save the oldest time in collection if migration is getting performed
        to avoid edge cases if child-project do not have metrics for 24hrs
        and input being halted for some reasons.
        """
        if not self._checkpoint_info and self._store.is_ckpt_available:
            self._save_checkpoint_info(checkpoint_id, ckpt.strf_metric_date(oldest))

    def _get_cloud_monitor_obj(self, version):
        self._config["version"] = version
        return gmw.GoogleCloudMonitor(logger, self._config)

    def _delete_ckpt_file(self):
        if self._store.is_ckpt_available:
            self._store.delete()
            logger.info(
                f"Successfully deleted checkpoint file - {self._store.checkpoint_filename}"
            )
            self._store.is_ckpt_available = False

    def _get_monitored_projects(self):
        """
        Get the list of monitored projects
        """
        monitored_projects = self._config[gmc.google_monitored_projects]
        if monitored_projects == gmc.all_projects:
            # fetch the list of all projects from the api
            # if list is empty then overwrite list with main project number
            mon = self._get_cloud_monitor_obj(gmc.cm_api_ver_1)
            monitored_projects = mon.monitored_projects(self._get_google_project)
            if not monitored_projects:
                res_mgr = grm.GoogleResourceManager(logger, self._config)
                parent_project_number = res_mgr.get_project_number(
                    self._get_google_project
                )
                monitored_projects = [parent_project_number]
        else:
            monitored_projects = monitored_projects.split(",")

        return monitored_projects

    @property
    def _get_monitored_project(self):
        return self._monitored_project

    @property
    def _get_google_project(self):
        return self._config[ggc.google_project]

    @property
    def _get_google_metric(self):
        return self._config[gmc.google_metrics]

    def _initialise_params(self):
        params = {
            ggc.google_project: self._get_google_project,
            gmc.google_metrics: self._get_google_metric,
            gmc.monitored_project: self._get_monitored_project,
        }
        return params

    def _get_oldest(self, checkpoint_id):
        self._fetch_checkpoint_info(checkpoint_id)
        if self._checkpoint_info:
            oldest_time = self._checkpoint_info.get(gmc.oldest)
        elif self._store.is_ckpt_available:
            logger.info(
                f"File based checkpoint found - {self._store.checkpoint_filename}."
            )
            oldest_time = self._store.oldest(gmc.oldest)
        else:
            oldest_time = ckpt.strip_off_timezone(self._config[gmc.oldest])
        return ckpt.strp_metric_date(oldest_time)

    def _fetch_checkpoint_info(self, checkpoint_id):
        """
        Fetch the checkpoint info from collection
        """
        self._checkpoint_info = self._checkpoint.get(checkpoint_id)

    def _save_checkpoint_info(self, checkpoint_key, oldest_time) -> None:
        """
        This will save the given timestamp in checkpoint
        """
        logger.debug(
            "Saving the checkoint information: Checkpoint_key=%s, time=%s",
            checkpoint_key,
            oldest_time,
        )
        self._checkpoint.batch_save(checkpoint_key, oldest_time)

    def _create_event(self, metric):
        try:
            event_time = metric["points"][0]["interval"]["startTime"]
            event_time = tacommon.rfc3339_to_seconds(event_time)
        except Exception:
            event_time = None
            logger.error(
                "Failed to parse rfc3339 datetime=%s, error=%s",
                event_time,
                traceback.format_exc(),
            )

        event = self._event_writer.create_event(
            index=self._config[ggc.index],
            host=self._host_name,
            source=self._source,
            sourcetype="google:gcp:monitoring",
            time=event_time,
            unbroken=False,
            done=False,
            events=json.dumps(metric, ensure_ascii=False, sort_keys=True),
        )
        return event

    def _write_events(self, metrics):
        total_count = 0
        events, max_timestamp = [], ""
        for metric in metrics:
            if "points" not in metric or not metric["points"]:
                continue

            metric["project_number"] = self._get_monitored_project
            points = metric["points"]
            # expand points
            del metric["points"]
            for point in points:
                data_point = {**metric, "points": [point]}
                event = self._create_event(data_point)
                events.append(event)
                total_count += 1
                if point["interval"]["endTime"] > max_timestamp:
                    max_timestamp = point["interval"]["endTime"]
                if len(events) >= 1000:
                    # events may contain values more than 1000 since we are separating events from the "points"
                    # to single event from the actual metric value
                    self._event_writer.write_events(events)
                    events = []

        logger.info(
            "Total received event for datainput=%s,project=%s, metric=%s, checkpoint=%s, count=%s",
            self._config[ggc.name],
            self._get_google_project,
            self._get_google_metric,
            self._config["cm_checkpoint_id"],
            total_count,
        )
        self._event_writer.write_events(events)
        return max_timestamp

    def _get_checkpoint_id(self):
        """
        Get the unique identifier for checkpointing

        Args:
            project (string): project number

        Returns:
            string: unique checkpoint id
        """
        checkpoint_id = self._get_monitored_project + "_" + self._get_google_metric
        return re.sub(r"[^\w]+", "_", checkpoint_id)

    def _initialize_collection(self):
        """
        Prepare collection for checkpointing
        Load/Create the collection
        """
        server_uri = self._config["server_uri"]
        token = self._config["session_key"]
        appname = self._config["appName"]
        collection_name = self._get_collection_name()
        parts = urllib.parse.urlparse(server_uri)
        scheme = parts.scheme
        server_host = parts.hostname
        server_port = parts.port
        service = Service(
            scheme=scheme,
            host=server_host,
            port=server_port,
            token=token,
            owner="nobody",
            app=appname,
        )
        self._checkpoint = ckpt.CloudMonitorKVStore(
            collection_name=collection_name, service=service
        )
        self._checkpoint.get_collection()

    def _get_collection_name(self):
        """
        Get collection name
        """
        appname = self._config["appName"]
        google_service = self._config["google_service"]
        input_name = self._config["name"]
        return "_".join([appname, google_service, input_name])
