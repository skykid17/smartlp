"""Notification helper.

Notifications are explicit, user-facing events and are separate from logging.
"""

from __future__ import annotations

from typing import Optional


def notify(message: str, level: str = "info") -> None:
    """Emit a user-facing notification via Socket.IO if available."""

    try:
        from core.socketio_manager import socketio_manager

        socketio = socketio_manager.socketio
        if not socketio:
            return

        socketio.emit(
            "notification",
            {
                "message": message,
                "level": level,
            },
        )
    except Exception:
        # Notifications should never break request handling.
        return
