"""
Logging utilities for SmartSOC application.
"""

import logging
from datetime import datetime, timezone
from typing import Optional


class SmartSOCLogger:
    """Custom logger for SmartSOC with SocketIO integration."""
    
    def __init__(self, name: str = "smartsoc"):
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
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_message(self, channel: str, message: str, level: str = "INFO") -> None:
        ts = datetime.now(timezone.utc).isoformat()

        # 1. Backend logging (for terminal / files / journald)
        self.logger.log(getattr(logging, level.upper(), logging.INFO), message)

        # 2. UI event stream (structured, no formatting)
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
app_logger = SmartSOCLogger()