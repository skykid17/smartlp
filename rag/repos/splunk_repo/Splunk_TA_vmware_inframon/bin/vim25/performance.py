# -*-  indent-tabs-mode:nil;  -*- 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved. 

import datetime
import random

from vim25.mo import ManagedObjectReference
from vim25 import utils
from vim25.connection import Connection

import vim25.inventory as inventory
from vim25.metrics_list_matcher import MetricsListMatcher
from vim25.metrics_cache import MetricsCache

import math
import re
import json

cluster_dict = {}

class PerfCollector(Connection):
	"""
	Class responsible for retrieval and output of performance metrics.

	Instantiated with:
	  config - dict of collection parameters
	  logger - logger instance

	Caches: 
	  performance metrics (from queryAvailablePerfMetrics)
	  performance counters (from PerfCounterInfo)
	
	The caches are typically multi-level dictionaries, with the VCs at the root level.
	"""
	def __init__(self, config, logger):
		self.config = config
		self.dbg_info = "[Performance Handler: {task}] [PerfCollector] ".format(task=config['perf_collection_type'])
		self.logger = logger
		self.logger.debug(self.dbg_info + "Instantiating perf collection class for %s (%s)" % (config['perf_collection_type'], str(config['perf_target_hosts'])))
		self._ref_rate_cache = {}
		self._counters_cache = {} # format: {self.domain: {'pcs_by_key': {}, 'pcs_fqname_by_key': {}, 'pcs_idx_name_by_key': {}}}
		self._metrics_cache = {}  # format: {self.domain: MetricsCache(200, 50)}
		self._entity_allow_deny_list_cache = {}
		self.pool_name = config.get("pool_name", None)
		self._vc_saved_id = None


	def update_config(self, newconfig):
		"""
		Updates the config member variable.  Note that target-specific keys
		in the config are expected to be different, so they are is excluded from
		comparison.
		"""
		def config_same(c1, c2):
			include_keys = ['cluster_metric_allowlist', 'cluster_metric_denylist', 'cluster_instance_denylist', 'cluster_instance_allowlist', 'perf_index', 'perf_format_type', 'perf_entity_denylist']
			for k in include_keys:
				if c1[k] != c2[k]: return False
			return True
		# If config is different, blow away the caches
		if not config_same(self.config, newconfig):
			self.logger.debug(self.dbg_info + "Found different config, blowing away caches")
			self._counters_cache = {} 
			self._metrics_cache = {} 
		self.config = newconfig


	def _update_counters_cache(self):
		"""
		Checks the current vc ID agains the saved vc_id and if we have changed vcs (or we
		haven't talked to one before) create (or re-create) dictionaries of performance counters 
		keyed by ID.  Returns the vcenter UUID.
		"""
		def populate_counter_dicts():
			pcis = self.perfManager.getPerfCounter().PerfCounterInfo
			pcs_by_key = {}
			pcs_fqname_by_key = {}
			pcs_idx_name_by_key = {}
			for pc in pcis:
				pcs_by_key[pc.key] = pc
				pcs_fqname_by_key[pc.key] = self._get_fqname(pc)
				pcs_idx_name_by_key[pc.key] = self._get_idx_name(pc)
			return {'pcs_by_key': pcs_by_key, 'pcs_fqname_by_key': pcs_fqname_by_key, 'pcs_idx_name_by_key': pcs_idx_name_by_key}
			
		if self.domain != self._vc_saved_id:
			self._vc_saved_id = self.domain
			if self.domain not in self._counters_cache:
				self._counters_cache[self.domain] = populate_counter_dicts()
				self.logger.debug(self.dbg_info + "Populated counters cache for domain %s", self.domain)
			self.pcs_by_key = self._counters_cache[self.domain]['pcs_by_key']
			self.pcs_fqname_by_key = self._counters_cache[self.domain]['pcs_fqname_by_key']
			self.pcs_idx_name_by_key = self._counters_cache[self.domain]['pcs_idx_name_by_key']
		return self._vc_saved_id


	def _prepare_metrics_lists(self, entities, vc_id):
		"""
		Prepares and caches metric lists for this collector's entities.

		Metric lists are created to conform to the allowlist/denylist specifications
		in the config.  Caching is done to ensure that for a given inventory set, 
		the metrics are only retrieved once.

		Returns: metrics as a dict of lists keyed by entity type.
		"""
		inventory_hash = hash(frozenset([vc_id] + [hash(frozenset([entity.value for entity in entities]))]))
		metrics = {}
		entity_allow_deny_list = {'cluster_metric_allowlist': self.config.get("cluster_metric_allowlist", []),
					   'cluster_metric_denylist' : self.config.get("cluster_metric_denylist", [])}
		
		if self.domain not in self._metrics_cache:
			self._metrics_cache[self.domain] = MetricsCache(2000, 50)
		if self.domain not in self._entity_allow_deny_list_cache:
			self._entity_allow_deny_list_cache[self.domain] = {}
		cache = self._metrics_cache[self.domain]
	
		if inventory_hash in cache and (entity_allow_deny_list == self._entity_allow_deny_list_cache[self.domain]):
			metrics = cache[inventory_hash]
			self.logger.debug(self.dbg_info + "Got a list of metrics from cache")
		else:
			self.logger.debug(self.dbg_info + "Getting a NEW list of metrics")
			self._entity_allow_deny_list_cache[self.domain] = entity_allow_deny_list

			metrics = self.get_all_metrics(entities)
			cache[inventory_hash] = metrics
		return metrics

	def _is_entity_excluded(self, e):
		return any(re.search(x, e) is not None for x in self.config['perf_entity_denylist'])
		
	def _get_fqname(self, pc):
		return ".".join([pc.groupInfo.key, pc.rollupType, pc.nameInfo.key, pc.unitInfo.key])

	def _get_idx_name(self, pc):
		return ".".join([pc.groupInfo.key, pc.nameInfo.key])
		
	def _aggregate_only(self):
		return (not self.config['cluster_instance_denylist'] 
				and not self.config['cluster_instance_allowlist'])

	def _get_ref_rate_for_entity(self, entity):
		"""
		Gets the refresh rate for the metrics.  
		
		This value is assumed to be fixed for a given entity type on a given
		collection run.  For instance, if collecting ResourcePool data from
		managed hosts the 'current'/20-sec refresh rate is not available and we have
		to use the 300-second summary roll-up.  However, ResourcePools collected
		from unmanaged hosts only have the 20-second data and NO 300-second summary.
		We never deal with managed and unmanaged hosts in the same collection run,
		so we just cache the highest available refresh rate when we first see 
		an entity of a given type and use that value for the duration of collection.

		TODO: In case of having multiple vCenter Servers with different 
		refresh rates, we need to modify the structure of class-level variable 
		_ref_rate_cache to handle multiple refresh rates of different vCenter servers
		"""
		def get_ref_rate():
			pps = self.perfManager.queryPerfProviderSummary(entity)
			if pps.currentSupported:
				rr = pps.refreshRate
			elif pps.summarySupported:
				rr = min([x.samplingPeriod for x in self.perfManager.getHistoricalInterval().PerfInterval])
			else:
				raise Exception("Unable to determine perf collection rate")
			self._ref_rate_cache[entity._type] = rr
			return rr
				
		if entity._type in self._ref_rate_cache:
			return self._ref_rate_cache[entity._type]
		else:
			return get_ref_rate()

	def _query_perf(self, entities, pmids, start_time=None, end_time=None, max_samples=None):
		"""
		Construct PerfQuerySpec and invoke queryPerf vipython method on the performance manager object.
		
		entities (list of MORs)
		start/end_time are optional; they form a (start, end] half-closed interval
		Returns: list of PerfEntityMetricCSV
		
		Long lists of entities require several calls to queryPerf
		"""
		max_api_call = 0
		matching_metrics_limit = 64
		entities_len = len(entities)
		pmids_len = len(pmids)
		total_call = float(entities_len * pmids_len)
		if total_call < 64:
			NUM_CLUSTER_SINGLE_COLLECTION = 1
		else:
			max_api_call = total_call / matching_metrics_limit
			if not max_api_call == 0 :
				NUM_CLUSTER_SINGLE_COLLECTION = math.ceil(entities_len / max_api_call)
		if not entities or not pmids:
			self.logger.debug(self.dbg_info + "Skipping collection due to empty lists of entities and/or metrics")
			return []
		num_collections = math.ceil(len(entities) / float(NUM_CLUSTER_SINGLE_COLLECTION))
		chunk_size = int(math.ceil(len(entities) / num_collections))
		assert chunk_size >= 0 and chunk_size <= len(entities)
		res = []
		try:
			for i in range(int(num_collections)):
				# python is OK with slice indexes being longer than max list index
				chunk = entities[i * chunk_size : (i + 1) * chunk_size]
				qspecs = [Connection.vim25client.new('PerfQuerySpec', entity=x, metricId=pmids, format= self.config.get('perf_format_type', 'csv'), intervalId=self._get_ref_rate_for_entity(x), 
												startTime=start_time, endTime=end_time) for x in chunk]
				res.extend(self.perfManager.queryPerf(qspecs))
			self.logger.debug(self.dbg_info + "Collected data: collection_type={coll}, entity_type={type} first_entity={first_ent} "
							  "len_in={num_ent} len_out={len_res} start_time={s} "
							  "end_time={e}".format(coll=self.config['perf_collection_type'], type=entities[0]._type, first_ent=entities[0].value,
													num_ent=len(entities), len_res=len(res), s=start_time, e=end_time))
		except Exception as e:
			self.logger.error("Max allowed metrics size of 64 has been exceeded for ClusterComputeResource.")
			raise
		return res

	def _find_clusters(self): 
		hierarchy_collector = inventory.CreateHierarchyCollector(targetConfigObject='PerfClusterComputeResourceList', oneTime=True)[1]
		gen_collect_propex = hierarchy_collector.collectPropertiesEx(hierarchy_collector.fSpecList)
		ccrs_list = []
		for ccrs in gen_collect_propex:
			if ccrs is None:
				break
			else:
				for x in ccrs:
					ccrs_list.append(x.obj)
		inventory.DestroyHierarchyCollector(hierarchy_collector)
		del gen_collect_propex, hierarchy_collector
		return ccrs_list

	def _check_format_type(self, format_type):
		"""
			Check if performance performance type, raise exception is not correct.
			@param format_type: specified peformance type in str format
			
			@return: Exception, if it is not supported format, otherwise None
		"""
		if not format_type in ['csv', 'normal']:
			self.logger.error("[Performance Handler] Specify performance format is incorrect. Specify format type either csv or normal.")
			raise Exception("[Performance Handler] Specify performance format is incorrect. Specify format type either csv or normal.")
		
	def _process_timestamps(self, perfdata, format):
		"""
			Get list of timestamps value in %Y-%m-%dT%H:%M:%SZ format of perfdata
			
			@return list of timestamps in %Y-%m-%dT%H:%M:%SZ format
		"""
		if format == 'csv':
			return perfdata.sampleInfoCSV.split(',')[1::2]
		else:
			timestamps = []
			for sampleInfo in perfdata.sampleInfo:
				# same time format as csv type
				timestamps.append(sampleInfo.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'))
			return timestamps

	def get_all_metrics(self, entities, mode='regex'):
		"""
		Gets performance metrics for a list of entities provided a given refresh rate and 
		relevant allowlists and denylists.
		
		entities (list of MORs) - these have to be of the SAME TYPE (e.g. all ClusterComputeResources)
		
		Keyword args:
		mode: MetricsListMatcher mode parameter ["regex" | "verbatim"]

		Returns:
		list of PerfMetricId's

		Implementation notes:
		Empirically, at 20-second collection intervals, two entities of the same type share counterIds 
		this is NOT necessarily true for other collection intervals.   However, different entities
		of the same type will NOT necessarily share instance ids. Thus, available PerfMetricIds, in general, 
		differ from entity to entity.  When getting intance-level data, we then must either specify ALL 
		available instance Ids in the perfMetricIds OR leave the instance string as "*"; this is
		more efficient and is the current approach.
		"""
		def aggregate_instances_maybe(pmids, style): 
			inst_field = {"glob": "*", "aggregate": ""}
			if style not in inst_field:
				raise ValueError("Style must be in {0}".format(list(inst_field)))
			res = []
			aggregate_cids = set()
			for mid in pmids:
				if mid.counterId not in aggregate_cids:
					aggregate_cids.add(mid.counterId)
					mid.instance = inst_field[style]
					res.append(mid)
			return res
		
		m = []
		if not entities: return m
		self.logger.debug(self.dbg_info + "Querying and pruning available metrics")
		# If all the metrics are identical, we can build the list of metrics 
		# based on the first entity in the list only.  However, this assumption turns out to be wrong
		# in general, e.g. if we have empty clusters, they do not have all of the relevant metrics
		# (in particular, they are missing the clusterServices metrics)
		entity = entities[0]
		refresh_rate = self._get_ref_rate_for_entity(entity)
		all_metrics = []
		all_metrics_d = {}
		d_key = lambda m: str(m.counterId) + str(m.instance)
		for e in entities:
			for m in self.perfManager.queryAvailablePerfMetric(e, intervalId=refresh_rate):
				if d_key(m) not in all_metrics_d: all_metrics_d[d_key(m)] = m
		all_metrics = list(all_metrics_d.values())
		counter_matcher = MetricsListMatcher(self.config['cluster_metric_allowlist'],
											 self.config['cluster_metric_denylist'], mode)
		instance_matcher = MetricsListMatcher(self.config['cluster_instance_allowlist'],
											  self.config['cluster_instance_denylist'], mode)
		
		pmid_to_fqname = lambda pmid: self.pcs_fqname_by_key[pmid.counterId]
		# Filtering logic: first prune the list of metrics to conform to the allow/denylists
		# Then match against the instance allow/denylists as follows: 
		# - if a metric conforms to the instance allow/denylists, it is included in the collection;
		#   but we must uniquify by counterIds and set instance attributes to "*"
		# - if a metric DOES NOT conform to the instance allow/denylists, we only care about the aggregated
		#   metric for that particular counterId.  Thus, we want to get the "rejected" list for
		#   instance-level collection, set all imstance attributes to "" and uniquify by counterId attribute
		instance_level_metrics = counter_matcher.prune(all_metrics, pmid_to_fqname)
		if not self._aggregate_only():
			instance_level_metrics, aggregated_metrics = instance_matcher.prune(instance_level_metrics, pmid_to_fqname, return_excluded=True)
			inst = aggregate_instances_maybe(instance_level_metrics, style='glob')
			agg = aggregate_instances_maybe(aggregated_metrics, style='aggregate')
			self.logger.debug(self.dbg_info + "Done querying and pruning available metrics")
			return inst + agg
		else:
			self.logger.debug(self.dbg_info + "Done querying and pruning available metrics")
			return aggregate_instances_maybe(instance_level_metrics, style='aggregate')


	def group_perf_data(self, perfdata_array, output, host, format):
		"""
		Parses performance data 

		@param perfdata_array: Performance data in raw format
		@param host: host from which performance data is being collected
		@param output: Object of output handler to write data to stdout
		@param format: Define perfdata format type. Possible values for this: 'csv' or 'normal'
		
		Expects that metric cache has been set on the handler.
		"""
		for perfdata in perfdata_array: # entities
			if (format == 'csv' and perfdata.sampleInfoCSV is None) or (format == 'normal' and perfdata.sampleInfo is None): 
				self.logger.debug(self.dbg_info + "Missing sample info for entity={0} of type={1}, skipping record".format(
					perfdata.entity.value, perfdata.entity._type))
				continue
			timestamps = timestamps = self._process_timestamps(perfdata, format)
			for pmser in perfdata.value: # counters (group, instance, name)
				if format == 'csv':
					data_values = list(map(int, pmser.value.split(',')))
				else:
					# normal format type has value in array format
					data_values = pmser.value
				pc = self.pcs_by_key[pmser.id.counterId]
				fqname = 'vsphere.cluster.{metric_name}'.format(metric_name=self.pcs_idx_name_by_key[pmser.id.counterId])
				group = pc.groupInfo.key
				entity_name = perfdata.entity.value
				rollup = str(pc.rollupType)
				unit = str(pc.unitInfo.key)
				# instance value of None or "" means this is an aggregated metric
				inst = pmser.id.instance if pmser.id.instance else "aggregated"
				global cluster_dict
				try:
					if perfdata.entity._type == "ClusterComputeResource" and entity_name not in cluster_dict:
						cluster_mor = ManagedObjectReference(value=entity_name, _type="ClusterComputeResource")
						cluster_mo = Connection.vim25client.createExactManagedObject(cluster_mor)
						name = cluster_mo.getCurrentProperty("name")
						cluster_dict[entity_name] = name
				except Exception as e:
					self.logger.warn("Configuration of cluster: {0} is not available, Error: {1}.".format(entity_name, e))
				sourcetype = 'vmware_inframon:perf:{group}'.format(group=group)
				data_values = [float(x)/100 if unit == "percent" else x for x in data_values]
				for tsi in range(len(timestamps)): # times
					# timestamps are returned as UTC: 2013-04-01T23:06:00Z
					ts = timestamps[tsi]
					buf = {'metric_name': fqname, 'value': data_values[tsi], 'moid': entity_name, 'instance': inst, 'name': cluster_dict.get(entity_name, None), 'vcenter': host, 'pool_name': self.pool_name, 'entity_type': 'vsphere.cluster', 'vmware_metric_aggregation': rollup, 'unit': unit}
					output.sendData(json.dumps(buf, ensure_ascii=False), sourcetype=sourcetype, source="VMPerf:ClusterComputeResource", host=host, time=utils.ConvertIsoUtcDate(ts), index=self.dest_index)
						
	def run_collection(self, start_time, end_time):
		"""
		Updates the vc, entity lists, metrics lists; iterates over entities
		by type, calling queryPerf.  Returns a concatenated array of data 
		returned by queryPerf (array entries correspond to entities).

		start_time (datetime) - earliest data timestamp, argument to the queryPerf vipython call
		end_time (datetime) - latest data timestamp, argument to the queryPerf vipython call

		(start, end] form a half-closed interval
		"""
		
		if end_time - start_time < datetime.timedelta(seconds=1):
			start_time = end_time - datetime.timedelta(seconds=1)
			
		perf_data = []
		vc_id = self._update_counters_cache()
		entities = []
		if not self._is_entity_excluded('ClusterComputeResource'): 
			entities = self._find_clusters()		
			self.logger.debug(self.dbg_info + "Updated entity lists: number of clusters: %d" % (len(entities)))
		else:
			self.logger.debug(self.dbg_info + "Entity ClusterComputeResource excluded for collection")

		if len(entities) > 0:
			metrics = self._prepare_metrics_lists(entities, vc_id)

			self.logger.debug(self.dbg_info + "calling QueryPerf on ClusterComputeResource")
			perf_data = self._query_perf(entities, metrics, start_time=start_time, end_time=end_time)
	
			self.logger.debug(self.dbg_info + "Done grabbing data from vc")
		return perf_data
		
	def collect_performance(self, start_time, end_time, output_handler, host=None):
		"""
		Kicks off the data collection: updates inventory, metric lists (if need be), queries the VC for data, and formats results.

		start_time (datetime) - earliest data timestamp, argument to the queryPerf vipython call
		end_time (datetime) - latest data timestamp, argument to the queryPerf vipython call
		output_handler - received from the invoking handler, used to direct the output
		host - name of the target collection VC (used primarily to set host field in the output manager)

		(start, end] form a half-closed interval
		"""
		# get format type (default 'csv')
		format_type = self.config.get('perf_format_type', 'csv')
		self._check_format_type(format_type)
		
		if host is None: host = self._vc_saved_id
		perf_data = self.run_collection(start_time, end_time)
		self.group_perf_data(perf_data, output_handler, host, format=format_type)
		self.logger.debug(self.dbg_info + "Successfully collected perf data batch: type={0}".format(self.config['perf_collection_type']))

