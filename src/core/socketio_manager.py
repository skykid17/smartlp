"""SocketIO management for SmartLP application."""

import logging
from typing import Optional
from flask_socketio import SocketIO


logger = logging.getLogger(__name__)


class SocketIOManager:
    """Manages SocketIO instance and connections."""
    
    def __init__(self):
        """Initialize SocketIO manager."""
        self._socketio: Optional[SocketIO] = None
    
    def initialize(self, app=None, **kwargs) -> SocketIO:
        """Initialize SocketIO instance.
        
        Args:
            app: Flask application instance
            **kwargs: Additional SocketIO configuration
            
        Returns:
            SocketIO instance
        """
        if self._socketio is None:
            self._socketio = SocketIO(async_mode='threading', cors_allowed_origins="*", **kwargs)
        
        if app and self._socketio:
            self._socketio.init_app(app)
        
        return self._socketio
    
    @property
    def socketio(self) -> Optional[SocketIO]:
        """Get SocketIO instance."""
        return self._socketio
    
    def emit(self, event: str, data: dict, **kwargs) -> None:
        """Emit event to clients.
        
        Args:
            event: Event name
            data: Event data
            **kwargs: Additional emit options
        """
        if self._socketio:
            self._socketio.emit(event, data, **kwargs)
    
    def register_handlers(self) -> None:
        """Register SocketIO event handlers."""
        if not self._socketio:
            return
        
        @self._socketio.on('connect')
        def handle_connect():
            logger.info("Client connected")
        
        @self._socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Client disconnected")


# Global SocketIO manager instance
socketio_manager = SocketIOManager()

# Backward compatibility
socketio = socketio_manager.initialize()