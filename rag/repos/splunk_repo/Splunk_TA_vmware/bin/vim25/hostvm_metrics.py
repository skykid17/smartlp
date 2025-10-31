from vim25.connection import Connection
from vim25.mo import ManagedObjectReference
import re

class MetricsCache(object):
	def __init__(self, hostmoid, vmmoid, vm_metric_allowlist=[], vm_metric_denylist=[], host_metric_allowlist=[], host_metric_denylist=[]):
		"""This class will set "fullcounters" to an dictionary with keys structured like so:
		as a side note, this would be better stored as a set of listed objects for structure,
		but I don't want to test pickling in hydra incase we ever go cross os...  SO nested
		dicts it is!  This class also always assumes an active connection object.

		fullcounters = {"hostmetrics":fullhostcounters,"vmmetrics":fullvmcounters, "vmrefreshrate":self.vmrefreshrate, "hostrefreshrate":self.hostrefreshRate}
	
		Instantiated with kwargs:
			@hostmoid - moid of the host to store a metric cache for
			@vmmoid - moid of a vm currently residing on the host.  Used to query vm counters.  Should be a list at max 5 vms.
			@vm_metric_allowlist - virtual machine metrics allow list
			@vm_metric_denylist - virtual machine metrics deny list
			@host_metric_allowlist - host system metrics allow list
			@host_metric_denylist - host system metrics deny list
		"""
		self.perfManager = Connection.perfManager
		self.hostmoid=hostmoid
		self.vmmoid=vmmoid
		self.vm_metric_allowlist = [re.compile(x) for x in vm_metric_allowlist]
		self.vm_metric_denylist = [re.compile(x) for x in vm_metric_denylist]
		self.host_metric_allowlist = [re.compile(x) for x in host_metric_allowlist]
		self.host_metric_denylist = [re.compile(x) for x in host_metric_denylist]
		self.hostsystem = Connection.vim25client.createExactManagedObject(mor=ManagedObjectReference(value=self.hostmoid, _type="HostSystem"))
		self.vm = []
		self.vmrefreshrate=0
		count=0
		if vmmoid:
			for vm in vmmoid:
				if count<=5:
					currentvm = Connection.vim25client.createExactManagedObject(mor=ManagedObjectReference(value=vm, _type="VirtualMachine"))
					currentvmrefreshrate = self._queryRefreshRate(currentvm)
					if currentvmrefreshrate < self.vmrefreshrate or self.vmrefreshrate==0:
						self.vmrefreshrate = currentvmrefreshrate
					self.vm.append(currentvm)
					count=count+1
				else:
					break
			self.counterlistvm = self._queryVMCounters()
		else:
			self.vmrefreshrate=0
			self.counterlistvm = []
		self.hostrefreshRate = self._queryRefreshRate(self.hostsystem)
		self.counterlisthost = self._queryHostCounters()
		if self.counterlisthost:
			self.fullcounters = self._getCounterListsNames()
		else:
			self.fullcounters = None
			
	def _queryRefreshRate(self, entity):
		pps = self.perfManager.queryPerfProviderSummary(entity)
		return pps.refreshRate
		
	def _queryHostCounters(self):
		counterlisthost = set()
		for counter in self.perfManager.queryAvailablePerfMetric(self.hostsystem, intervalId=self.hostrefreshRate):
			counterlisthost.add(counter.counterId)
		return counterlisthost
		
	def _queryVMCounters(self):
		counterlistvm = set()
		for vm in self.vm:
			for counter in self.perfManager.queryAvailablePerfMetric(vm, intervalId=self.vmrefreshrate):
				counterlistvm.add(counter.counterId)
		return counterlistvm
	
	def _pruneAllowDenylists(self, listtoprune, allowlist, denylist):
		'''
		Must be passed as regex compiled python objects.  re.compile("string").
		Will return a list with items pruned.  Items that match the allowlist AND are not
		in the denylist will be returned.  A blank allowlist will assume that all entries are allowed.
		a blank denylist will assume no entries are denied.
		'''
		res = []
		for metric in listtoprune:
			processmetric=True
			if allowlist and denylist:
				#There is a allowlist pattern specified and a denylist pattern
				processmetric=False
				if [regexmatch for regexmatch in allowlist if regexmatch.match(metric['name'])] and not [regexmatch for regexmatch in denylist if regexmatch.match(metric['name'])]:
					processmetric=True
			elif allowlist and not denylist:
				#There is a allow list and no denylist
				processmetric=False
				if [regexmatch for regexmatch in allowlist if regexmatch.match(metric['name'])]:
					processmetric=True
			elif not allowlist and denylist:
				#There is no allowlist and there is a denylist
				if [regexmatch for regexmatch in denylist if regexmatch.match(metric['name'])]:
					processmetric=False
			if processmetric:
				res.append(metric)
		return res

	def _getCounterListsNames(self):
		if self.counterlistvm:
			counterlistvmnames=self.perfManager.queryPerfCounter(counterId=list(self.counterlistvm))
			fullvmcounters = []
			for counter in counterlistvmnames:
				fullvmcounters.append({"id":counter.key, "name":"_".join(['p', counter.rollupType, counter.groupInfo.key, counter.nameInfo.key, counter.unitInfo.key]), "group":str(counter.groupInfo.key)})
			if self.vm_metric_allowlist or self.vm_metric_denylist:
				fullvmcounters = self._pruneAllowDenylists(fullvmcounters, self.vm_metric_allowlist, self.vm_metric_denylist)
		else:
			fullvmcounters = []
		counterlisthostnames=self.perfManager.queryPerfCounter(counterId=list(self.counterlisthost))
		fullhostcounters = []
		for counter in counterlisthostnames:
			fullhostcounters.append({"id":counter.key, "name":"_".join(['p', counter.rollupType, counter.groupInfo.key, counter.nameInfo.key, counter.unitInfo.key]), "group":str(counter.groupInfo.key)})
		if self.host_metric_allowlist or self.host_metric_denylist:
			fullhostcounters = self._pruneAllowDenylists(fullhostcounters, self.host_metric_allowlist, self.host_metric_denylist)
		return {"hostmetrics":fullhostcounters,"vmmetrics":fullvmcounters, "vmrefreshrate":self.vmrefreshrate, "hostrefreshrate":self.hostrefreshRate}
