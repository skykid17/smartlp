"""
Logging utilities for SmartSOC application.
"""

import logging
from datetime import datetime, timezone
from typing import Optional


class SmartLPLogger:
    """Custom logger for SmartLP with SocketIO integration."""
    
    def __init__(self, name: str = "smartlp"):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        # Prevent messages from being propagated to the root logger
        # which can cause duplicate output if a root handler exists.
        self.logger.propagate = False
    
    def log_message(self, channel: str, message: str, level: str = "INFO") -> None:
        ts = datetime.now(timezone.utc).isoformat()

        # Backend logging (for terminal / files / journald)
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message)

        # UI event stream (structured, no formatting)
        if channel in ("log", "notification"):
            try:
                from core.socketio_manager import socketio_manager
                if socketio_manager.socketio:
                    socketio_manager.socketio.emit(channel, {
                        "timestamp": ts,
                        "message": message,
                        "level": level
                    })
            except (ImportError, AttributeError):
                pass
        
# Global logger instance
app_logger = SmartLPLogger()