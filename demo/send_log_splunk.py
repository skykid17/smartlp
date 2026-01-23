import splunklib.client as splunk_client
import os

service = splunk_client.connect(
    host="localhost", 
    port=8089, 
    username="admin", 
    password=os.getenv("SPLUNK_PASSWORD"),
    verify=False
)

my_index = service.indexes["unparsed"]

# Send a log message
my_index.submit("Hello Splunk! This is a test log from Python.", sourcetype="catchall")

print("Log sent successfully.")