"""
WSGI entry point for production server (Gunicorn).

Usage:
    gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
        -w 1 --bind 0.0.0.0:8800 wsgi:app
"""

# Monkey-patch stdlib for gevent BEFORE any other imports.
from gevent import monkey
monkey.patch_all()

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.app_factory import ApplicationFactory

app = ApplicationFactory.create_app()
