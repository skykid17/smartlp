"""Logging utilities for SmartLP application.

This module intentionally uses Python stdlib logging as the single source of truth.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional


class SocketIOLogHandler(logging.Handler):
    """Logging handler that forwards log records to Socket.IO.

    Emits a single event: "log" with a structured payload:
    {"ts": ..., "level": ..., "logger": ..., "message": ...}
    """

    def __init__(self, socketio: Any):
        super().__init__()
        self._socketio = socketio
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            }
            # Emit to all clients on the default namespace
            # When using eventlet, socketio.emit() automatically broadcasts from background threads
            self._socketio.emit("log", payload, namespace='/')
        except Exception as e:
            # Log errors to stderr for debugging, but don't break the application
            print(f"SocketIOLogHandler emit error: {e}", file=sys.stderr)


def configure_logging(socketio: Optional[Any] = None) -> None:
    """Configure stdlib logging once for the entire application."""

    logging.basicConfig(
        level=os.getenv("APP_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if socketio:
        root_logger = logging.getLogger()
        if not any(isinstance(h, SocketIOLogHandler) for h in root_logger.handlers):
            handler = SocketIOLogHandler(socketio)
            handler.setLevel(logging.INFO)
            root_logger.addHandler(handler)