#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function

from future import standard_library

standard_library.install_aliases()
import copy
import datetime
import json
import multiprocessing
import queue
import sys
import threading
import time
import traceback
from builtins import object, range, str
from collections.abc import Iterable

import splunktalib.common.util as scutil
import splunktalib.hec_config as hecc
import splunktalib.rest as sr
from six import string_types
from splunktalib.common import log, logger


class _ExtendedEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class ModinputEvent(object):

    base_fmt = (
        """<event{unbroken}>"""
        "<index>{index}</index>"
        "<host>{host}</host>"
        "<source>{source}</source>"
        "<sourcetype>{sourcetype}</sourcetype>"
        "<time>{time}</time>"
        "<data>{data}</data>{done}</event>"
    )

    event_fmt = base_fmt.replace("{unbroken}", "").replace("{done}", "")
    unbroken_fmt = base_fmt.replace("{unbroken}", ' unbroken="1"').replace("{done}", "")
    done_fmt = base_fmt.replace("{unbroken}", ' unbroken="1"').replace(
        "{done}", "<done/>"
    )

    def __init__(self, index, host, source, sourcetype, time, unbroken, done, events):
        self._string_events = self._format_events(
            index, host, source, sourcetype, time, events, unbroken, done
        )

    def _format_events(
        self, index, host, source, sourcetype, time, events, unbroken, done
    ):
        evt_fmt = self.event_fmt
        if done:
            evt_fmt = self.done_fmt
        elif unbroken:
            evt_fmt = self.unbroken_fmt

        if isinstance(events, (list, tuple)):
            dumps = json.dumps
            events = (dumps(evt) if isinstance(evt, dict) else evt for evt in events)
            res = "".join(
                (
                    self._do_format(evt, evt_fmt, index, host, source, sourcetype, time)
                    for evt in events
                )
            )
        elif isinstance(events, (str, str)):
            res = self._do_format(
                events, evt_fmt, index, host, source, sourcetype, time
            )
        elif isinstance(events, dict):
            events = json.dumps(events, cls=_ExtendedEncoder)
            res = self._do_format(
                events, evt_fmt, index, host, source, sourcetype, time
            )
        else:
            assert 0

        return "<stream>{}</stream>".format(res)

    def _do_format(self, evt, evt_fmt, index, host, source, sourcetype, time):
        evt = scutil.escape_cdata(evt)
        res = evt_fmt.format(
            index=index,
            host=host,
            source=source,
            sourcetype=sourcetype,
            time=time,
            data=evt,
        )
        return res

    def to_string(self):
        return self._string_events


class ModinputEventWriter(object):
    def __init__(self, process_safe=False):
        if process_safe:
            self._mgr = multiprocessing.Manager()
            self._event_queue = self._mgr.Queue(1000)
        else:
            self._event_queue = queue.Queue(1000)
        self._event_writer = threading.Thread(target=self._do_write_events)
        self._started = False

    def start(self):
        if self._started:
            return
        self._started = True

        self._event_writer.start()
        logger.info("ModinputEventWriter started.")

    def tear_down(self):
        if not self._started:
            return
        self._started = False

        self._event_queue.put(None)
        self._event_writer.join()
        logger.info("ModinputEventWriter stopped.")

    def write_events(self, events, retry=3):
        """
        :param evetns: list of ModinputEvent objects
        """

        if events is None:
            return

        self._event_queue.put(events)

    @staticmethod
    def create_event(index, host, source, sourcetype, time, unbroken, done, events):
        return ModinputEvent(
            index=index,
            host=host,
            source=source,
            sourcetype=sourcetype,
            time=time,
            unbroken=unbroken,
            done=done,
            events=events,
        )

    def _do_write_events(self):
        event_queue = self._event_queue
        write = sys.stdout.write
        got_shutdown_signal = False

        while 1:
            try:
                events = event_queue.get(timeout=3)
            except queue.Empty:
                # We need drain the queue before shutdown
                # timeout means empty for now
                if got_shutdown_signal:
                    logger.info("ModinputEventWriter is going to exit...")
                    break
                else:
                    continue

            if events is not None:
                if isinstance(events, (str, str)):
                    # for legacy interface
                    write(events)
                else:
                    for event in events:
                        write(event.to_string())
                    sys.stdout.flush()
            else:
                logger.info("ModinputEventWriter got tear down signal")
                got_shutdown_signal = True


