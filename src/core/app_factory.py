"""
Application factory for SmartSOC Flask application.
"""

import logging
import os
import signal
import sys
import threading
from typing import Optional

from flask import Flask, request, redirect, jsonify

from config.environment import env_manager
from core.socketio_manager import socketio_manager
from utils.logging import configure_logging


logger = logging.getLogger(__name__)


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
        
        # Initialize SocketIO early so logging can forward events to the UI.
        socketio_manager.initialize(app)
        socketio_manager.register_handlers()

        # Configure logging once, globally (console + optional SocketIO handler)
        configure_logging(socketio_manager.socketio)

        # Configure app
        ApplicationFactory._configure_app(app)
        
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
        if env_manager.app.secret_key:
            app.config['SECRET_KEY'] = env_manager.app.secret_key
        
        # Additional Flask configuration
        app.config['JSON_SORT_KEYS'] = False
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        
        # --- First-run initialization gate ---
        # If global settings are not marked initialized, force all routes to /init
        # and allow only init APIs + static assets.
        from services.settings import settings_service

        ALLOWED_PREFIXES = (
            "/init",
            "/api/init",
            "/api/settings/global",
            "/socket.io",
        )
        STATIC_PREFIXES = (
            "/css/",
            "/js/",
            "/logos/",
            "/webfonts/",
            "/favicon",
            "/static/",
        )

        @app.before_request
        def initialization_guard():
            try:
                global_settings = settings_service.get_global_settings() or {}
                initialized = bool(global_settings.get("initialized"))
            except Exception:
                initialized = False

            if initialized:
                return None

            path = request.path or "/"
            if path.startswith(ALLOWED_PREFIXES) or path.startswith(STATIC_PREFIXES):
                return None

            # Avoid redirecting API calls (fetch/XHR) into HTML.
            if path.startswith("/api/"):
                return jsonify({"error": "Initialization required"}), 403

            return redirect("/init")

        logger.info("Flask application configured")


    @staticmethod
    def _initialize_extensions(app: Flask) -> None:
        """Initialize Flask extensions.

        SocketIO is initialized in create_app() before configure_logging().
        This method remains for future extensions.
        """
        logger.info("Flask extensions initialized")
    
    @staticmethod
    def _register_routes(app: Flask) -> None:
        """Register application routes.
        
        Args:
            app: Flask application instance
        """
        try:
            from api.init_routes import register_init_routes
            from api.settings_routes import register_settings_routes
            from api.main_routes import register_main_routes
            from services.settings import settings_service

            # Register all route modules
            register_init_routes(app)
            logger.info("Init routes registered")
            register_settings_routes(app)
            logger.info("Settings routes registered")

            # Always register the dashboard route(s).
            # The heavy imports happen inside the view function, and the
            # initialization_guard blocks access before setup is complete.
            register_main_routes(app)
            logger.info("Main routes registered")

            # Only register SmartLP routes once initialization is complete.
            # This prevents import-time side effects (SIEM service instantiation)
            # from crashing the app when the settings collection is empty.
            try:
                global_settings = settings_service.get_global_settings() or {}
                initialized = bool(global_settings.get("initialized"))
            except Exception:
                initialized = False

            if initialized:
                from api.smartlp_routes import register_smartlp_routes
                register_smartlp_routes(app)
                logger.info("SmartLP routes registered")
            else:
                logger.info("Initialization not complete; skipping SmartLP routes registration")
            
            logger.info("All application routes registered")
        except Exception as e:
            logger.exception("Error registering routes")
            raise
    
    @staticmethod
    def _setup_background_tasks(app: Flask) -> None:
        """Setup background tasks.
        
        Args:
            app: Flask application instance
        """
        # Import here to avoid circular imports
        from services.smartlp import smartlp_service
        from services.settings import settings_service
        
        @app.before_request
        def start_background_ingester():
            """Start background log ingestion on first request."""
            try:
                global_settings = settings_service.get_global_settings() or {}
                if not bool(global_settings.get("initialized")):
                    return None
            except Exception:
                return None

            # Remove this function after first execution
            if start_background_ingester in app.before_request_funcs[None]:
                app.before_request_funcs[None].remove(start_background_ingester)
                
                # Start background ingestion in daemon thread
                thread = threading.Thread(
                    target=smartlp_service.start_log_ingestion, 
                    daemon=True
                )
                thread.start()
    
    @staticmethod
    def _setup_signal_handlers() -> None:
        """Setup signal handlers for graceful shutdown."""
        def handle_exit(sig, frame):
            """Handle application exit signal."""
            try:
                # Import here to avoid circular imports
                from services.smartlp import smartlp_service
                
                logger.info("Graceful shutdown initiated")
                smartlp_service.stop_log_ingestion()
                
                # Close database connections
                from database.connection import db_connection
                db_connection.close()
                
                logger.info("Shutdown complete")
            except Exception as e:
                logger.exception("Error during shutdown")
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
            host: Host to bind to (uses settings default if None)
            port: Port to bind to (uses settings default if None)
            debug: Debug mode (uses settings default if None)
        """
        # Use settings defaults if not specified
        run_host = host or env_manager.app.host
        run_port = port or env_manager.app.port
        run_debug = debug if debug is not None else env_manager.app.debug
        
        logger.info("Starting SmartLP server on %s:%s", run_host, run_port)
        
        # Run with SocketIO
        if socketio_manager.socketio is not None:
            try:
                socketio_manager.socketio.run(
                    app, 
                    host=run_host, 
                    port=run_port, 
                    debug=run_debug,
                    # use_reloader=False  # Disable reloader to avoid double threads
                )
            except Exception as e:
                logger.exception("SocketIO run error")
                raise
        else:
            logger.error("SocketIO not initialized")
            raise RuntimeError("SocketIO not initialized")