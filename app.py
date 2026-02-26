#!/usr/bin/env python3
"""
SmartSOC - Smart Security Operations Center Application
Main application entry point using the refactored architecture.
"""

import sys
import os
import logging

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.app_factory import ApplicationFactory


logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    try:
        # Create the Flask application
        app = ApplicationFactory.create_app()
        
        # Run the application
        ApplicationFactory.run_app(app)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Failed to start application")
        sys.exit(1)


if __name__ == "__main__":
    main()