#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
description_log = "splunk_gcp_resource_metadata"
compute_data_collection_conf = "google_cloud_resource_metadata_inputs.conf"
compute_resource_settings_conf = "google_cloud_resource_metadata_inputs"
apis = "google_apis"
source = "source"
sourcetype = "sourcetype"
index = "index"
interval = "polling_interval"
api = "google_api"
zones = "google_zones"
zone = "google_zone"
log_file = "log_file"
google_resource_metadata = "google_resource_metadata"
google_resource_metadata_cloud_storage = "google_resource_metadata_cloud_storage"
storage_data_collection_conf = (
    "google_cloud_resource_metadata_inputs_cloud_storage.conf"
)
storage_resource_settings_conf = "google_cloud_resource_metadata_inputs_cloud_storage"
google_resource_metadata_vpc_access = "google_resource_metadata_vpc_access"
vpcaccess_data_collection_conf = "google_cloud_resource_metadata_inputs_vpc_access.conf"
vpcaccess_resource_settings_conf = "google_cloud_resource_metadata_inputs_vpc_access"
google_resource_metadata_kubernetes = "google_resource_metadata_kubernetes"
kubernetes_data_collection_conf = (
    "google_cloud_resource_metadata_inputs_kubernetes.conf"
)
kubernetes_resource_settings_conf = "google_cloud_resource_metadata_inputs_kubernetes"
resource_endpoints = {
    "compute": {
        "accelerator_types": "acceleratorTypes",
        "autoscalers": "autoscalers",
        "disk_types": "diskTypes",
        "disks": "disks",
        "firewalls": "firewalls",
        "instance_group_managers": "instanceGroupManagers",
        "instance_groups": "instanceGroups",
        "instances": "instances",
        "machine_types": "machineTypes",
        "network_endpoint_groups": "networkEndpointGroups",
        "node_groups": "nodeGroups",
        "node_types": "nodeTypes",
        "operation_resources": "zoneOperations",
        "reservations": "reservations",
        "target_instance": "targetInstances",
    },
    "storage": {
        "buckets": "buckets",
        "bucket_access_controls": "bucketAccessControls",
        "default_object_access_controls": "defaultObjectAccessControls",
        "notifications": "notifications",
        "object_access_controls": "objectAccessControls",
    },
    "vpcaccess": {
        "locations": "locations",
        "connectors": "connectors",
        "operations": "operations",
    },
    "container": {
        "subnetworks": "subnetworks",
        "clusters": "clusters",
        "node_pools": "nodepools",
        "operations": "operations",
    },
}
resource_metadata_supported_scopes = {
    "compute": [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/cloud-platform.read-only",
        "https://www.googleapis.com/auth/compute",
        "https://www.googleapis.com/auth/compute.readonly",
    ],
    "storage": [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/cloud-platform.read-only",
    ],
    "vpcaccess": ["https://www.googleapis.com/auth/cloud-platform"],
    "container": [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/cloud-platform.read-only",
    ],
}
