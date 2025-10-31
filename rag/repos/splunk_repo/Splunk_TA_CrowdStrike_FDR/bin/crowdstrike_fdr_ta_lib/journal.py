#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import random
import traceback
from threading import Thread, Event, Lock
from time import time, sleep
from collections import namedtuple
from typing import Optional, Union, Tuple, Callable, Dict, List, Any
from requests import Response

import solnlib

from .abort_signal import (
    AbortSignalException,
)
from .constants import (
    JOURNAL_COLLECTION_NAME,
    JOURNAL_HEARTBEAT_INTERVAL,
    JOURNAL_MAX_TASK_ATTEMPTS,
    JOURNAL_MONITOR_INTERVAL,
    JOURNAL_REG_TTL,
)
from .kvstore_collection import KVStoreCollection, KVStoreApiError

DEBUG_DUMP_JOURNAL = False
DEBUG_DUMP_JOURNAL_GROUP = False

from .logger_adapter import CSLoggerAdapter

logger = CSLoggerAdapter(
    solnlib.log.Logs().get_logger("splunk_ta_crowdstrike_fdr").getChild("journal")
)

RECORD_TYPES = namedtuple("RecordTypesEnum", "reg task")(reg="REG", task="TASK")  # type: ignore

RECORD_FIELDS = namedtuple(  # type: ignore
    "RecordFieldsEnum",
    "record_type shared_group owner assignment started time status data traceback_msg",
)(
    record_type="record_type",
    shared_group="shared_group",
    owner="owner",
    assignment="assignment",
    started="started",
    time="time",
    status="status",
    data="data",
    traceback_msg="traceback_msg",
)

ACTOR_TYPES = namedtuple("ActorTypesEnum", "manager worker")(  # type: ignore
    manager="manager", worker="worker"
)

ACTOR_STATUS = namedtuple("ActorStatusEnum", "init ready busy done failed")(  # type: ignore
    init="init", ready="ready", busy="busy", done="done", failed="failed"
)

TASK_STATUS = namedtuple("TaskStatusEnum", "new assigned failed retry done fatal")(  # type: ignore
    new="new",
    assigned="assigned",
    failed="failed",
    retry="retry",
    done="done",
    fatal="fatal",
)

JOURNAL_SCHEMA = {
    f"field.{RECORD_FIELDS.record_type}": "string",  # type: ignore
    f"field.{RECORD_FIELDS.shared_group}": "string",  # type: ignore
    f"field.{RECORD_FIELDS.owner}": "string",  # type: ignore
    f"field.{RECORD_FIELDS.assignment}": "string",  # type: ignore
    f"field.{RECORD_FIELDS.started}": "time",  # type: ignore
    f"field.{RECORD_FIELDS.time}": RECORD_FIELDS.time,  # type: ignore
    f"field.{RECORD_FIELDS.status}": "string",  # type: ignore
    f"field.{RECORD_FIELDS.data}": "string",  # type: ignore
    f"field.{RECORD_FIELDS.traceback_msg}": "string",  # type: ignore
}


def process_general_exception(message: str, e: Exception) -> None:
    msg = f"{message}: {e}"
    tb = " ---> ".join(traceback.format_exc().split("\n"))
    solnlib.log.log_exception(logger, e, "Journal Error", msg_before=f"{msg} {tb}")


