from __future__ import annotations

import sys
from pathlib import Path

# Allow running this script directly via `python demo/reset_for_demo.py`
# by ensuring the project's `src/` folder is on sys.path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.smartlp import smartlp_service
from database.connection import db_connection

elastic_settings = smartlp_service._get_elastic_settings()
elastic_host = elastic_settings.get("host")
elastic_password = elastic_settings.get("password")
elastic_user = elastic_settings.get("user")
pipeline_id = elastic_settings.get("pipeline_id") or "smartlp"

pipeline_body = r'''
input {
    tcp {
        port => 1701
        codec => multiline {
        pattern => "^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\s(.*?)\s[A-Z]+|^<Event xmlns|^\S{3}\s+\d+\s\d{2}:\d{2}:\d{2}|^<\d+>\S{3}\s+\d+\s\d{2}:\d{2}:\d{2}|^<\d+>\d\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d+\s\w+\s\w+:\d+"
        negate => true
        what => "previous"
        }
    }
}
filter {
}'''

pipeline_body += f'''
output {{
    stdout {{ codec => rubydebug }}
    elasticsearch {{
        hosts => ["{elastic_host}"]
        ssl_enabled => true
        ssl_certificate_authorities => "/etc/logstash/certs/cyberlab-rca-ica-chain.cer"
        user => "{elastic_user}"
        password => "{elastic_password}"
        data_stream => true
        data_stream_type => "logs"
        data_stream_dataset => "unparsed"
        data_stream_namespace => "default"
        }}
    }}'''

smartlp_service.deploy_config_elastic(pipeline_body)

# Clear the database collection "logs"
db_connection.delete_many("logs", {})
print("Database collection 'logs' has been cleared.")