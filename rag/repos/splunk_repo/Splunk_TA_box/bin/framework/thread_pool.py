#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import traceback
import configparser as ConfigParser
import log_files
from queue import Queue
import threading
import os.path as op

from solnlib import log

_LOGGER = log.Logs().get_logger(log_files.ta_box)


def read_default_settings():
    cur_dir = op.dirname(op.abspath(__file__))
    setting_file = op.join(cur_dir, "setting.conf")
    parser = ConfigParser.ConfigParser()
    parser.read(setting_file)
    settings = {}
    for option in ("thread_num", "queue_maxsize"):
        try:
            settings[option] = parser.get("global", option)
        except ConfigParser.NoOptionError:
            settings[option] = -1

        if settings[option] == "dynamic":
            settings[option] = -1

        try:
            settings[option] = int(settings[option])
        except ValueError:
            settings[option] = -1
    _LOGGER.debug("settings:%s", settings)
    return settings


# Thread-safe queue for managing tasks
_settings = read_default_settings()
task_queue = Queue(maxsize=_settings.get("queue_maxsize"))


class WorkerThread(threading.Thread):
    """Custom worker thread that processes tasks from the queue."""

    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.daemon = True  # Set the thread as a daemon thread
        self.running = True

    def run(self):
        while self.running:
            try:
                task = self.queue.get()  # Get a task from the queue
                if task is None:  # Stop signal
                    break
                task.run()  # Execute the task
            except Exception as e:
                _LOGGER.error("Error processing task: %s", e)
                _LOGGER.debug("Stack trace: %s", traceback.format_exc())
            finally:
                self.queue.task_done()  # Mark the task as done

    def stop(self):
        """Stop the worker thread."""
        self.running = False
        self.queue.put(None)  # Signal the thread to stop


class CustomThreadPool:
    """Custom thread pool using threading.Thread."""

    def __init__(self, num_threads, queue):
        self.num_threads = num_threads
        self.queue = queue
        self.threads = []

    def start(self):
        """Start the thread pool."""
        _LOGGER.debug("Starting thread pool with %d threads.", self.num_threads)
        for _ in range(self.num_threads):
            worker = WorkerThread(self.queue)
            worker.start()
            self.threads.append(worker)

    def stop(self):
        """Stop the thread pool gracefully."""
        _LOGGER.debug("Stopping thread pool...")
        for thread in self.threads:
            thread.stop()  # Signal all threads to stop
        for thread in self.threads:
            thread.join()  # Wait for all threads to finish
        _LOGGER.debug("Thread pool has been stopped.")

    def wait_for_completion(self):
        """Wait for all tasks in the queue to be processed."""
        self.queue.join()


# Create the thread pool
pool_executor = CustomThreadPool(
    num_threads=_settings.get("thread_num"), queue=task_queue
)


def start_thread_pool(rest_endpoint):
    """Start the thread pool."""
    if rest_endpoint == "folders":
        global pool_executor
        pool_executor.start()


def stop_thread_pool(rest_endpoint):
    """Stop the thread pool gracefully."""
    if rest_endpoint == "folders":
        global pool_executor
        pool_executor.wait_for_completion()
        pool_executor.stop()