class HecEventWriter(object):
    max_length = 52428800

    def __init__(self, config):
        """
        :params config: dict
        {
        "token": required,
        "hec_server_uri": required,
        "proxy_url": zz,
        "proxy_port": aa,
        "proxy_username": bb,
        "proxy_password": cc,
        "proxy_type": http,socks5,
        "proxy_rdns": 0 or 1,
        }
        """

        self._config = config
        self._max_event_size = int(config.get("max_hec_event_size", 1000000))
        self._http = config.get("http")
        self._compose_uri_headers(config)

    def _compose_uri_headers(self, config):
        self._uri = "{host}/services/collector".format(host=config["hec_server_uri"])
        self._headers = {
            "Authorization": "Splunk {}".format(config["token"]),
            "User-Agent": "curl/7.29.0",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        }

    def _prepare_events(self, events):
        """
        :param events: json dict list
        :return: a list string which contains strings and each string is less
        than 1000,000 bytes (HEC default)
        """

        size = 0
        all_events, batched = [], []
        for evt in events:
            if not evt["event"]:
                continue

            try:
                evt = json.dumps(evt)
            except ValueError:
                logger.error("Invalid json event=%s", evt)
                continue

            if size + len(evt) + 1 >= self._max_event_size:
                if batched:
                    all_events.append("\n".join(batched))
                del batched[:]
                size = 0
            batched.append(evt)
            size = size + len(evt) + 1

        if batched:
            all_events.append("\n".join(batched))
        return all_events

    def write_events(self, events, retry=3):
        """
        :params: events a list of json dict which meets HEC event schema
        {
        "event": xx,
        "index": yy,
        "host": yy,
        "source": yy,
        "sourcetype": yy,
        "time": yy,
        }
        Clients should consider batching, since when batching here, upper layer
        may have data loss
        """

        if not events:
            return

        last_ex = None
        events = self._prepare_events(events)
        for event in events:
            for _ in range(retry):
                try:
                    response, content = sr.splunkd_request(
                        self._uri,
                        self._config["token"],
                        method="POST",
                        headers=self._headers,
                        data=event,
                        http=self._http,
                    )

                    if response is None:
                        logger.error(
                            "Failed to write events through HEC, plese make "
                            "sure http event collector is enabled and consult "
                            "util.log for more details"
                        )
                        time.sleep(2)
                        continue

                    if response.status in (200, 201):
                        last_ex = None
                        break
                    else:
                        msg = (
                            "Failed to post events to HEC_URI={}, "
                            "error_code={}, reason={}"
                        ).format(self._uri, response.status, content)
                        logger.error(msg)
                        handled = self._handle_too_large_error(
                            event, response.status, content
                        )
                        if not handled:
                            last_ex = None
                            break

                        # We raise here to commonly use the below code block
                        raise Exception(msg)
                except Exception as e:
                    last_ex = e
                    logger.error(
                        "Failed to post events to HEC_URI=%s, error=%s",
                        self._uri,
                        traceback.format_exc(),
                    )
                    time.sleep(2)

        if last_ex is not None:
            raise last_ex

    def start(self):
        pass

    def tear_down(self):
        pass

    @staticmethod
    def create_event(index, host, source, sourcetype, time, unbroken, done, events):
        keys = [index, host, source, sourcetype, time]
        for i, key in enumerate(keys):
            if not key:
                keys[i] = None
        index, host, source, sourcetype, time = keys

        return {
            "index": index,
            "host": host,
            "source": source,
            "sourcetype": sourcetype,
            "time": time,
            "event": events,
        }

    def _handle_too_large_error(self, event, status, content):
        if status == 413 and "too large" in content:
            hcc = hecc.HECConfig(
                self._config["server_uri"], self._config["session_key"]
            )
            limits = hcc.get_limits()
            new_limit = {"max_content_length": int(limits["max_content_length"]) * 2}
            if new_limit["max_content_length"] < self.max_length:
                hcc.set_limits(new_limit)
                return True
            else:
                # Each event should not exceed 25 MB
                logger.error("Event is too bigger. Drop event=%s", event)
                return False


class RawHecEventWriter(HecEventWriter):
    def __init__(self, config):
        """
        :param: config should meet HecEventWriter param and include
        "channel"
        """

        super(RawHecEventWriter, self).__init__(config)

    def _compose_uri_headers(self, config):
        self._uri = "{host}/services/collector/raw".format(
            host=config["hec_server_uri"]
        )
        self._headers = {
            "Authorization": "Splunk {}".format(config["token"]),
            "User-Agent": "curl/7.29.0",
            "Connection": "keep-alive",
            "x-splunk-request-channel": "{}".format(config["channel"]),
        }

    def _prepare_events(self, events):
        """
        :param events: string
        """

        # FIXME source, sourcetype etc

        return events


def create_event_writer(config, process_safe=False, use_proxy=False):
    if not use_proxy:
        config = copy.copy(config)
        config["proxy_url"] = None

    if scutil.is_true(config.get("use_hec")):
        config["http"] = sr.HttpPoolManager(config).pool()
        return HecEventWriter(config)
    elif scutil.is_true(config.get("use_raw_hec")):
        config["http"] = sr.HttpPoolManager(config).pool()
        return RawHecEventWriter(config)
    else:
        return ModinputEventWriter(process_safe=process_safe)


