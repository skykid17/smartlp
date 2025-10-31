#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from splunksdc.collector import SimpleCollectorV1
from .bucket_metadata_data_collector import BucketMetadataCollector


def modular_input_run(app, config):
    stanza = app.inputs()[0]
    data_input = BucketMetadataCollector(stanza)
    return data_input.run(app, config)


def main():
    """
    Main Function
    """
    arguments = {
        "google_credentials_name": {
            "title": "The name of Google service account",
            "description": "GCP service account",
        },
        "google_project": {
            "title": "The Google project ID",
            "description": "GCP project ID",
        },
        "bucket_name": {"title": "Bucket name", "description": "GCP bucket_name"},
        "chunk_size": {
            "title": "Chunk Size",
            "description": "Size of a chunk in bytes while downloading blob content",
        },
        "number_of_threads": {
            "title": "Number of threads",
            "description": "The number of threads that will work concurrently to fetch files from bucket and ingest it into Splunk",
        },
    }
    SimpleCollectorV1.main(
        modular_input_run,
        title="Google Buckets Metadata",
        use_single_instance=False,
        arguments=arguments,
    )
