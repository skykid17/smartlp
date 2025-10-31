# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.

#Core Python Imports
import sys
import re

#Splunk Library Imports
from splunk.models.field import Field, IntField, BoolField

#Import from SA-Hydra-inframon
from splunk.clilib.bundle_paths import make_splunkhome_path
sys.path.append(make_splunkhome_path(['etc', 'apps', 'SA-Hydra-inframon', 'bin']))
from hydra_inframon.models import SOLNAppObjModel, CSVField, PythonObjectField, ISODateTimeField, WildcardField

########################################################################
# COLLECTION MODEL 
########################################################################
class TAVMwareCollectionStanza(SOLNAppObjModel):
	'''
	Provides object mapping for the TA-vmware-inframon collection stanzas
	The conf file is used to determine what jobs are to be done to what hosts.
	'''

	resource = 'configs/conf-inframon_ta_vmware_collection'
	
	use_model_as_spec = True
	
	#The target resource on which to apply the job, i.e. the vCenter uri or unmanaged host uri
	target = CSVField()
	#The username to use on all targets for auth purposes
	username = Field()
	#this is the realm associated with the credential, though unused in vmware, it must be present for hydra
	realm = Field()
	# this is field for saving pool name
	pool_name = Field()
	#for storing the last updated time of vcenter stanza
	last_connectivity_checked = ISODateTimeField()
	#We use wildcard fields for priority since they are rare we do not want them to show up in metadata unnecessarily
	wildcard_fields = {
			"priority": WildcardField(re.compile(".+_priority$"), IntField()),
			"confirmation_expiration": WildcardField(re.compile(".+_confirmation_expiration$"), IntField())
		}
	
	
	#These are the destination indexes for the different data types
	perf_index = Field()
	inv_index = Field()
	taskevent_index = Field()
	#The following are internal fields used by the app to determine state for GUI configuration
	credential_validation = BoolField()
	target_type = Field()
	#The following are filters for performance data
	managed_host_includelist = Field()
	managed_host_excludelist = Field()
	host_instance_allowlist = CSVField()
	host_instance_denylist = CSVField()
	vm_instance_allowlist = CSVField()
	vm_instance_denylist = CSVField()
	cluster_instance_allowlist = CSVField()
	cluster_instance_denylist = CSVField()
	perf_entity_denylist = CSVField()
	# perf format type, it value should be 'csv' or 'normal'
	perf_format_type = Field()
	# maxObjectUpdates count value for waitForUpdates API call, which decide max objects value in the SOAP response
	inv_maxObjUpdates = IntField()
	# The following are fields for enable datagen and set poweroff vms count in auto generated vms
	# Set autoeventgen = true, if random moids and names are generated for hosts and vms to reach out to vc limit (1000 hosts, 10000 vms).
	# This fields are used only for internal purpose only.
	autoeventgen = BoolField()
	autoeventgen_poweroff_vmcount = IntField()
	deployment_type = Field()


########################################################################
# CACHE MODEL 
########################################################################

class TAVMwareCacheStanza(SOLNAppObjModel):
	'''
	Provides object mapping for the TA-vmware-inframon cache stanzas
	The conf file should NEVER be managed manually, it is a datastore for the shared objects
	'''
	
	resource = 'configs/conf-inframon_ta_vmware_cache'
	
	use_model_as_spec = True
	
	#This is the serialized python object representing inv_data
	inv_data = PythonObjectField()
	inv_time = ISODateTimeField()
	#This is a pointer to the worker that is currently editing the cache, 
	#workers will use this field to 'lock' this session to avoid collisions
	worker = Field()
	last_lock_time = ISODateTimeField()

########################################################################
# VC FORWARDER MODEL 
########################################################################

class TAVMwareVCenterForwarderStanza(SOLNAppObjModel):
	'''
	Provides object mapping for the vcenter forwarder stanzas
	The conf file is for storing information on accessing splunk forwarders.
	Note that by convention the name of these stanzas must match the vc stanza in inframon_ta_vmware_collection.conf
	Field Meanings:
		host - The routable address of the virtual center splunk forwarder management, e.g. https://vcenter.splunk.com:8089
		user - The user to use when administering the forwarder
		credential_validation - boolean indicating the credentials have been validated 
		addon_validation - boolean indicating the addon (TA-vcenter) has been validated as installed
	'''
	
	resource = 'configs/conf-vcenter_forwarder'
	
	use_model_as_spec = True
	
	host = Field()
	user = Field()
	#The field stores the state of VC log collection 
	collect_vc_logs = BoolField()
	credential_validation = BoolField()
	addon_validation = BoolField()

