import sys
import os

# isort: skip_file
lib_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(1, os.path.join(lib_path, "httplib2"))
import httplib2  # noqa