if __name__ == "__main__":
    all_events = [["i love you"], ["1", "2", "3"]]

    index_events = []
    for events in all_events:
        for unbroken in (1, 0):
            for done in (0, 1):
                evt = ModinputEvent(
                    index="main",
                    host="localhost",
                    source="test",
                    sourcetype="test:json",
                    time=time.time(),
                    unbroken=unbroken,
                    done=done,
                    events=events,
                )
                index_events.append(evt)
                print(evt.to_string())

    print("\n\n")
    writer = ModinputEventWriter()
    writer.start()
    writer.write_events(index_events)
    writer.tear_down()

    print("\n\n")
    writer = ModinputEventWriter(process_safe=True)
    writer.start()
    writer.write_events(index_events)
    writer.tear_down()

    import uuid

    config = {
        "hec_server_uri": "https://localhost:8088",
        "token": "139979A1-C8DD-42AF-9A8E-A2E91E7D0440",
        "channel": str(uuid.uuid4()),
    }

    writer = HecEventWriter(config)
    event = {
        "index": "main",
        "source": "hec_test",
        "sourcetype": "hec:test",
        "event": "i love you",
        "time": time.time(),
    }

    writer.write_events([event] * 10)


class EventWriter(object):
    def __init__(self, process_safe=False):
        if process_safe:
            self._mgr = multiprocessing.Manager()
            self._event_queue = self._mgr.Queue(1000)
        else:
            self._event_queue = queue.Queue(1000)
        self._event_writer = threading.Thread(target=self._do_write_events)
        self._event_writer.daemon = True
        self._started = False
        self._exception = False

    def start(self):
        if self._started:
            return
        self._started = True

        self._event_writer.start()
        log.logger.info("Event writer started.")

    def tear_down(self):
        if not self._started:
            return
        self._started = False

        self._event_queue.put(None)
        self._event_writer.join()
        log.logger.info("Event writer stopped.")

    def isopen(self):
        return self._started and (not self._exception)

    def write_events(self, events):
        if not self.isopen():
            return False
        if events is None:
            return True
        self._event_queue.put(events)
        return True

    def _do_write_events(self):
        event_queue = self._event_queue
        write = sys.stdout.write
        got_shutdown_signal = False

        while 1:
            try:
                event = event_queue.get(timeout=3)
                if event is not None:
                    if isinstance(event, string_types):
                        write(event.encode("utf-8"))
                    elif isinstance(event, Iterable):
                        for evt in event:
                            write(evt.encode("utf-8"))
                else:
                    log.logger.info("Event writer got tear down signal")
                    got_shutdown_signal = True
            except queue.Empty:
                # We need drain the queue before shutdown
                # timeout means empty for now
                if got_shutdown_signal:
                    log.logger.info("Event writer is going to exit...")
                    break
                else:
                    continue
            except Exception:
                log.logger.exception(
                    "EventWriter encounter exception which may"
                    "cause data loss, queue leftsize={"
                    "}".format(event_queue.qsize())
                )
                self._exception = True
                break

        log.logger.info(
            "Event writer stopped, queue leftsize={}".format(event_queue.qsize())
        )


class EventWriterWithCheckpoint(EventWriter):
    def _do_write_events(self):
        event_queue = self._event_queue
        write = sys.stdout.write
        got_shutdown_signal = False

        while 1:
            try:
                event = event_queue.get(timeout=3)
                if event is not None:
                    # event is a tuple which consists of events and checkpoint
                    # information: (events, checkpoint_tuple)
                    # checkpoint_tuple includes the checkpoint manager obj, key
                    # and value of checkpoint: (ckpt_mgr_obj, key, state)
                    events = event[0]
                    ckpt_tuple = event[1]
                    if isinstance(events, string_types):
                        write(events.encode("utf-8"))
                    elif isinstance(events, Iterable):
                        for evt in events:
                            write(evt.encode("utf-8"))

                    # Update checkpoint after events are sent to stdout to avoid
                    # data loss.
                    if ckpt_tuple and ckpt_tuple[2]:
                        ckpt_tuple[0].update_state(ckpt_tuple[1], ckpt_tuple[2])

                    # Close the checkpoint obj to flush the data in cache to
                    # disk to aviod data duplication if it is teared down
                    if not self._started:
                        ckpt_tuple[0].close()
                else:
                    log.logger.info("Event writer got tear down signal")
                    got_shutdown_signal = True

            except queue.Empty:
                # We need drain the queue before shutdown
                # timeout means empty for now
                if got_shutdown_signal:
                    log.logger.info("Event writer is going to exit...")
                    break
                else:
                    continue
            except Exception:
                log.logger.exception(
                    "EventWriter encounter exception which may"
                    "cause data loss, queue leftsize={"
                    "}".format(event_queue.qsize())
                )
                self._exception = True
                break

        log.logger.info(
            "Event writer stopped, queue leftsize={}".format(event_queue.qsize())
        )
