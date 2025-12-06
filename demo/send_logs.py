
#!/usr/bin/env python3
import time
import requests
from datetime import datetime

ES_URL = "http://192.168.31.62:9200"
DATASTREAM = "logs-unparsed-default"
SLEEP_SECONDS = 5    # send every 5 seconds

def send_log(log_line):
    doc = {
        "@timestamp": datetime.utcnow().isoformat(),
        "message": log_line
    }
    r = requests.post(f"{ES_URL}/{DATASTREAM}/_doc", json=doc)
    print(r.status_code, r.text)

def tail_file(filename):
    with open(filename, "r") as f:
        f.seek(0, 2)  # go to end of file
        while True:
            line = f.readline()
            if not line:
                time.sleep(SLEEP_SECONDS)
                continue
            send_log(line.strip())
            print(f"Sent log: {line.strip()}")

if __name__ == "__main__":
    tail_file("demo/logfile.log")  # change this to your log file
