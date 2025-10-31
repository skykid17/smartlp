# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
import logging, logging.handlers
from splunk.clilib.bundle_paths import make_splunkhome_path

def setupLogger(logger=None, log_format='%(asctime)s %(levelname)s | pid:%(process)d | %(filename)s:%(funcName)s:%(lineno)d | [vim25] %(message)s', level=logging.INFO, log_name="splunk_vsphere_vim25.log", max_bytes=2500000, backup_count=5):
	"""
	Setup a logger suitable for splunkd consumption
	"""
	if logger is None:
		logger = logging.getLogger('vim25')
	
	logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
	logger.setLevel(level)
	
	file_handler = logging.handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', log_name]), maxBytes=max_bytes, backupCount=backup_count)
	formatter = logging.Formatter(log_format)
	file_handler.setFormatter(formatter)
	
	logger.handlers = []
	logger.addHandler(file_handler)
	
	logger.debug("Init splunk vSphere {} logger".format(logger.name))
	
	return logger

logger = setupLogger()