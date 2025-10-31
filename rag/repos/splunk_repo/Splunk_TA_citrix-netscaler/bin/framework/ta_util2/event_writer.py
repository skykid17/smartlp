#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import logging
import queue
import sys
import threading
import traceback

import ta_util2.log_files as log_files

_LOGGER = logging.getLogger(log_files.ta_util)


class EventWriter:
    def __init__(self):
        self._event_queue = queue.Queue()
        self._event_writer = threading.Thread(target=self._do_write_events)
        self._started = False
        self._stopped = False

    def start(self):
        if self._started:
            return
        self._started = True
        self._event_writer.start()
        _LOGGER.info("Event writer started.")

    def tear_down(self):
        if self._stopped:
            return
        self._stopped = True

        self._event_queue.put(None)
        self._event_writer.join()
        _LOGGER.info("Event writer stopped.")

    def write_events(self, events):
        if events is None:
            return

        self._event_queue.put(events)

    def _do_write_events(self):
        event_queue = self._event_queue
        write = sys.stdout.write
        flush = sys.stdout.flush
        while 1:
            event = event_queue.get()
            if event is not None:
                try:
                    write(event)
                except UnicodeEncodeError:
                    _LOGGER.critical(
                        "Events are not ingested. Possible cause could be a mismatch of event "
                        "character set with system-defined character set."
                    )
                except Exception:
                    _LOGGER.critical(
                        "Faced an unknown error while writing events. Traceback: %s",
                        traceback.format_exc(),
                    )
                flush()
            else:
                break
