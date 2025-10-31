"""
SocketIO management for SmartSOC application.
"""

from typing import Optional
from flask_socketio import SocketIO


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
            self._socketio = SocketIO(cors_allowed_origins="*", **kwargs)
        
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
            print("Client connected")
        
        @self._socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected")


# Global SocketIO manager instance
socketio_manager = SocketIOManager()

# Backward compatibility
socketio = socketio_manager.initialize()