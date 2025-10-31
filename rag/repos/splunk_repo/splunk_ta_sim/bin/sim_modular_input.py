# Copyright (C) 2005-2020 Splunk Inc. All Rights Reserved.
from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, json, requests, re,logging,uuid,multiprocessing, threading
from multiprocessing.pool import ThreadPool

current_path = os.path.dirname(__file__)
sys.path.append(os.path.join(current_path, '..', 'libs'))
sys.path.append(os.path.join(current_path, '..', 'libs', 'external'))

from solnlib.modular_input import ModularInput, XMLEvent
import noah_event_writer
import stack_info
from splunklib.client import Service
from splunklib.binding import HTTPError

import signalfx, sim_common
from signalfx.signalflow import SignalFlowClient,messages,sse

from splunklib.searchcommands import environment


class SIMModularInput(ModularInput):
    """
    Class that implements all the required steps. See method `do_run`.
    """
    # Constants
    SPLUNK_SIM_CONF_NAME = 'sim'
    SPLUNK_SIM_CONF_API_STANZA_NAME = 'sim_api'
    SIM_MOD_INPUT_METADATA_FIELDS_TO_IGNORE_IN_MATERIALIZED_VIEW = 'sf_createdOnMs,sf_isPreQuantized,sf_key,sf_metric,sf_type,sf_singletonFixedDimensions, sf_originatingMetric'
    SIM_MOD_INPUT_METADATA_FIELDS_TO_IGNORE_IN_OPTIMIZED_VIEW = 'sf_createdOnMs,sf_isPreQuantized,sf_metric,sf_type,sf_singletonFixedDimensions'
    SIM_FLOW_LIMIT_MSG_CODE = 'FIND_LIMITED_RESULT_SET'
    MAX_BACKFILL_TIME = 3600000
    MAX_DELAY = 900000
    MIN_DELAY = 2000
    SPLUNK_MODULARINPUT_COLLECTION = 'https://127.0.0.1:{}/servicesNS/nobody/splunk_ta_sim/storage/collections/data/sim_modularinputs'
    SPLUNK_MODULARINPUT_URL = 'https://127.0.0.1:{}/services/data/inputs/sim_modular_input?output_mode=json'
    
    # internal class variables
    sim_api_url = None
    sim_api_token = None
    sim_realm = 'us0'
    sim_flow_client = None
    sim_mod_input_retry_wait_time = 3
    sim_mod_input_retry_count = 3

    # modular input properties
    title = 'Splunk Infrastructure Monitoring Data Streams'
    description = 'Streams Infrastructure Monitoring metrics data into Splunk using SignalFlow programs.'
    app = 'splunk_ta_sim'
    name = 'sim_modular_input'
    use_single_instance = False
    use_kvstore_checkpointer = False
    # kvstore_checkpointer_collection_name = 'checkpoint'
    # checkpointer_obj = None
    stop_mod_input_when_one_computation_fails = False
    backfill_timestamp_update_frequency = 5
    detail_log_frequency = 5
    
    # modular input conf init
    sim_mod_input_enable_materialized_view = 1
    sim_mod_input_store_to_metric_index = 1
    index = 'sim_metrics'
    sourcetype = 'stash'
    use_hec_event_writer = False
    hec_input_name = 'sim_modular_input'
    msg_last_seen = time.time()


    def extra_arguments(self):
        return [
                    {
                        'name': 'org_id',
                        'title': 'Organization ID',
                        'description': 'Provide the Infrastructure Monitoring Organization ID to fetch metrics data from.'
                    },
                    {
                        'name': 'signal_flow_programs',
                        'title': 'SignalFlow Program',
                        'description': 'Provide a SignalFlow program to stream Infrastructure Monitoring metrics data into Splunk.'
                    },
                    {
                        'name': 'additional_meta_data_flag',
                        'title': 'Additional Metadata Flag',
                        'description': 'If 1, the metrics stream results contain full metadata. Defaults to 0.'
                    },
                    {
                        'name': 'sim_modinput_restart_interval_seconds',
                        'title': 'Restart Interval for Modular Input',
                        'description': 'Only applies when data is not being received. The default value is 3600s(1 hour), maximum value is 86400s(24 hours) and minimum is 900s(15 minutes). Setting this to -1 disables the restart interval.'
                    },
                    {
                        'name': 'metric_resolution',
                        'title': 'Metric Resolution',
                        'description': 'The interval for retrieving data in milliseconds. Default enables the system to determine the resolution. Set this to a static value to hardcode the interval for your data.'
                    },
                    {
                        'name': 'sim_max_delay',
                        'title': 'Max wait time for delayed data',
                        'description': 'The default of -1 calculates optimal return time based on your lag history and waits for delayed data before returning. To override defaults, set the maximum time you\'re willing to wait for delayed data, using a value between 2000 ms and 900000 ms. Data arriving after that set time is not retrieved.'
                    },
                ]

    def do_run(self, stanzas_config):
        """
        This is the method called by splunkd when mod input is enabled.
        @type stanzas_config: dict
        @param stanzas_config: input config for all stanzas passed down by splunkd.
        """
        flow_programs_thread_pool =  None
        self.mod_input_instance_name = ''
        self.modularinput_collection = 'sim_modularinputs'

        try:
            
            if len(stanzas_config) == 0:
                # if no stanzas are present, The feature is disabled.
                return
            
            self.stanza_name = next(iter(stanzas_config.keys()))
            self.stanza_config = next(iter(stanzas_config.values()))
            self.mod_input_instance_name = (self.stanza_name.split('//')[1]).strip() if '//' in self.stanza_name else self.stanza_name
            
            # Initialize Logger    
            self.logger, self.logging_configuration = environment.configure_logging(self.__class__.__name__)
            self.logger.addFilter(self.LoggerContextFilter())

            # TODO: Wait 20 sec. for the splunk to initialize all its internal services - KV store  
            time.sleep(20)

            if (self.mod_input_instance_name == 'Cleanup_Disabled_Modinput_Data'):
                # Below line of code executes a watcher of modular inputs, which would delete all stale 
                # timestamps stored for disabled/deleted/modified sim modinputs
                self.cleanup_timestamps_of_stale_modinputs()
                return
            
            self.service = Service(scheme=self.server_scheme,host=self.server_host,port=self.server_port,token=self.session_key,owner='nobody')
            self.org_id = self.stanza_config.get('org_id', None)
            
            self.logger.info('status=start, instance_name={0}, stanzas_config={1}, org_id={2}'.format(self.mod_input_instance_name, json.dumps(stanzas_config), self.org_id))
            
            try:
                self.max_delay = int(self.stanza_config.get('sim_max_delay', -1))
            except (TypeError, ValueError) as e:
                self.max_delay = None
            
            if self.max_delay == -1:
                self.max_delay = None
            
            if self.max_delay and self.max_delay > self.MAX_DELAY:
                self.logger.info(f'The Max wait time for delayed data can have maximum value of {self.MAX_DELAY}ms, using  {self.MAX_DELAY} instead of {self.max_delay}')
                self.max_delay = self.MAX_DELAY
            elif self.max_delay and self.max_delay < self.MIN_DELAY:
                self.logger.info(f'The Max wait time for delayed data can have minimum value of {self.MIN_DELAY}ms, using {self.MIN_DELAY} instead of {self.max_delay}')
                self.max_delay = self.MIN_DELAY

            try:
                self.metric_resolution = int(self.stanza_config.get('metric_resolution', -1))
            except (TypeError, ValueError) as e:
                self.metric_resolution = -1

            self.resolution_adjustable = False 
            if self.metric_resolution == -1:
                self.resolution_adjustable = True
                self.metric_resolution = None 
            
            try:
                self.sim_modinput_restart_interval_seconds = int(self.stanza_config.get('sim_modinput_restart_interval_seconds'))
                # Max delay user can expect for this configuration is 24hrs and Minimum value will be 15mins.
                if self.sim_modinput_restart_interval_seconds > 86400:
                    self.logger.info(f'The Maximum value of Restart Interval for Modular Input can have is 86400s which is 24hrs, using 86400s for the restart instead of {self.sim_modinput_restart_interval_seconds}')
                    self.sim_modinput_restart_interval_seconds = 86400
                elif (self.sim_modinput_restart_interval_seconds < 900) and (self.sim_modinput_restart_interval_seconds != -1):
                    self.logger.info(f'The Minimum value of Restart Interval for Modular Input can have is 900s which is 15min, using 900s for the restart instead of {self.sim_modinput_restart_interval_seconds}')
                    self.sim_modinput_restart_interval_seconds = 900
            except (TypeError, ValueError) as e:
                self.logger.error(f"Error while fetching sim_modinput_restart_interval_seconds error {str(e)} falling back to the default value 3600s", exc_info=True)
                self.sim_modinput_restart_interval_seconds = 3600
                
            try:
                self.additional_meta_data_flag = bool(int(self.stanza_config.get('additional_meta_data_flag', 0)))
            except (TypeError, ValueError) as e:
                self.additional_meta_data_flag = 0
            
            try:
                self.logger.info('status=start, instance_name={0}, org_id={1}, action=get_sim_connection'.format(self.mod_input_instance_name,self.org_id))
                self.sim_connection = sim_common.SIMConnection(self.service,self.org_id)
                self.org_id = self.sim_connection.org_id
                self.sim_realm = self.sim_connection.realm
                self.logger.info('status=complete, action=get_sim_connection, instance_name={0}, org_id={1}, is_default={2}, org_name={3}, realm={4}, access_token=*************{5}'.format(
                    self.mod_input_instance_name,self.sim_connection.org_id,self.sim_connection.is_default,self.sim_connection.org_name,self.sim_connection.realm,self.sim_connection.access_token[-4:]))
            except Exception as e:
                self.logger.error('status=error, instance_name={0}, org_id={1}, action=get_sim_connection, error_msg={1}'.format(self.mod_input_instance_name,self.org_id,str(e)), exc_info=True)
                return
            
            # Initialization: Splunk Infrastructure Monitoring Flow Mod Input #####################################################################################
            self.logger.info('status=start, action=initialize, instance_name={0}, org_id={1}, realm={1}'.format(self.mod_input_instance_name,self.org_id))
            
            
            # fetch the value of backfill_timestamp from sim_modularinputs collection
            try:
                query = {"title":self.mod_input_instance_name}
                response = self.modularinput_collection_data(request_type="GET", query_params=query)
                self.logger.info(f'check if backfill timestamp is present for the modinput {self.mod_input_instance_name}')
                if response.status_code == 200 and json.loads(response.content):
                    self.backfill_timestamp = json.loads(response.content)[0].get('last_timestamp_fetch')
                    self.modinput_key = json.loads(response.content)[0].get('_key')
                    self.logger.info(f'Backfill timestamp is present for the modinput  {self.mod_input_instance_name} {self.backfill_timestamp }')
                else:
                    self.backfill_timestamp = int(time.time()*1000)
                    self.logger.info(f'Backfill timestamp is NOT present for the modinput {self.mod_input_instance_name} fetching data from currenttime')
                    modinput_data = {
                                "title":self.mod_input_instance_name,
                                "last_timestamp_fetch": self.backfill_timestamp
                            }
                    response = self.modularinput_collection_data(request_type="POST", modinput_data=modinput_data)
                    self.modinput_key = json.loads(response.content).get('_key')
            except Exception as e:
                    self.logger.info("status=error, action=Fetch backfill_timestamp from collection, error_msg = {}".format(str(e)), exc_info=True)

            # self.backfill_timestamp_key = self.mod_input_instance_name + ':backfill_timestamp'
            # self.checkpointer_obj = self.checkpointer
            # self.backfill_timestamp = self.checkpointer_obj.get(self.backfill_timestamp_key)
            # current_timestamp = int(time.time()*1000)
            
            # if self.backfill_timestamp is None:
            #     self.backfill_timestamp = int(current_timestamp)
            #     self.checkpointer_obj.update(self.backfill_timestamp_key, self.backfill_timestamp)
            # else:
            #     # Apply backfill limit
            #     self.backfill_timestamp = max(current_timestamp - self.MAX_BACKFILL_TIME, int(self.backfill_timestamp))

            self.sim_api_conf_stanza = sim_common.get_conf_stanza(self.service,self.SPLUNK_SIM_CONF_NAME,self.SPLUNK_SIM_CONF_API_STANZA_NAME)
            self.sim_mod_input_metadata_fields_to_ignore_in_materialized_view = [x.strip() for x in self.sim_api_conf_stanza.get('sim_mod_input_metadata_fields_to_ignore_in_materialized_view',self.SIM_MOD_INPUT_METADATA_FIELDS_TO_IGNORE_IN_MATERIALIZED_VIEW).split(',')]
            self.sim_mod_input_metadata_fields_to_ignore_in_optimized_view = [x.strip() for x in self.sim_api_conf_stanza.get('sim_mod_input_metadata_fields_to_ignore_in_optimized_view',self.SIM_MOD_INPUT_METADATA_FIELDS_TO_IGNORE_IN_OPTIMIZED_VIEW).split(',')]
            self.sim_mod_input_retry_wait_time = int(self.sim_api_conf_stanza.get('sim_mod_input_retry_wait_time',5))
            self.sim_mod_input_retry_count = int(self.sim_api_conf_stanza.get('sim_mod_input_retry_count',3))
            self.stop_mod_input_when_one_computation_fails_flag = int(self.sim_api_conf_stanza.get('sim_mod_input_stop_mod_input_when_one_computation_fails',0))
            self.sim_api_signal_flow_use_sse = int(self.sim_api_conf_stanza.get('sim_api_signal_flow_use_sse',0))
            self.sim_api_proxy_url = self.sim_api_conf_stanza.get('sim_api_proxy_url',None)
            
            # modular input conf setup
            self.sim_mod_input_store_to_metric_index = int(self.sim_api_conf_stanza.get('sim_mod_input_store_to_metric_index',self.sim_mod_input_store_to_metric_index))
            self.sim_mod_input_enable_materialized_view = int(self.sim_api_conf_stanza.get('sim_mod_input_enable_materialized_view',self.sim_mod_input_enable_materialized_view))
            self.index = self.stanza_config.get('index', self.index)
            self.sourcetype = self.stanza_config.get('sourcetype', self.sourcetype)
            
            # send the data to metric index only when materialized view is enabled
            if not self.sim_mod_input_enable_materialized_view:
                self.sim_mod_input_store_to_metric_index = 0
            # create hec token only when the mod input required to send the data to metric index
            if self.sim_mod_input_store_to_metric_index:
                self.use_hec_event_writer = True
                self.hec_global_settings_schema = True
            
            # Get SignalFlow Programs from KV Store
            self.signalflow_programs = [x.strip() for x in self.stanza_config.get('signal_flow_programs', '').split('|') if x]
            # Remove first and last double quotes and Remove empty SignalFlow Programs from the list
            self.signalflow_programs = [y.strip() for y in [re.sub(r'^"|"$', '', x) for x in self.signalflow_programs if x] if y.strip()]
                
            self.logger.info('status=complete, action=initialize, instance_name={0}, org_id={1}, index={2}, enable_materialized_view={3}, store_to_metric_index={4}, use_hec_event_writer={5}, metric_resolution={6}, additional_meta_data_flag={7}, backfill_timestamp={8}, signalflow_programs={9},signalflow_computation_count={10}, sim_realm={11}, sim_stream_api_url={12}, sim_api_token=*******{13}, sim_api_conf_stanza={14},'.format(
                              self.mod_input_instance_name,self.org_id, self.index, str(self.sim_mod_input_enable_materialized_view), str(self.sim_mod_input_store_to_metric_index), str(self.use_hec_event_writer),str(self.metric_resolution), str(self.additional_meta_data_flag), str(self.backfill_timestamp), ' | '.join(self.signalflow_programs),len(self.signalflow_programs),self.sim_realm, self.sim_connection.sim_stream_url, self.sim_connection.access_token[-4:],json.dumps(self.sim_api_conf_stanza)))
            
            flow_programs_thread_pool = None
            if len(self.signalflow_programs) > 1:
                # Run Signal Flow Programs in multi thread pool
                pool_process_size = len(self.signalflow_programs) # min (multiprocessing.cpu_count() * 2, len(self.signalflow_programs))
                self.logger.info('status=start, action=initialize_flow_programs_thread_pool, instance_name={0}, org_id={1}, pool_process_size={2}'.format(self.mod_input_instance_name,self.org_id,str(pool_process_size)))
                flow_programs_thread_pool = ThreadPool(pool_process_size)
                self.logger.info('status=start, action=execute_flow_programs_thread_pool, instance_name={0}, org_id={1}'.format(self.mod_input_instance_name,self.org_id))
                flow_programs_thread_pool.map(self.run_signalflow_program, self.signalflow_programs)
                self.logger.info('status=complete, action=execute_flow_programs_thread_pool, instance_name={0}, org_id={1}'.format(self.mod_input_instance_name,self.org_id))
            elif len(self.signalflow_programs) == 1:
                self.run_signalflow_program(self.signalflow_programs[0])
            
        except Exception as e:
            self.logger.error('status=error, instance_name={0}, org_id={1}, error_msg={2}'.format(self.mod_input_instance_name,self.org_id,str(e)), exc_info=True)
        finally:
            if flow_programs_thread_pool is not None:
                flow_programs_thread_pool.terminate()
                self.logger.info('status=complete, action=terminate_flow_programs_thread_pool, instance_name={0}, org_id={1}'.format(self.mod_input_instance_name,self.org_id))
                flow_programs_thread_pool.close()
                self.logger.info('status=complete, action=close_flow_programs_thread_pool, instance_name={0}, org_id={1}'.format(self.mod_input_instance_name,self.org_id))
                
            self.logger.info('status=stop, instance_name={0}, org_id={1}, stanza_config={2}'.format(self.mod_input_instance_name,self.org_id, json.dumps(self.stanza_config)))

    # Run: Splunk Infrastructure Monitoring Flow Mod Input #####################################################################################
    # TODO: make sure the ever run is thread safe. don't set any external class variables.
    def run_signalflow_program(self,signalflow_program):
        
        thread_id = uuid.uuid4().hex
        sim_flow_client = None
        retry_count = 0 
        backfill_timestamp = self.backfill_timestamp

        # Create event writer based on stack type
        self.writer = self.get_event_writer()

        '''
            watchdog_bark will stop the modular input execution if the data is delayed more than the configured time interval.
            Eg: self.sim_modinput_restart_interval_seconds = 900
            if the data is delayed more then 900 secs the modular input will stop.
        '''
        def watchdog_bark():
            self.logger.info("Watchdog for the {} started, will shutdown the modularinput in {} seconds if data stops coming".format(self.mod_input_instance_name, self.sim_modinput_restart_interval_seconds))
            self.break_watchdog = False
            while True:
                if self.break_watchdog:
                    break
                try:
                    current_time = time.time()
                    if int(current_time - self.msg_last_seen) > int(self.sim_modinput_restart_interval_seconds):
                        self.logger.info(f'Data from modular input has been delayed for more than configured time interval {self.sim_modinput_restart_interval_seconds}-secs, exiting the modularinput')
                        sim_flow_client.close()
                        self.logger.error('Sim modularinput {} timed out after {} seconds'.format(self.mod_input_instance_name, self.sim_modinput_restart_interval_seconds))
                        os._exit(1)
                    time.sleep(5)
                except Exception as e:
                    self.logger.info("status=complete, action=Error while executing watchdog_bark method, error_msg = {}".format(str(e)), exc_info=True)
                    break
        
        if int(self.sim_modinput_restart_interval_seconds) != -1:
            watchdog = threading.Thread(target=watchdog_bark)
            watchdog.start()

        
        # Retry Loop
        while retry_count<self.sim_mod_input_retry_count and not self.stop_mod_input_when_one_computation_fails:
            try:
                self.logger.info('status=start, action=run_signalflow_program, instance_name={0}, org_id={1}, thread_id={2}, signalflow_program="{3}",retry_count={4}'.format(
                    self.mod_input_instance_name,self.org_id, thread_id, signalflow_program,str(retry_count)))         
                
                # Initialize Signal Flow Client
                self.logger.info('status=start, action=initialize_sim_flow_client, thread_id={0}, org_id={1}, retry_count={2}, url={3}, use_sse={4}, proxy_url={5}'.format(
                thread_id,self.org_id,str(retry_count),self.sim_connection.sim_stream_url,str(self.sim_api_signal_flow_use_sse),str(self.sim_api_proxy_url)))      
                if self.sim_api_signal_flow_use_sse:
                    sim_flow_client = SignalFlowClient(token=self.sim_connection.access_token,endpoint=self.sim_connection.sim_stream_url,transport=sse.SSETransport,proxy_url=self.sim_api_proxy_url)
                else:
                    sim_flow_client = SignalFlowClient(token=self.sim_connection.access_token,endpoint=self.sim_connection.sim_stream_url,proxy_url=self.sim_api_proxy_url)
                self.logger.info('status=complete, action=initialize_sim_flow_client, thread_id={0}, org_id={1}, retry_count={2}'.format(thread_id,self.org_id,str(retry_count)))

                
                # Create computation for Signal Flow Program
                computation = sim_flow_client.execute(signalflow_program, start=backfill_timestamp, resolution=self.metric_resolution, max_delay=self.max_delay, withDerivedMetadata=self.additional_meta_data_flag, resolutionAdjustable=self.resolution_adjustable)
                self.logger.info('status=complete, action=create_signalflow_program_computation, thread_id={0}, org_id={1}, retry_count={2}, max_delay={3},  resolutionAdjustable={4}, metric_resolution={5}'.format(thread_id,self.org_id, str(retry_count), self.max_delay, self.resolution_adjustable, self.metric_resolution))
                
                # Stream Signal Flow Program computation Results 
                process_results_error_count, data_msg_count, empty_data_msg_count, metadata_msg_count, mts_count, other_msg_count, computation_id, meta_data, mts_delay  = 0, 0, 0, 0, 0, 0, '', {}, 0
                self.logger.info('status=start, action=stream_sim_flow_program_results, thread_id={0}, org_id={1}, retry_count={2}'.format(thread_id,self.org_id,str(retry_count)))

                for msg in computation.stream():
                    self.msg_last_seen = time.time()
                    if self.stop_mod_input_when_one_computation_fails:
                        break
                    retry_count = 0
                    events = []
                    message_type = msg.__class__.__name__
                    try:
                        if isinstance(msg, messages.MetadataMessage):
                            metadata_msg_count +=1
                            if self.sim_mod_input_enable_materialized_view:
                                # Optimize the proc memory: by removing the common data(sf_organizationID, computationId) from the in-memory metadata dict.  
                                msg.properties.pop('sf_organizationID', None)
                                msg.properties.pop('computationId', None)
                                
                                # rename the sf_originatingMetric to metric_name (splunk metric name field)
                                msg.properties['metric_name'] = msg.properties.get('sf_originatingMetric',None)
                                
                                # Remove unused metadata fields
                                for key in self.sim_mod_input_metadata_fields_to_ignore_in_materialized_view:
                                    msg.properties.pop(key, None)
                                meta_data[msg.tsid] = msg.properties
                            else:
                                for key in self.sim_mod_input_metadata_fields_to_ignore_in_optimized_view:
                                    msg.properties.pop(key, None)
                                raw_json = msg.properties
                                raw_json['md_id'] = computation_id + '.' + msg.tsid
                                raw_json['sf_realm'] = self.sim_realm
                                events.append(self.writer.create_event(data=json.dumps(raw_json), source='sim_metadata', sourcetype=self.sourcetype, index=self.index))
                        elif isinstance(msg, messages.DataMessage):
                                if not msg.data.items():
                                    empty_data_msg_count +=1
                                    continue
                                data_msg_count +=1
                                mts_in_data_msg = len(msg.data.items())
                                mts_count += mts_in_data_msg
                                event_time = sim_common.normalize_time(msg.logical_timestamp_ms)
                                mts_delay = time.time() - event_time
                                backfill_timestamp = msg.logical_timestamp_ms
                                modinput_data = {
                                "title":self.mod_input_instance_name,
                                "last_timestamp_fetch": backfill_timestamp
                                }
                                self.modularinput_collection_data(request_type="POST", query_params=str(self.modinput_key), modinput_data=modinput_data)
                                
                                # Metrics index Source type - not to incur license usage
                                # options 1 (Current implemnation). use HEC to ingest the data from mod input to index - no license usage
                                # Data Path: IDM(Mod input) to HEC(IDM) to IDX
                                # stash - https://docs.splunk.com/Documentation/SplunkCloud/8.0.2006/SearchReference/Collect
                                
                                # options 2. use mcollect_stash csv format and emit sys.stdout.write(data) - no license usage
                                # Data Path: IDM (std.out) to IDX
                                # mcollect_stash - https://docs.splunk.com/Documentation/Splunk/8.0.5/SearchReference/Mcollect
                                # Sample csv metric data format
                                # metric_timestamp,namespace,AWSUniqueId,metric_name,_value
                                # 1598306160.000,"AWS/RDS",rds_scwskgnl5pnp6b_us-east-1_507961774953,DatabaseConnections,0.0
                                # 1598306160.000,"AWS/RDS",rds_movies_us-east-1_507961774953,DatabaseConnections,0.0
                                # TODO: how to write CSV stream with sys.write. so mcollect can consume it?
                                
                                # options 3. Create new source type ex- "sim". and set the props INDEXED_EXTRACTIONS = HEC. 
                                # This option incur license usage.
                                
                                # event_with_common_fields = {'time': event_time, 'event': 'metric', 'index':self.index, 'source':'sim'}
                                for k, v in msg.data.items():
                                    if self.sim_mod_input_enable_materialized_view:
                                        if k in meta_data:
                                            fields = meta_data.get(k).copy()
                                            fields['_value'] = v
                                            fields['sf_realm'] = self.sim_realm
                                            # Optimize the proc memory: by adding the common data(sf_organizationID, sf_resolutionMs, computationId) at output generation time. 
                                            fields['sf_organizationID'] = self.org_id
                                            fields['sf_resolutionMs'] = self.metric_resolution
                                            fields['computationId'] = computation_id
                                            if self.sim_mod_input_store_to_metric_index:
                                                # event = event_with_common_fields.copy()
                                                # event['fields'] = fields
                                                
                                                events.append(self.writer.create_event(data={}, time=event_time, source='sim', sourcetype=self.sourcetype, index=self.index, fields=fields))
                                            else:
                                                events.append(self.writer.create_event(data=json.dumps(fields), time=event_time, source='sim',sourcetype=self.sourcetype, index=self.index)) 
                                    else:
                                        flat_json = {}
                                        flat_json['md_id'] = computation_id + '.' + k
                                        flat_json['_value'] = v
                                        events.append(self.writer.create_event(data=json.dumps(flat_json), time=event_time, source='sim_mts',sourcetype=self.sourcetype, index=self.index)) 

                                # TODO: SignalFlow is not working for backfill_date. its only working for current time. 
                                # if data_msg_count % self.backfill_timestamp_update_frequency == 0:
                                #     if self.checkpointer_obj is not None: 
                                #         self.checkpointer_obj.update(self.backfill_timestamp_key, backfill_timestamp)
                                #         self.logger.info('status=complete, action=update_backfill_timestamp, instance_name={0}, org_id={1}, thread_id={1}, signalflow_program="{2}", computation_id={3}, backfill_timestamp_key={4}, backfill_timestamp={5}, retry_count={6}'.format(
                                #         self.mod_input_instance_name,self.org_id, thread_id,signalflow_program, computation_id, self.backfill_timestamp_key, str(backfill_timestamp),str(retry_count)))
                                
                                if data_msg_count % self.detail_log_frequency == 0: 
                                    self.logger.info('status=running, action=stream_sim_flow_program_results, instance_name={0}, org_id={1}, thread_id={2}, signalflow_program="{3}", computation_id={4}, message_type={5}, metadata_msg_count={6}, data_msg_count={7}, mts_count={8}, other_msg_count={9}, data_msg_timestamp={10}, empty_data_msg_count={11}, retry_count={12}, mts_in_data_msg={13},mts_delay={14}'.format(
                                        self.mod_input_instance_name,self.org_id, thread_id,signalflow_program, computation_id, message_type, str(metadata_msg_count), str(data_msg_count), str(mts_count),str(other_msg_count),str(msg.logical_timestamp_ms),str(empty_data_msg_count),str(retry_count),str(mts_in_data_msg),str(mts_delay)))
                                else:
                                    self.logger.info('status=running, action=stream_sim_flow_program_results, instance_name={0}, org_id={1}, thread_id={2}, computation_id={3}, message_type={4}, metadata_msg_count={5}, data_msg_count={6}, mts_count={7}, other_msg_count={8}, data_msg_timestamp={9}, empty_data_msg_count={10},mts_in_data_msg={11},mts_delay={12}'.format(
                                        self.mod_input_instance_name,self.org_id, thread_id,computation_id, message_type, str(metadata_msg_count), str(data_msg_count), str(mts_count),str(other_msg_count),str(msg.logical_timestamp_ms),str(empty_data_msg_count),str(mts_in_data_msg),str(mts_delay)))
                        else:
                            other_msg_count+=1
                            if isinstance(msg, messages.JobStartMessage):
                                computation_id = msg.handle
                            
                            # Check for SIM Limit reached message 
                            if isinstance(msg, messages.InfoMessage) and msg.message and msg.message.get('messageCode',None) == self.SIM_FLOW_LIMIT_MSG_CODE:
                                self.logger.error('status=error, error_code=limit_reached, error_msg=SignalFlow Program reached metadata message limit of {6}., action=stream_sim_flow_program_results, instance_name={0}, org_id={1}, thread_id={2}, signalflow_program="{3}", computation_id={4}, message_type={5}, message={6}, metadata_msg_count={7}, data_msg_count={8}, mts_count={9}, other_msg_count={10}, retry_count={11}'.format(
                                                self.mod_input_instance_name,self.org_id, thread_id, signalflow_program,computation_id, message_type,json.dumps(msg.__dict__), str(metadata_msg_count), str(data_msg_count), str(mts_count),str(other_msg_count),str(retry_count)))
                            else:
                                self.logger.info('status=running, action=stream_sim_flow_program_results, instance_name={0}, org_id={1}, thread_id={2}, signalflow_program="{3}", computation_id={4}, message_type={5}, message={6}, metadata_msg_count={7}, data_msg_count={8}, mts_count={9}, other_msg_count={10}, retry_count={11}'.format(
                                                self.mod_input_instance_name,self.org_id, thread_id, signalflow_program,computation_id, message_type,json.dumps(msg.__dict__), str(metadata_msg_count), str(data_msg_count), str(mts_count),str(other_msg_count),str(retry_count)))
                                
                        if events:
                            self.writer.write_events(events)
                         
                    except Exception as e:
                        process_results_error_count+=1
                        self.logger.error('status=error, action=stream_sim_flow_program_results, instance_name={0}, org_id={1}, thread_id={2}, error_msg={3}, computation_id={4}, message_type={5}, metadata_msg_count={6}, data_msg_count={7}, mts_count={8}, other_msg_count={9}, retry_count={10}, process_results_error_count={11}'.format(
                                            self.mod_input_instance_name,self.org_id, thread_id, str(e), computation_id, message_type, str(metadata_msg_count), str(data_msg_count), str(mts_count),str(other_msg_count), str(retry_count), str(process_results_error_count)), exc_info=True)
                        if process_results_error_count >= self.sim_mod_input_retry_count:
                            break
                    
                self.logger.info('status=complete, action=stream_sim_flow_program_results, instance_name={0}, org_id={1}, thread_id={2}, computation_id={3}, metadata_msg_count={4}, data_msg_count={5}, mts_count={6}, other_msg_count={7}, retry_count={8}'.format(
                                                    self.mod_input_instance_name,self.org_id, thread_id,computation_id, str(metadata_msg_count), str(data_msg_count), str(mts_count),str(other_msg_count), str(retry_count)))
                # EXIT THE RETRY LOOP            
                break
    
            except Exception as e:
                self.logger.error('status=error, action=run_signalflow_program, instance_name={0}, org_id={1}, thread_id={2}, retry_count={3}, error_msg={4}'.format(self.mod_input_instance_name,self.org_id, thread_id, str(retry_count), str(e)), exc_info=True)
                retry_count+=1
                time.sleep(self.sim_mod_input_retry_wait_time * retry_count) #TODO: wait x sec. before retry.
                self.logger.info('status=retry, action=run_signalflow_program, thread_id={0}, org_id={1}, retry_count={2}'.format(thread_id,self.org_id,str(retry_count)))
        
        if sim_flow_client is not None:
                sim_flow_client.close()
                self.logger.info('status=complete, action=close_sim_flow_client, thread_id={0}, org_id={1}, retry_count={1}'.format(thread_id,self.org_id,str(retry_count)))
        # Need to stop the watchdog_bark function which is running in separate thread, else this run_signalflow_program function will not exit normally.
        self.break_watchdog = True 
        self.stop_mod_input_when_one_computation_fails=self.stop_mod_input_when_one_computation_fails_flag or self.stop_mod_input_when_one_computation_fails
        self.logger.info('status=complete, action=run_signalflow_program, thread_id={0}, org_id={1}, retry_count={1}'.format(thread_id,self.org_id,str(retry_count))) 

    '''
    This function is responsible for making any REST calls to the sim_modular_inputs collection
    '''
    def modularinput_collection_data(self, request_type, query_params=None, modinput_data=None):
        headers = {
                        'Authorization': f'Splunk {self.session_key}',
                        'Content-Type': 'application/json'
                    }
        host_url =self.SPLUNK_MODULARINPUT_COLLECTION.format(self.server_port)
        try:
            if request_type == 'GET':
                if query_params:
                    host_url = host_url + f'?query={json.dumps(query_params)}'
                response = requests.get(
                    host_url,
                    headers=headers,
                    verify=False
                    )
                return response
            elif request_type == 'DELETE':
                if query_params:
                    host_url = host_url + f'?query={json.dumps(query_params)}'
                response = requests.delete(
                    host_url,
                    headers=headers,
                    verify=False
                    )
            else:
                if query_params:
                    host_url = host_url + "/" + str(query_params)
                response = requests.post(
                                host_url,
                                json=modinput_data,
                                headers=headers,
                                verify=False
                                )
                return response
        except Exception as e:
                self.logger.error('status=error, action={0} error_msg={1}'.format(request_type, str(e)), exc_info=True)
    
    '''
    This function is responsible for making any  REST calls to Splunk Infrastructure Monitoring Data Streams page.
    '''
    def get_modular_input_data(self):
        try:
            headers = {
                            'Authorization': f'Splunk {self.session_key}',
                            'Content-Type': 'application/json'
                        }

            host_url = self.SPLUNK_MODULARINPUT_URL.format(self.server_port)
            self.logger.info(f'Getting all splunk modular inputs: {host_url}')
            response = requests.get(
                host_url,
                headers=headers,
                verify=False
                )
            return response
        except Exception as e:
                self.logger.error('status=error, Error while accessing modularinput page, error_msg={0}'.format(str(e)), exc_info=True)
        
    ################################################################################################################################# 
    # Common Functions ############################################################################################################## 
    ################################################################################################################################# 
    
    class LoggerContextFilter(logging.Filter):
        """
        This is a filter which injects command invocation instance UUID in the logs.
        """
        request_id = uuid.uuid4().hex
        def filter(self, record):
            record.request_id = self.request_id
            return True
    
    # This function does the cleanup of disabled and stale timestamps of modular inputs 
    # which are stored in collection - sim_modularinputs
    def cleanup_timestamps_of_stale_modinputs(self):
        self.logger.info('Starting the cleanup of stale modularinputs from sim_modularinputs collection')
        try:
            response = self.modularinput_collection_data(request_type="GET")
            if not json.loads(response.content):
                self.logger.info(f'There are no modular input timestamps to clear')
                return

            timestamp_modinput_set = set()
            for mod_input in response.json():
                timestamp_modinput_set.add(mod_input.get("title"))

            response = self.get_modular_input_data()

            # Below for loop will Remove all the active sim_modularinputs from the set timestamp_modinput_set
            for mod_input in response.json().get("entry"):
                if (mod_input.get("content").get("disabled") == False):
                    self.logger.info(f'Removing modular input: {mod_input.get("name")} from set')
                    modinput_name = mod_input.get("name")
                    if (modinput_name in timestamp_modinput_set):
                        timestamp_modinput_set.remove(modinput_name)
            
            if not timestamp_modinput_set:
                self.logger.info(f'There are no modular input timestamps to clear')
                return

            self.logger.info(f'Modular inputs to be deleted: {timestamp_modinput_set}')
            
            # Query to form for delete - query={"$or": [{"title":"MOD_INPUT1"},{"title":"MOD_INPUT2"}]}
            modinputs_to_delete=[]
            for mod in timestamp_modinput_set:
                query = {}
                query['title'] = mod
                modinputs_to_delete.append(query)
            final_query = {}
            final_query['$or'] = modinputs_to_delete
            self.modularinput_collection_data(request_type="DELETE", query_params=final_query)
            self.logger.info(f'Cleanup of modular inputs {timestamp_modinput_set} completed successfully.')
            
        except Exception as e:
            self.logger.error('status=error, action=cleanup_timestamps_of_stale_modinputs, error_msg={0}'.format(str(e)), exc_info=True)


    def get_event_writer(self):
        """This method returns event writer based on stack type.
        If the stack is Classic or on-prem, it returns an object of HECEventWriter.
        If the stack is Noah, it returns an object of NoahHECEventWriter.

        Returns:
            obj: Returns event writer object.
        """
        self._stack_info = stack_info.StackInfo(self.session_key)
        if self._stack_info.is_noah_stack:
            self.logger.debug(f'Detected Noah Stack. Creating NoahHECEventWriter.')
            hec_input_name = ":".join([self.app, self.hec_input_name])
            return noah_event_writer.NoahHECEventWriter(hec_input_name, self.session_key)
        self.logger.debug(f'Detected Non-Noah Stack. Creating HECEventWriter.')
        return self.event_writer


if __name__ == "__main__":
    worker = SIMModularInput()
    worker.execute()
