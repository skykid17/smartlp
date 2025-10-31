"""
Application factory for SmartSOC Flask application.
"""

import os
import signal
import sys
import threading
from typing import Optional
from flask import Flask

from config.settings import config
from core.socketio_manager import socketio_manager
from utils.logging import app_logger


class ApplicationFactory:
    """Factory class for creating and configuring Flask application."""
    
    @staticmethod
    def create_app(config_name: str = 'default') -> Flask:
        """Create and configure Flask application.
        
        Args:
            config_name: Configuration name (unused for now, kept for future)
            
        Returns:
            Configured Flask application
        """
        # Get project root directory (go up from src/core to project root)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        static_path = os.path.join(project_root, 'static')
        template_path = os.path.join(project_root, 'templates')
        
        # Create Flask app with correct paths
        app = Flask(__name__, 
                   static_url_path='', 
                   static_folder=static_path, 
                   template_folder=template_path)
        
        # Configure app
        ApplicationFactory._configure_app(app)
        
        # Initialize extensions
        ApplicationFactory._initialize_extensions(app)
        
        # Register blueprints/routes
        ApplicationFactory._register_routes(app)
        
        # Setup background tasks
        ApplicationFactory._setup_background_tasks(app)
        
        # Setup signal handlers
        ApplicationFactory._setup_signal_handlers()
        
        return app
    
    @staticmethod
    def _configure_app(app: Flask) -> None:
        """Configure Flask application settings.
        
        Args:
            app: Flask application instance
        """
        # Set secret key if available
        if config.app.secret_key:
            app.config['SECRET_KEY'] = config.app.secret_key
        
        # Additional Flask configuration
        app.config['JSON_SORT_KEYS'] = False
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        
        print("Flask application configured")  # Use print instead of logger initially
    
    @staticmethod
    def _initialize_extensions(app: Flask) -> None:
        """Initialize Flask extensions.
        
        Args:
            app: Flask application instance
        """
        # Initialize SocketIO
        socketio_instance = socketio_manager.initialize(app)
        print(f"SocketIO initialized: {socketio_instance is not None}")
        socketio_manager.register_handlers()
        
        print("Flask extensions initialized")  # Use print initially, then we can use logger
    
    @staticmethod
    def _register_routes(app: Flask) -> None:
        """Register application routes.
        
        Args:
            app: Flask application instance
        """
        try:
            from api.main_routes import register_main_routes
            from api.smartlp_routes import register_smartlp_routes
            from api.smartuc_routes import register_smartuc_routes
            from api.settings_routes import register_settings_routes
            from api.deployment_routes import register_deployment_routes
            
            # Register all route modules
            register_main_routes(app)
            print("Main routes registered")
            register_smartlp_routes(app)
            print("SmartLP routes registered")
            register_smartuc_routes(app)
            print("SmartUC routes registered")
            register_settings_routes(app)
            print("Settings routes registered")
            register_deployment_routes(app)
            print("Deployment routes registered")
            
            print("All application routes registered")
        except Exception as e:
            print(f"Error registering routes: {e}")
            raise
    
    @staticmethod
    def _setup_background_tasks(app: Flask) -> None:
        """Setup background tasks.
        
        Args:
            app: Flask application instance
        """
        # Import here to avoid circular imports
        from services.smartlp import smartlp_service
        
        @app.before_request
        def start_background_ingester():
            """Start background log ingestion on first request."""
            # Remove this function after first execution
            if start_background_ingester in app.before_request_funcs[None]:
                app.before_request_funcs[None].remove(start_background_ingester)
                
                # Start background ingestion in daemon thread
                thread = threading.Thread(
                    target=smartlp_service.start_log_ingestion, 
                    daemon=True
                )
                thread.start()
                
                app_logger.log_message('log', 'Background log ingestion started')
    
    @staticmethod
    def _setup_signal_handlers() -> None:
        """Setup signal handlers for graceful shutdown."""
        def handle_exit(sig, frame):
            """Handle application exit signal."""
            try:
                # Import here to avoid circular imports
                from services.smartlp import smartlp_service
                
                app_logger.log_message('log', 'Graceful shutdown initiated')
                smartlp_service.stop_log_ingestion()
                
                # Close database connections
                from database.connection import db_connection
                db_connection.close()
                
                app_logger.log_message('log', 'Shutdown complete')
            except Exception as e:
                print(f"Error during shutdown: {e}")
            finally:
                sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)
    
    @staticmethod
    def run_app(app: Flask, host: Optional[str] = None, 
                port: Optional[int] = None, debug: Optional[bool] = None) -> None:
        """Run the Flask application with SocketIO.
        
        Args:
            app: Flask application instance
            host: Host to bind to (uses config default if None)
            port: Port to bind to (uses config default if None)
            debug: Debug mode (uses config default if None)
        """
        # Use config defaults if not specified
        run_host = host or config.app.host
        run_port = port or config.app.port
        run_debug = debug if debug is not None else config.app.debug
        
        print(f'Starting SmartSOC server on {run_host}:{run_port}')
        
        # Debug SocketIO state
        print(f"SocketIO instance: {socketio_manager.socketio}")
        print(f"SocketIO type: {type(socketio_manager.socketio)}")
        
        # Run with SocketIO
        if socketio_manager.socketio is not None:
            try:
                socketio_manager.socketio.run(
                    app, 
                    host=run_host, 
                    port=run_port, 
                    debug=run_debug
                )
            except Exception as e:
                print(f"SocketIO run error: {e}")
                print(f"SocketIO instance details: {dir(socketio_manager.socketio) if socketio_manager.socketio else 'None'}")
                raise
        else:
            print("Error: SocketIO not initialized")
            raise RuntimeError("SocketIO not initialized")