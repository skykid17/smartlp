"""
WSGI entry point for production server (Gunicorn).

Usage:
    gunicorn --worker-class gthread --threads 4 -w 1 --bind 0.0.0.0:8800 wsgi:app
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.app_factory import ApplicationFactory

app = ApplicationFactory.create_app()