########################################################################
# SYSLOG FORWARDER MODEL 
########################################################################

class TAVMwareSyslogForwarderStanza(SOLNAppObjModel):
	'''
	Provides object mapping for the syslog forwarder stanzas
	The conf file is for storing configuration information related to syslog forwarding.
	Note that by convention the name of stanzas must match the vc stanza in inframon_ta_vmware_collection.conf
	Field Meanings:
		status - boolean on/off switch for data collection
		validation_status - boolean indicating if validation has passed
		syslog_uri - csv list of target ssylog forwarders
	'''
	
	resource = 'configs/conf-ta_vmware_syslog_forwarder'
	
	use_model_as_spec = True
	status = BoolField()
	validation_status = BoolField()
	uri = CSVField()
	config_status_msg= Field()


########################################################################
# DATA COLLECTION MODEL 
########################################################################

class TAVMwareCollectionScheduler(SOLNAppObjModel):
	"""
	Provides object mapping for the TA VMware Collection Scheduler present in inputs.conf
	Note that by convention the name of these stanzas must match the vc stanza in inframon_ta_vmware_collection.conf
	Field Meanings:
		disabled : boolean to store the state of Data collection
	"""
	resource ='configs/conf-inputs'
	use_model_as_spec = True
	
	disabled = BoolField()


########################################################################
# SSL CERTIFICATE MODEL
########################################################################

class SSLCertificate(SOLNAppObjModel):
	"""
	Provides object mapping for the SSL Certificate stanzas
	Field Meanings:
		disabled : boolean to store the state of ssl certificate validation
	"""
	resource = 'configs/conf-inframon_ta_vmware_config_ssl'
	use_model_as_spec = True
	validate_ssl_certificate = BoolField()
	
########################################################################
# POOL MODEL 
########################################################################

class PoolStanza(SOLNAppObjModel):

	"""
	Provides object mapping for the TA-vmware-inframon pool stanzas
	The conf file is used to save the configuration details of all the pools.
	"""

	resource = 'configs/conf-inframon_ta_vmware_pool'
	use_model_as_spec = True
	node_modification_time = ISODateTimeField()
	collection_modification_time = ISODateTimeField()
	description = Field()
	template_name = Field()
	# Vmware tasks include hostvmperf, clusterperf, inv, task, event
	task = CSVField()
	# The tasks considered atomic and thus config tokens of this task cannot generate a job while a previously generated job from the same config token is in progress
	atomic_tasks = CSVField()
	# The following are the collection intervals for particular tasks
	hostvmperf_interval = IntField()
	clusterperf_interval = IntField()
	vcperf_interval = IntField()
	datastoreperf_interval = IntField()
	task_interval = IntField()
	event_interval = IntField()
	hostinv_interval = IntField()
	vminv_interval = IntField()
	clusterinv_interval = IntField()
	datastoreinv_interval = IntField()
	hierarchyinv_interval = IntField()
	# The following are the expiration periods for particular tasks
	hostvmperf_expiration = IntField()
	clusterperf_expiration = IntField()
	vcperf_expiration = IntField()
	datastoreperf_expiration = IntField()
	task_expiration = IntField()
	event_expiration = IntField()
	hostinv_expiration = IntField()
	vminv_expiration = IntField()
	clusterinv_expiration = IntField()
	datastoreinv_expiration = IntField()
	hierarchyinv_expiration = IntField()

########################################################################
# TEMPLATE MODEL 
########################################################################

class TemplateStanza(SOLNAppObjModel):

	"""
	Provides object mapping for the TA-vmware-inframon template stanzas
	The conf file is used to save the additional fields for pool.
	"""

	resource = 'configs/conf-inframon_ta_vmware_template'
	use_model_as_spec = True
	vm_inv_fields = CSVField()
	host_inv_fields = CSVField()
	datastore_inv_fields = CSVField()
	cluster_inv_fields = CSVField()
	vm_ui_fields = CSVField()
	host_ui_fields = CSVField()
	datastore_ui_fields = CSVField()
	cluster_ui_fields = CSVField()
	host_metric_allowlist = CSVField()
	host_metric_denylist = CSVField()
	vm_metric_allowlist = CSVField()
	vm_metric_denylist = CSVField()
	cluster_metric_allowlist = CSVField()
	cluster_metric_denylist = CSVField()
	vc_metric_allowlist = CSVField()
	vc_metric_denylist = CSVField()


