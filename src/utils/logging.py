"""
Logging utilities for SmartSOC application.
"""

import logging
from datetime import datetime
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
        """Log message with SocketIO emission.
        
        Args:
            channel: SocketIO channel ('log' or 'notification')
            message: Message to log
            level: Log level
        """
        timestamp = datetime.now().strftime("%d %b %H:%M:%S")
        
        if channel == 'log':
            formatted_message = f'{timestamp}: {message}'
            self.logger.info(message)
            try:
                from core.socketio_manager import socketio_manager
                if socketio_manager.socketio is not None:
                    socketio_manager.socketio.emit(channel, {'message': formatted_message})
            except (ImportError, AttributeError):
                pass  # SocketIO not available yet
        elif channel == 'notification':
            self.logger.info(f"NOTIFICATION: {message}")
            try:
                from core.socketio_manager import socketio_manager
                if socketio_manager.socketio is not None:
                    socketio_manager.socketio.emit(channel, {'message': message})
            except (ImportError, AttributeError):
                pass  # SocketIO not available yet
        else:
            self.logger.log(getattr(logging, level.upper(), logging.INFO), message)


# Global logger instance
app_logger = SmartSOCLogger()

def log_message(channel: str, message: str) -> None:
    """Backward compatibility function for logging.
    
    Args:
        channel: SocketIO channel ('log' or 'notification')
        message: Message to log
    """
    app_logger.log_message(channel, message)