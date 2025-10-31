# -*-  indent-tabs-mode:nil;  -*- 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved. 

import datetime
from vim25 import utils
from vim25.connection import Connection
from vim25.metrics_cache import MetricsCache
from vim25.metrics_list_matcher import MetricsListMatcher
import json

class VCPerfCollector(Connection):
	"""
	Class responsible for retrieval and output of vcenter performance metrics.

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
		self.logger.debug(self.dbg_info + "Instantiating vcenter perf collection class for %s" % (config['perf_collection_type']))
		self._ref_rate_cache = {}
		self._counters_cache = {} # format: {self.domain: {'pcs_by_key': {}, 'pcs_fqname_by_key': {}, 'pcs_idx_name_by_key': {}}}
		self._metrics_cache = {}  # format: {self.domain: MetricsCache(2000, 50)}
		self._entity_allow_deny_list_cache = {}
		self.pool_name = config.get("pool_name", None)
		self._vc_saved_id = None
		self.instanced = False # Set True if Instance level data collection is required

	def update_config(self, newconfig):
		"""
		Updates the config member variable.
		"""
		def config_same(c1, c2):
			include_keys = ['vc_metric_allowlist', 'vc_metric_denylist', 'perf_index', 'perf_format_type']
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
		
	def _prepare_metrics_lists(self, entity, vc_id):
		"""
		Prepares and caches metric lists for entity.

		Caching is done to ensure that for a given inventory set, 
		the metrics are only retrieved once.

		Returns: metrics as a dict of lists keyed by entity type.
		"""
		inventory_hash = hash(frozenset([vc_id] + [hash(frozenset([entity.value]))]))
		metrics = {}
		entity_allow_deny_list = {'vc_metric_allowlist': self.config.get("vc_metric_allowlist", []),
					   'vc_metric_denylist' : self.config.get("vc_metric_denylist", [])}
		
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

			metrics = self.get_all_metrics(entity)
			cache[inventory_hash] = metrics
		return metrics

	def _get_fqname(self, pc):
		return ".".join([pc.groupInfo.key, pc.rollupType, pc.nameInfo.key, pc.unitInfo.key])
	
	def _get_idx_name(self, pc):
		return ".".join([pc.groupInfo.key, pc.nameInfo.key])
		
	def _get_ref_rate_for_entity(self, entity):
		"""
		Gets the refresh rate for the metrics.  
		
		This value is assumed to be fixed for a given entity type on a given
		collection run.
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

	def _query_perf(self, entity, pmids, start_time=None, end_time=None):
		"""
		Construct PerfQuerySpec and invoke queryPerf vipython method on the performance manager object.
		
		entities (list of MORs)
		start/end_time are optional; they form a (start, end] half-closed interval
		Returns: list of PerfEntityMetricCSV
		
		Long lists of entities require several calls to queryPerf
		"""
		perfdata = []
		try:
			qspecs = Connection.vim25client.new('PerfQuerySpec', entity=entity, metricId=pmids, format= self.config.get('perf_format_type', 'csv'), intervalId=self._get_ref_rate_for_entity(entity), 
												startTime=start_time, endTime=end_time)
			perfdata = Connection.perfManager.queryPerf(qspecs)
			self.logger.debug(self.dbg_info + "Collected data: collection_type={coll}, entity_type={type}, entity={ent}, start_time={s}, end_time={e}".format(coll=self.config['perf_collection_type'], type=entity._type, ent=entity.value,
													s=start_time, e=end_time))
		except Exception as e:
			self.logger.error(str(e))
			raise
		return perfdata

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

	def get_all_metrics(self, entity, mode='regex'):
		"""
		Gets performance metrics for entity provided a given refresh rate and	
		relevant allowlists and denylists.
		
		entity - Root Folder
		
		Keyword args:
		mode: MetricsListMatcher mode parameter ["regex" | "verbatim"]
		
		Returns:
		list of PerfMetricId's
		"""
		self.logger.debug(self.dbg_info + "Querying and pruning available metrics")

		refresh_rate = self._get_ref_rate_for_entity(entity)
		counteridlist = set()
		all_metrics = []
		for counter in self.perfManager.queryAvailablePerfMetric(entity, intervalId=refresh_rate):
			counteridlist.add(counter.counterId)
		if self.instanced:
			all_metrics=[self.vim25client.new('PerfMetricId', counterId=counterid, instance="*") for counterid in counteridlist]
		else:	
			all_metrics=[self.vim25client.new('PerfMetricId', counterId=counterid, instance="") for counterid in counteridlist]
		
		counter_matcher = MetricsListMatcher(self.config['vc_metric_allowlist'],
											 self.config['vc_metric_denylist'], mode)
		pmid_to_fqname = lambda pmid: self.pcs_fqname_by_key[pmid.counterId]
		req_metrics = counter_matcher.prune(all_metrics, pmid_to_fqname)
		return req_metrics


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
			if (format == 'csv' and perfdata.sampleInfoCSV is None) or (format == 'normal' and not hasattr(perfdata, 'value')): 
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
				fqname = 'vsphere.vc.{metric_name}'.format(metric_name=self.pcs_idx_name_by_key[pmser.id.counterId])
				group = pc.groupInfo.key
				entity_name = perfdata.entity.value
				rollup = str(pc.rollupType)
				unit = str(pc.unitInfo.key)
				# instance value of None or "" means this is an aggregated metric
				inst = pmser.id.instance if pmser.id.instance else "aggregated"
				sourcetype = 'vmware_inframon:perf:{group}'.format(group=group)
				# values labeled percent are actually in units of % * 100, so must convert
				data_values = [float(x)/100 if unit == "percent" else x for x in data_values]
				for tsi in range(len(timestamps)): # times
					# timestamps are returned as UTC: 2013-04-01T23:06:00Z
					ts = timestamps[tsi]
					buf = {'metric_name': fqname, 'value': data_values[tsi], 'moid': entity_name, 'instance': inst, 'vcenter': host, 'pool_name': self.pool_name, 'entity_type': 'vsphere.vcenter', 'vmware_metric_aggregation': rollup, 'unit': unit}
					output.sendData(json.dumps(buf, ensure_ascii=False), sourcetype=sourcetype, source="VMPerf:VcenterServer", host=host, time=utils.ConvertIsoUtcDate(ts), index=self.dest_index)
						
	def run_collection(self, start_time, end_time):
		"""
		Updates the vc, metrics lists; calling queryPerf. 
		Returns a concatenated array of data 
		returned by queryPerf (array entries correspond to entities).

		start_time (datetime) - earliest data timestamp, argument to the queryPerf vipython call
		end_time (datetime) - latest data timestamp, argument to the queryPerf vipython call

		(start, end] form a half-closed interval
		"""
		
		if end_time - start_time < datetime.timedelta(seconds=1):
			start_time = end_time - datetime.timedelta(seconds=1)
			
		perf_data = []
		vc_id = self._update_counters_cache()
		entity = Connection.rootFolder.getMOR()
		metrics = self._prepare_metrics_lists(entity, vc_id)

		self.logger.debug(self.dbg_info + "calling QueryPerf on %s", entity)
		perf_data = self._query_perf(entity, metrics, start_time=start_time, end_time=end_time)
		self.logger.debug(self.dbg_info + "Done grabbing data from vc")
		return perf_data
		
	def collect_performance(self, start_time, end_time, output_handler, host=None):
		"""
		Kicks off the data collection: updates metric lists (if need be), queries the VC for data, and formats results.

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

