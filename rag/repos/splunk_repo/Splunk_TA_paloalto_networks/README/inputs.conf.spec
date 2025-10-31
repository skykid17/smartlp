[palo_iot_security://<name>]
index = Index where data is going to be ingested.  Default: default
interval = Time interval of input in seconds.
iot_account = IoT account to use for this input.
start_time = Specify a date and time in UTC format (YYYY-MM-DD HH:MM:SS) from which to start collecting data. For example, 2024-03-10 09:35:00

[palo_data_security://<name>]
data_security_account = Data Security account to use for this input.
index = Index where data is going to be ingested.  Default: default
interval = Time interval of input in seconds.

[palo_cortex_xdr://<name>]
index = Index where data is going to be ingested.  Default: default
interval = Time interval of input in seconds.
start_time = Specify a date and time in UTC format (YYYY-MM-DD HH:MM:SS) from which to start collecting data. For example, 2024-03-10 09:35:00
xdr_account = Cortex XDR to use for this input.
xdr_get_details = Enrich incidents with details
