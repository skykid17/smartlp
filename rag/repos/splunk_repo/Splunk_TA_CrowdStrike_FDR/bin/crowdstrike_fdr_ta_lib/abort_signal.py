#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import datetime
import signal

import solnlib
from typing import Any

from .logger_adapter import CSLoggerAdapter

logger = CSLoggerAdapter(
    solnlib.log.Logs().get_logger("splunk_ta_crowdstrike_fdr").getChild("abort_signal")
)

global_is_aborted = False


class AbortSignalException(Exception):
    def __init__(self) -> None:
        self.timestamp = datetime.datetime.now()

    def __str__(self) -> str:
        return f"Recieved abort signal at {self.timestamp} !!!"


def signal_abort_handler(*args: Any, **kwargs: Any) -> None:
    global global_is_aborted
    global_is_aborted = True
    logger.info("Abort signal recieved")


def abort_signal_handler_setup(callback_fm=signal_abort_handler) -> None:

    try:
        global global_is_aborted
        global_is_aborted = False

        signals_to_catch = [
            "SIGABRT",
            "SIGQUIT",
            "SIGINT",
            "SIGTERM",
            "SIGHUP",
            "SIGBREAK",
        ]

        for sig_name in signals_to_catch:
            try:
                sig_code = getattr(signal, sig_name, None)
                if sig_code is not None:
                    signal.signal(sig_code, callback_fm)
                    logger.debug(f"Abort signal handler is installed for {sig_name}")
                    signal.siginterrupt(sig_code, False)
            except AttributeError as e:
                logger.warning(f"Abort signal {sig_name} handler setup: {e}")

    except Exception as e:
        solnlib.log.log_exception(
            logger,
            e,
            "Abort signal",
            msg_before=f"Abort signal handler regstraion has failed: {e}",
        )
        raise
    else:
        logger.debug("Abort signal handler is registered")


def is_aborted() -> bool:
    return global_is_aborted


def check_and_abort() -> None:
    if global_is_aborted:
        logger.info("Abort signal exception raised")
        raise AbortSignalException()