class JournalBase:
    def __init__(
        self,
        server_uri: str,
        app: str,
        token: str,
        group: Any,
        owner: str,
        stopper_fn: Callable,
    ):
        self._state_update_lock = Lock()
        self._heartbeat_stop_event = Event()
        self.stopper_fn = stopper_fn

        self._journal = KVStoreCollection(
            server_uri, token, app, JOURNAL_COLLECTION_NAME
        )
        self._reg_id = None
        self._registered = False
        self._heartbeat = None
        self._heartbeat_fails = 0

        self.group = group
        self.owner = owner
        self.assignment = self.__class__.__name__
        self.started = time()

        self.status = None
        self.data = None
        self.traceback_msg = None

    def _get_journal(self, can_create_journal: bool = False) -> Optional[bool]:
        start_time = time()
        while time() - start_time < 10:
            try:
                logger.debug(f"{self.owner} Getting journal collection ...")
                if not self._journal.check_collection_exists():
                    if can_create_journal:
                        self._journal.create_collection()
                        self._journal.define_collection_schema(JOURNAL_SCHEMA)
                    sleep(1)
                    continue
                logger.debug(f"{self.owner} Got journal collection")
                return True
            except KVStoreApiError:
                sleep(1)
                continue
            except Exception as e:
                process_general_exception(
                    f"{self.owner} Failed to get journal collection:", e
                )
                raise

        timeout_err_msg = f"{self.owner} has run out of time trying to retrieve or create journal collection"
        solnlib.log.log_exception(
            logger,
            Exception(timeout_err_msg),
            "Journal Error",
            msg_before=timeout_err_msg,
        )
        raise Exception(timeout_err_msg)

    def _drop_journal(self) -> None:
        logger.info(f"{self.owner} Deleting collection ...")
        self._journal.delete_collection()

    def _debug_dump_journal(self) -> None:
        if DEBUG_DUMP_JOURNAL:
            res = self._journal.search_records()
            logger.debug(f"{self.owner} JOURNAL DUMP: {json.dumps(res)}")

    def _debug_dump_journal_group(self) -> None:
        if DEBUG_DUMP_JOURNAL_GROUP:
            query = json.dumps({RECORD_FIELDS.shared_group: self.group})
            res = self._journal.search_records(query=query)
            logger.debug(
                f"{self.owner} GROUP {self.group} JOURNAL DUMP: {json.dumps(res)}"
            )

    @property
    def is_registered(self) -> bool:
        return self._registered

    @staticmethod
    def diff_tasks(task1: Dict[str, Any], task2: Dict[str, Any]) -> Dict[str, Any]:
        res = {}
        for k, v in task1.items():
            if v != task2.get(k):
                res[k] = f"{v} -> {task2.get(k)}"
        for k, v in task2.items():
            if task1.get(k) != v:
                res[k] = f"{task1.get(k)} -> {v}"
        return res

    def update_task(self, task: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Updates task dict object with new values passed as optional named arguments via kwargs.
        Only "assignment", "status", "data" and "traceback_msg" argument values are taken into account, other arguments passed via kwargs are ignored.
        Updates task journal record with the new state of the task

        Args:
            task (dict): object representing task current state
            **kwargs (dict): named argumants representing the changes required in task

        Returns:
            dict: object representing the task new state
        """
        updatable_fields = [
            RECORD_FIELDS.assignment,
            RECORD_FIELDS.status,
            RECORD_FIELDS.data,
            RECORD_FIELDS.traceback_msg,
        ]

        # extracts values that are allowed to be changed
        changes = {k: v for k, v in kwargs.items() if k in updatable_fields}
        # sets time of record update
        changes[RECORD_FIELDS.time] = time()

        # builds task current state object
        state = {
            RECORD_FIELDS.record_type: RECORD_TYPES.task,
            RECORD_FIELDS.shared_group: self.group,
            RECORD_FIELDS.owner: self.owner,
            RECORD_FIELDS.assignment: task.get(RECORD_FIELDS.assignment),
            RECORD_FIELDS.started: task.get(RECORD_FIELDS.started),
            RECORD_FIELDS.status: task.get(RECORD_FIELDS.status),
            RECORD_FIELDS.data: task.get(RECORD_FIELDS.data),
            RECORD_FIELDS.traceback_msg: task.get(RECORD_FIELDS.traceback_msg),
        }

        # logs change difference map for debug purposes
        diff = {k: f"{state.get(k)} => {v}" for k, v in changes.items()}
        logger.debug(f"{self.owner}, TASK state diff: {diff}")

        # updates state object with changes
        state.update(changes)
        # updates journal record with state changes
        self._journal.update_record(task["_key"], state)
        self._debug_dump_journal()
        return state

    def update_reg(self, **kwargs: Any) -> Dict[str, Any]:
        """Updates journal actor registration state object (self) with new values passed as optional named arguments via kwargs.
        Only "status", "data", "traceback_msg" and "started" argument values are taken into account, other arguments passed via kwargs are ignored.
        Updates actor journal record with the new state

        Args:
            **kwargs: named argumants representing the changes required in the worker/actor

        Returns:
            dict: object representing the actor new state
        """
        updatable_fields = [
            RECORD_FIELDS.status,
            RECORD_FIELDS.data,
            RECORD_FIELDS.traceback_msg,
            RECORD_FIELDS.started,
        ]

        # extracts values that are allowed to be changed
        changes = {k: v for k, v in kwargs.items() if k in updatable_fields}
        # sets time of record update
        changes[RECORD_FIELDS.time] = time()

        # builds actor current state object
        state = {
            RECORD_FIELDS.record_type: RECORD_TYPES.reg,
            RECORD_FIELDS.shared_group: self.group,
            RECORD_FIELDS.owner: self.owner,
            RECORD_FIELDS.assignment: self.assignment,
            RECORD_FIELDS.started: self.started,
            RECORD_FIELDS.status: self.status,
            RECORD_FIELDS.data: self.data,
            RECORD_FIELDS.traceback_msg: self.traceback_msg,
        }

        # logs change difference map for debug purposes
        diff = {k: f"{state.get(k)} => {v}" for k, v in changes.items()}
        logger.debug(f"{self.owner}, REG state diff: {diff}")

        # updates state object with changes
        state.update(changes)
        # locks and updates self object with state changes
        with self._state_update_lock:
            for k, v in changes.items():
                setattr(self, k, v)

        # updates journal record with state changes or creates a new record
        if self._reg_id is None:
            self._reg_id = self._journal.create_record(state)
            logger.debug(
                f"{self.owner}, created new journal REG record: {self._reg_id}"
            )
        else:
            self._journal.update_record(self._reg_id, state)

        self._debug_dump_journal()
        return state

    def recover(self) -> bool:
        res = self._journal.search_records(
            query={
                RECORD_FIELDS.record_type: RECORD_TYPES.reg,
                RECORD_FIELDS.shared_group: self.group,
                RECORD_FIELDS.owner: self.owner,
                RECORD_FIELDS.assignment: self.assignment,
            }
        )

        logger.info(f"{self.owner} Recovered record: {res}")

        if res:
            self._reg_id = res[0].get("_key")
            return True

        return False

    def register(self, can_create_journal: bool = False, **opt: str) -> bool:
        if not self._get_journal(can_create_journal):
            logger.warning(f'{self.owner} journal_error="Failed to access journal"')
            return False

        if self.recover():
            logger.info(f"{self.owner} Recovered journal registration: {self._reg_id}")

        if RECORD_FIELDS.status not in opt:
            opt[RECORD_FIELDS.status] = ACTOR_STATUS.init

        self.update_reg(**opt)
        if not self._reg_id:
            logger.warning(
                f'{self.owner} journal_error="Failed to create/recover journal registration record"'
            )
            return False

        self._heartbeat_fails = 0
        self._heartbeat = Thread(target=self.keep_alive, name="HeartbeatThread")
        self._heartbeat.start()
        self._registered = True
        logger.info(f"{self.owner} REGISTERED with id {self._reg_id}")
        return True

    def unregister(self) -> None:
        if self._heartbeat:
            self._heartbeat_stop_event.set()
            self._heartbeat.join()

        if self._journal:
            self._journal.delete_records(key=self._reg_id)
            logger.info(f"{self.owner} UNREGISTERED with id {self._reg_id}")

        self._registered = False

    def set_ready(self) -> None:
        logger.info(f"{self.owner} is READY!")
        self.update_reg(status=ACTOR_STATUS.ready)

    def keep_alive(self) -> None:
        sleep(random.random())
        logger.info(f"{self.owner} heartbeat {self._reg_id} started")
        try:
            while not self._heartbeat_stop_event.wait(JOURNAL_HEARTBEAT_INTERVAL):
                try:
                    state = self.update_reg()
                    self._heartbeat_fails = 0
                    logger.debug(
                        f"{self.owner} heartbeat {self._reg_id} update {state[RECORD_FIELDS.time]}"
                    )
                except Exception as e:
                    self._heartbeat_fails += 1
                    msg = f"{self.owner} heartbeat {self._reg_id} fail_count: {self._heartbeat_fails}, error: {e}"
                    tb = " ---> ".join(traceback.format_exc().split("\n"))
                    solnlib.log.log_exception(
                        logger, e, "Heartbeat Error", msg_before=f"{msg} {tb}"
                    )
        finally:
            logger.info(f"{self.owner} heartbeat {self._reg_id} stopped")

    @staticmethod
    def is_numb(actor: Dict[str, Any]) -> bool:
        heartbeat_age = time() - actor[RECORD_FIELDS.time]
        return heartbeat_age > 1.1 * JOURNAL_HEARTBEAT_INTERVAL

    def query_task(self, query_args: Dict[str, Any]) -> Dict[str, Any]:
        query = {
            RECORD_FIELDS.record_type: RECORD_TYPES.task,
            RECORD_FIELDS.shared_group: self.group,
        }
        query.update(query_args)
        return query

    def query_reg(self, query_args: Dict[str, Any]) -> Dict[str, Any]:
        query = {
            RECORD_FIELDS.time: {"$gt": time() - JOURNAL_REG_TTL},
            RECORD_FIELDS.record_type: RECORD_TYPES.reg,
            RECORD_FIELDS.shared_group: self.group,
        }
        query.update(query_args)
        return query

    def search_journal(
        self, *queries: Dict[str, Any], bind_op: Union[str, List[Any]] = "$or"
    ) -> Optional[List[Dict[str, Any]]]:
        if not queries:
            return []

        logger.debug(f"{self.owner} Query DUMP: {queries}")

        if len(queries) == 1:
            return self._journal.search_records(query=queries[0])

        return self._journal.search_records(query={bind_op: list(queries)})

    def check_tasks_statuses(
        self, query: Dict[str, Any] = {}, patterns: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        tasks = self.search_journal(self.query_task(query))

        by_status = {}
        for task in tasks:
            for field, pattern in patterns.items():
                if not pattern.match(task.get(field) or ""):
                    break
            else:
                status = task[RECORD_FIELDS.status]
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(task)

        return by_status

    def run(self, interval: int = 5) -> None:
        logger.info(f"{self.owner} is RUNNING")
        try:
            self.set_ready()
            while True:
                if self.stopper_fn and self.stopper_fn():
                    raise AbortSignalException()

                if self._heartbeat_fails >= 3:
                    raise KVStoreApiError(
                        "{self.owner} Repetitive journal heartbeat update problem. Journal kvstore may not be available."
                    )

                iter_started = time()
                self.iterate()
                iter_time_taken = time() - iter_started
                wait_interval = interval - iter_time_taken
                if wait_interval < 0.5:
                    wait_interval = 0.5
                logger.debug(
                    f"{self.owner} Iteration time taken: {iter_time_taken}, reserved interval: {interval}, "
                    + f"sleep planed: {wait_interval}"
                )
                sleep(wait_interval)
        except AbortSignalException:
            logger.warning(
                f"{self.owner} Stopping input as abort signal has been received."
            )
        except (StopIteration, KeyboardInterrupt):
            logger.info(
                f"{self.owner} has recieved stop iteration signal and is stopping ..."
            )
        except Exception as e:
            msg = f"{self.owner} input error: {e}"
            tb = " ---> ".join(traceback.format_exc().split("\n"))
            solnlib.log.log_exception(
                logger, e, "Input error", msg_before=f"{msg} {tb}"
            )
        finally:
            self.unregister()

    def iterate(self):
        pass


class ManagerJournal(JournalBase):
    def __init__(self, server_uri, app, token, group, owner, stopper_fn):
        super(ManagerJournal, self).__init__(
            server_uri, app, token, group, owner, stopper_fn
        )
        self.assignment = ACTOR_TYPES.manager

        self._journal_monitor_stop_event = Event()
        self._journal_monitor = None

    def register(self, can_create_journal: bool = False, **opt: str) -> None:
        if not super(ManagerJournal, self).register(can_create_journal, **opt):
            return

        self._journal_monitor = Thread(
            target=self.journal_monitor_executor, name="JournalMonitorThread"
        )
        self._journal_monitor.start()

    def unregister(self) -> None:
        logger.info(f"{self.owner} SQS manager unregister")
        super(ManagerJournal, self).unregister()

        self._journal_monitor_stop_event.set()
        self._journal_monitor.join()

    def journal_monitor_executor(self) -> None:
        try:
            sleep(random.random())
            logger.info(
                f"{self.owner} has started journal monitor with check interval {JOURNAL_MONITOR_INTERVAL}"
            )
            while True:
                try:
                    workers, tasks = self.list_workers_and_all_tasks()
                    logger.debug(
                        f"{self.owner} manager found {len(tasks)} active tasks and {len(workers)} available workers"
                    )
                    self.on_journal_monitor(workers, tasks)

                    if self._journal_monitor_stop_event.wait(JOURNAL_MONITOR_INTERVAL):
                        break
                except Exception as e:
                    process_general_exception(f"{self.owner} monitor exception: ", e)
        finally:
            logger.info(f"{self.owner} journal monitor stopped")

    def on_journal_monitor(
        self, workers: Dict[str, Any], tasks: List[Dict[str, Any]]
    ) -> None:
        # Dummy handler for journal monitor
        pass

    def on_task_state_change(self, old_state: Any, new_state: Any) -> None:
        # Dummy handler for tasks state change
        pass

    def on_start_iteration(self, workers: Any, tasks: Any) -> None:
        # Dummy handler for start iteration: workers
        pass

    def list_manager_tasks(self) -> Optional[List[Dict[str, Any]]]:
        return self.search_journal(self.query_task({RECORD_FIELDS.owner: self.owner}))

    def check_tasks_statuses(
        self, query: Dict[str, Any] = {}, patterns: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        manager_tasks = {RECORD_FIELDS.owner: self.owner}
        manager_tasks.update(query)
        return super(ManagerJournal, self).check_tasks_statuses(manager_tasks, patterns)

    def append_tasks(self, data_list: list) -> None:
        for task_data in data_list:
            self.create_task(task_data)

    def create_task(
        self, data: Union[Dict[str, Any], str, None], worker_id: Optional[str] = None
    ) -> str:
        task = {
            RECORD_FIELDS.record_type: RECORD_TYPES.task,
            RECORD_FIELDS.shared_group: self.group,
            RECORD_FIELDS.owner: self.owner,
            RECORD_FIELDS.assignment: worker_id,
            RECORD_FIELDS.started: time(),
            RECORD_FIELDS.time: time(),
            RECORD_FIELDS.status: TASK_STATUS.new,
            RECORD_FIELDS.data: data,
            RECORD_FIELDS.traceback_msg: None,
        }
        task_id = self._journal.create_record(task)
        logger.info(f"{self.owner} Created task {json.dumps(task)} with id {task_id}")
        return task_id

    def assign_task(self, task: Dict[str, Any], worker_id: str) -> Dict[str, Any]:
        task_update = {
            RECORD_FIELDS.record_type: RECORD_TYPES.task,
            RECORD_FIELDS.shared_group: self.group,
            RECORD_FIELDS.owner: self.owner,
            RECORD_FIELDS.assignment: worker_id,
            RECORD_FIELDS.started: task[RECORD_FIELDS.started],
            RECORD_FIELDS.time: time(),
            RECORD_FIELDS.status: TASK_STATUS.assigned,
            RECORD_FIELDS.data: task[RECORD_FIELDS.data],
            RECORD_FIELDS.traceback_msg: None,
        }
        self._journal.update_record(task["_key"], task_update)
        logger.info(f"{self.owner} Assigned task {json.dumps(task)} to {worker_id}")
        return task_update

    def delete_tasks(self, tasks: list) -> None:
        task_ids = [task["_key"] if isinstance(task, dict) else task for task in tasks]
        res = self._journal.delete_records(key=task_ids)
        logger.info(f"{self.owner} Deleted task ids {task_ids}: {res}")

    def delete_task(self, task: Dict[str, Any]) -> None:
        task_id = task["_key"] if isinstance(task, dict) else task
        res = self._journal.delete_records(key=task_id)
        logger.info(f"{self.owner} Deleted task id {task_id}: {res}")

    def delete_manager_tasks(self) -> None:
        res = self._journal.delete_records(
            query=self.query_task({RECORD_FIELDS.owner: self.owner})
        )
        logger.info(f"{self.owner} Deleted manager tasks: {res}")

    def list_workers_and_active_tasks(
        self,
    ) -> Tuple[Dict[Any, Dict[str, Any]], List[Dict[str, Any]]]:
        res = self.search_journal(
            self.query_reg(
                {
                    RECORD_FIELDS.assignment: ACTOR_TYPES.worker,
                }
            ),
            self.query_task(
                {
                    RECORD_FIELDS.owner: self.owner,
                    "$or": [
                        {RECORD_FIELDS.status: TASK_STATUS.new},
                        {RECORD_FIELDS.status: TASK_STATUS.assigned},
                        {RECORD_FIELDS.status: TASK_STATUS.retry},
                    ],
                }
            ),
        )

        workers, tasks = {}, []
        for r in res:
            if r[RECORD_FIELDS.record_type] == RECORD_TYPES.task:
                tasks.append(r)
            elif r[RECORD_FIELDS.record_type] == RECORD_TYPES.reg:
                workers[r[RECORD_FIELDS.owner]] = r

        logger.debug(f"{self.owner}, group worker list: {workers}")
        logger.debug(f"{self.owner}, group active task list: {tasks}")
        return workers, tasks

    def list_workers_and_all_tasks(
        self,
    ) -> Tuple[Dict[Any, Dict[str, Any]], List[Dict[str, Any]]]:
        res = self.search_journal(
            self.query_reg(
                {
                    RECORD_FIELDS.assignment: ACTOR_TYPES.worker,
                }
            ),
            self.query_task(
                {
                    RECORD_FIELDS.owner: self.owner,
                }
            ),
        )

        workers, tasks = {}, []
        for r in res:
            if r[RECORD_FIELDS.record_type] == RECORD_TYPES.task:
                tasks.append(r)
            elif r[RECORD_FIELDS.record_type] == RECORD_TYPES.reg:
                workers[r[RECORD_FIELDS.owner]] = r

        logger.debug(f"{self.owner}, group worker list: {workers}")
        logger.debug(f"{self.owner}, group all task list: {tasks}")
        return workers, tasks

    def handle_task_error(self, task: Dict[str, Any], error: str) -> None:
        errors = json.loads(task.get(RECORD_FIELDS.traceback_msg) or "[]")
        errors.append(
            {
                RECORD_FIELDS.assignment: task[RECORD_FIELDS.assignment],
                RECORD_FIELDS.time: time(),
                RECORD_FIELDS.traceback_msg: error,
            }
        )

        if error is None:
            logger.warning(f"{self.owner} traceback_msg from worker is None")
            status = TASK_STATUS.retry
        elif error.startswith("(unrecoverable)"):
            status = TASK_STATUS.fatal
        elif len(errors) >= JOURNAL_MAX_TASK_ATTEMPTS:
            status = TASK_STATUS.failed
        else:
            status = TASK_STATUS.retry

        new_state = self.update_task(
            task, status=status, assignment=None, traceback_msg=json.dumps(errors)
        )
        self.on_task_state_change(task, new_state)

    def iterate(self) -> None:
        logger.debug(f"{self.owner} - iterate, status: {self.status}")
        super(ManagerJournal, self).iterate()

        ready_workers = []
        workers, tasks = self.list_workers_and_active_tasks()
        self.on_start_iteration(workers, tasks)
        for worker_id, worker in workers.items():
            assigned_tasks = {
                t["_key"]: t for t in tasks if t[RECORD_FIELDS.assignment] == worker_id
            }
            if worker[RECORD_FIELDS.status] == ACTOR_STATUS.done:
                task = assigned_tasks.pop(worker[RECORD_FIELDS.data], None)
                if task:
                    new_state = self.update_task(task, status=TASK_STATUS.done)
                    self.on_task_state_change(task, new_state)
            elif worker[RECORD_FIELDS.status] == ACTOR_STATUS.failed:
                task = assigned_tasks.pop(worker[RECORD_FIELDS.data], None)
                if task is not None:
                    self.handle_task_error(task, worker[RECORD_FIELDS.traceback_msg])
            elif worker[RECORD_FIELDS.status] == ACTOR_STATUS.ready:
                ready_workers.append(worker_id)

        for task in tasks:
            worker_id = task[RECORD_FIELDS.assignment]
            if task[RECORD_FIELDS.status] == TASK_STATUS.assigned:
                if worker_id not in workers:
                    error = f"{self.owner}: worker {worker_id} appears inactive!"
                    self.handle_task_error(task, error)
                elif worker_id in ready_workers:
                    ready_workers.remove(worker_id)

        for task in tasks:
            if (
                task[RECORD_FIELDS.status] in (TASK_STATUS.new, TASK_STATUS.retry)
                and ready_workers
            ):
                worker_id = ready_workers.pop()
                new_state = self.update_task(
                    task,
                    status=TASK_STATUS.assigned,
                    assignment=worker_id,
                )
                self.on_task_state_change(task, new_state)


class WorkerJournal(JournalBase):
    def __init__(
        self,
        server_uri: str,
        app: str,
        token: str,
        group: Any,
        manager,
        owner,
        stopper_fn,
    ):
        super(WorkerJournal, self).__init__(
            server_uri, app, token, group, owner, stopper_fn
        )
        self.manager = manager
        self.assignment = ACTOR_TYPES.worker

    def handle_task_execute(self, task: Any) -> None:
        # Dummy task execute
        error = None
        return error

    def find_manager(self, attempts: int = 1) -> Optional[Dict[str, Any]]:

        self._debug_dump_journal()

        res = {}
        for attempt in range(attempts):
            logger.info(
                f"{self.owner} is looking for assigned manager, attempt {attempt+1}"
            )
            res = self.search_journal(
                self.query_reg(
                    {
                        RECORD_FIELDS.owner: self.manager,
                        RECORD_FIELDS.assignment: ACTOR_TYPES.manager,
                        RECORD_FIELDS.status: ACTOR_STATUS.ready,
                    }
                )
            )

            if len(res) > 0:
                break

        if len(res) == 0:
            return None

        if len(res) > 1:
            logger.warning(f"{self.owner}, too many managers records found: {res}")
        else:
            logger.info(f"{self.owner}, manager {self.manager} record found: {res[0]}")

        return res[0]

    def list_assigned_tasks(self) -> Optional[List[Dict[str, Any]]]:
        tasks = self.search_journal(
            self.query_task(
                {
                    RECORD_FIELDS.owner: self.manager,
                    RECORD_FIELDS.assignment: self.owner,
                    RECORD_FIELDS.status: TASK_STATUS.assigned,
                }
            ),
        )

        logger.debug(f"{self.owner}, assigned task list: {tasks}")
        return tasks

    def iterate(self) -> None:
        logger.debug(f"{self.owner} - iterate, status: {self.status}")
        super(WorkerJournal, self).iterate()

        if self.status in [
            ACTOR_STATUS.ready,
            ACTOR_STATUS.done,
            ACTOR_STATUS.failed,
        ]:
            tasks = self.list_assigned_tasks()
            if self.status == ACTOR_STATUS.ready:
                if tasks:
                    self.run_task(tasks[0])
            else:
                assigned = [t for t in tasks if t["_key"] == self.data]
                logger.debug(
                    f"{self.owner}: status {self.status}, checking if can switch to READY state, "
                    + f"task_started={self.started}, task_assigned={assigned}"
                )
                if not assigned or assigned[0][RECORD_FIELDS.time] > self.started:
                    self.update_reg(
                        status=ACTOR_STATUS.ready, data=None, traceback_msg=None
                    )

    def run_task(self, task: Dict[str, Any]) -> None:
        self.update_reg(
            status=ACTOR_STATUS.busy,
            data=task["_key"],
            started=time(),
            traceback_msg=None,
        )
        try:
            logger.info(f"{self.owner}: start task {task}")
            warning = self.handle_task_execute(task)
            if warning:
                logger.warning(
                    f"{self.owner}: run_task_result=failed, task {task}, traceback: {warning}"
                )
                self.update_reg(status=ACTOR_STATUS.failed, traceback_msg=str(warning))
            else:
                logger.info(f"{self.owner}: run_task_result=done, task {task}")
                self.update_reg(status=ACTOR_STATUS.done, traceback_msg=None)
        except StopIteration:
            raise
        except Exception as e:
            process_general_exception(
                f"{self.owner}: run_task_result=failed, task {task}, traceback_msg", e
            )
            self.update_reg(status=ACTOR_STATUS.failed, traceback_msg=str(e))
