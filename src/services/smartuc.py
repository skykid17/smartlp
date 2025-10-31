"""
SmartUC (Use Case) service for SmartSOC.

This service provides business logic for:
- Sigma rule management and pagination
- MITRE ATT&CK Navigator data preparation  
- SIEM rule retrieval and content handling
- Search and filtering capabilities
- Rule configuration generation for different SIEMs
"""

import json
import math
import re
import time
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Tuple, Any, Optional

from bson import json_util, ObjectId

from .base import BaseService
from .settings import settings_service
from config.mitre import TACTIC_ORDER, TACTIC_DISPLAY_NAMES
from config.siem_constants import LEVEL_TO_NUMERIC_SPLUNK
from utils.pagination import generate_pagination_links, convert_dates_to_datetime





class SmartUCService(BaseService):
    """Service class for SmartUC operations."""
    
    def __init__(self):
        super().__init__('smartuc')
        # Collection names for different data types
        self.sigmarules_collection = 'sigma_rules'
        self.splunk_collection = 'splunk_rules' 
        self.elastic_collection = 'elastic_rules'
        self.mitre_collection = 'mitre_techniques'
    
    def get_rules_with_pagination(
        self,
        page: int = 1, 
        per_page: int = 10, 
        search_query: Optional[str] = None,
        main_type_filter: str = 'all',
        sub_type_filter: str = 'all'
    ) -> Dict[str, Any]:
        """Get rules with pagination and filters.
        
        Args:
            page: Current page number
            per_page: Number of rules per page
            search_query: Search query string
            main_type_filter: Main type filter
            sub_type_filter: Sub type filter
            
        Returns:
            Dict containing rules and pagination info
        """
        try:
            # Build query filters
            query = {}
            
            # Search filter
            if search_query:
                query['$or'] = [
                    {'title': {'$regex': search_query, '$options': 'i'}},
                    {'description': {'$regex': search_query, '$options': 'i'}},
                    {'tags': {'$regex': search_query, '$options': 'i'}}
                ]
            
            # Main type filter
            if main_type_filter != 'all':
                query['logsource.category'] = main_type_filter
            
            # Sub type filter
            if sub_type_filter != 'all':
                query['logsource.product'] = sub_type_filter
            
            # Get total count
            total_rules = self.db.count_documents(self.sigmarules_collection, query)
            
            # Calculate pagination
            total_pages = math.ceil(total_rules / per_page) if total_rules > 0 else 1
            skip = (page - 1) * per_page
            
            # Get rules
            rules = self.db.query(
                self.sigmarules_collection, 
                query, 
                limit=per_page, 
                skip=skip,
                sort=[('_id', -1)]
            )
            
            # Get unique main and sub types for filters
            main_types = self.db.get_distinct_values(self.sigmarules_collection, 'logsource.category')
            sub_types = self.db.get_distinct_values(self.sigmarules_collection, 'logsource.product')
            
            # Generate pagination links
            max_display_pages = 5
            start_page = max(1, page - max_display_pages // 2)
            end_page = min(total_pages, start_page + max_display_pages - 1)
            page_links = list(range(start_page, end_page + 1))
            
            return {
                'rules': rules,
                'total_rules': total_rules,
                'page': page,
                'total_pages': total_pages,
                'per_page': per_page,
                'search_query': search_query,
                'main_types': sorted([t for t in main_types if t]),
                'sub_types': sorted([t for t in sub_types if t]),
                'selected_main_type': main_type_filter,
                'selected_sub_type': sub_type_filter,
                'page_links': page_links,
                'activeSiem': "elastic"
            }
            
        except Exception as e:
            self.log_error(f"Error in get_rules_with_pagination: {str(e)}", e)
            return {
                'rules': [],
                'total_rules': 0,
                'page': 1,
                'total_pages': 0,
                'per_page': per_page,
                'search_query': search_query,
                'main_types': [],
                'sub_types': [],
                'selected_main_type': main_type_filter,
                'selected_sub_type': sub_type_filter,
                'page_links': [],
                'activeSiem': 'elastic'
            }
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a single rule by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            Rule data or None if not found
        """
        try:
            # Try to find by ObjectId first
            try:
                query = {'_id': ObjectId(rule_id)}
            except:
                # If not ObjectId, try as string ID
                query = {'id': rule_id}
            
            rule = self.db.query(self.sigmarules_collection, query, limit=1)
            return rule if rule else None
            
        except Exception as e:
            self.log_error(f"Error in get_rule_by_id: {str(e)}", e)
            return None
    
    def get_attack_navigator_data(self) -> Dict[str, Any]:
        """Get data for ATT&CK Navigator.
        
        Returns:
            Dict containing techniques grouped by tactic
        """
        try:
            # Get MITRE techniques from database
            techniques = self.db.query(self.mitre_collection, {})
            
            # Group techniques by tactic
            techniques_by_tactic = defaultdict(list)
            tactic_names = {}
            
            for technique in techniques:
                mitre_id = technique.get('mitre_id', '')
                if not mitre_id:
                    continue
                    
                # Get tactics for this technique
                tactics = technique.get('tactics', [])
                if not tactics:
                    continue
                
                for tactic in tactics:
                    # Normalize tactic name to match expected format
                    tactic_id = tactic.lower().replace(' ', '-').replace('_', '-')
                    
                    # Store tactic name
                    tactic_names[tactic_id] = tactic.replace('-', ' ').replace('_', ' ').title()
                    
                    # Add technique to tactic
                    techniques_by_tactic[tactic_id].append({
                        'id': mitre_id,
                        'mitre_id': mitre_id,
                        'name': technique.get('name', ''),
                        'description': technique.get('description', ''),
                        'is_subtechnique': technique.get('is_subtechnique', '.' in mitre_id if mitre_id else False)
                    })
            
            # Define tactic order based on MITRE ATT&CK framework
            tactic_order = [
                'initial-access', 'execution', 'persistence', 'privilege-escalation',
                'defense-evasion', 'credential-access', 'discovery', 'lateral-movement',
                'collection', 'command-and-control', 'exfiltration', 'impact'
            ]
            
            # Filter tactic_order to only include tactics that have techniques
            available_tactics = [tactic for tactic in tactic_order if tactic in techniques_by_tactic]
            
            return {
                'tactic_order': available_tactics,
                'tactic_names': tactic_names,
                'techniques_by_tactic': dict(techniques_by_tactic)
            }
            
        except Exception as e:
            self.log_error(f"Error in get_attack_navigator_data: {str(e)}", e)
            return {
                'tactic_order': [],
                'tactic_names': {},
                'techniques_by_tactic': {}
            }
    
    def get_siem_rule(self, collection: str, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get SIEM rule from specific collection.
        
        Args:
            collection: Collection name (e.g., 'splunk_rules', 'elastic_rules')
            rule_id: Sigma rule ID
            
        Returns:
            SIEM rule data or None if not found
        """
        try:
            # Try different possible field names for sigma rule ID
            queries = [
                {'sigma_id': rule_id},
                {'rule_id': rule_id},
                {'id': rule_id},
                {'sigma_rule_id': rule_id}
            ]
            
            for query in queries:
                rule = self.db.query(collection, query, limit=1)
                if rule:
                    return rule
            
            return None
            
        except Exception as e:
            self.log_error(f"Error in get_siem_rule: {str(e)}", e)
            return None



    
    def get_sigma_rules(
        self, 
        page: int = 1, 
        per_page: int = 20, 
        search_query: Optional[str] = None, 
        main_type_filter: Optional[str] = None, 
        sub_type_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Fetches Sigma rules from MongoDB with pagination, search, and type filters.
        
        Args:
            page: Page number
            per_page: Rules per page
            search_query: Search query string
            main_type_filter: Main type filter
            sub_type_filter: Sub type filter
            
        Returns:
            Tuple of (rules_list, total_count)
        """
        try:
            skip = (page - 1) * per_page
            query = {}
            
            # Apply search filter (if any)
            if search_query:
                try:
                    query['original_content'] = {'$regex': search_query, '$options': 'imx'}
                except Exception as e:
                    self.log_warning(f"Regex search failed: {e}")
                    # Continue with other filters
            
            # Apply rule type filters
            if main_type_filter and main_type_filter != "all":
                if sub_type_filter and sub_type_filter != "all":
                    # Exact match for main_type/sub_type
                    query['rule_type'] = f"{main_type_filter}/{sub_type_filter}"
                else:
                    # Regex match for main_type followed by optional /sub_type or end of string
                    query['rule_type'] = {'$regex': f'^{re.escape(main_type_filter)}(/.*)?$'}
            
            # Count documents matching the final query
            total_rules = self.db.count_documents(self.sigmarules_collection, query)
            
            # Fetch the rules matching the final query with pagination
            if per_page == 1:
                rules = [self.db.query(self.sigmarules_collection, query, skip=skip, limit=per_page)]
            else:
                rules = list(self.db.query(self.sigmarules_collection, query, skip=skip, limit=per_page))
            
            return rules, total_rules
            
        except Exception as e:
            self.log_error(f"Error fetching/counting rules: {str(e)}", e)
            return [], 0
    
    def get_distinct_rule_types(self) -> Tuple[List[str], List[str]]:
        """Gets distinct main and sub rule types from the database.
        
        Returns:
            Tuple of (main_types, sub_types)
        """
        main_types = set()
        sub_types = set()
        
        try:
            # Find all distinct non-null/non-empty rule_type values
            distinct_types = self.db.get_distinct_values(self.sigmarules_collection, 'rule_type')
            
            for rt in distinct_types:
                if rt and isinstance(rt, str):  # Check if not None/empty and is a string
                    parts = rt.split('/', 1)
                    main_types.add(parts[0])
                    if len(parts) > 1 and parts[1]:  # Check if sub-type exists and is not empty
                        sub_types.add(parts[1])
                        
        except Exception as e:
            self.log_error(f"Error fetching distinct rule types: {str(e)}", e)
        
        return sorted(list(main_types)), sorted(list(sub_types))
    
    def build_navigator_json(self, techniques: List[Dict[str, Any]]) -> str:
        """Constructs the ATT&CK Navigator JSON from the technique data.
        
        Args:
            techniques: List of technique data
            
        Returns:
            JSON string for ATT&CK Navigator
        """
        try:
            navigator_data = {
                "name": "Custom Navigator Layer",
                "versions": {
                    "attack": "14",
                    "navigator": "4.9.5",
                    "layer": "4.5"
                },
                "domain": "enterprise-attack",
                "description": "Custom Navigator layer based on stored techniques",
                "filters": {"platforms": ["Windows", "Linux", "macOS"]},
                "sorting": 0,
                "layout": {
                    "layout": "side", 
                    "aggregateFunction": "average", 
                    "showID": False, 
                    "showName": True, 
                    "showAggregateScores": False, 
                    "countUnscored": False, 
                    "expandedSubtechniques": "none"
                },
                "hideDisabled": False,
                "techniques": [],
                "gradient": {"colors": ["#ffffff", "#ff6666"], "minValue": 0, "maxValue": 1},
                "legendItems": [{"label": "Has Rule", "color": "#ff6666"}],
                "metadata": [],
                "showTacticRowBackground": False,
                "tacticRowBackground": "#dddddd",
                "selectTechniquesAcrossTactics": True,
                "selectSubtechniquesWithParent": False,
                "selectVisibleTechniques": False
            }
            
            for technique in techniques:
                if 'mitre_attack' in technique:
                    navigator_data["techniques"].append({
                        "techniqueID": technique['mitre_attack'],
                        "score": 1,
                        "color": "#ff6666",
                        "comment": f"Rule available: {technique.get('technique_name', 'N/A')}",
                        "enabled": True
                    })
                else:
                    self.log_warning(f"Skipping technique due to missing 'mitre_attack' field: {technique.get('_id')}")
            
            return json.dumps(navigator_data)
            
        except Exception as e:
            self.log_error(f"Error building navigator JSON: {str(e)}", e)
            return json.dumps({"error": "Failed to build navigator data"})
    

    
    def create_rule_config(self, entry_ids: List[str]) -> str:
        """Function to support log ingestion from different SIEMs.
        
        Args:
            entry_ids: List of entry IDs
            
        Returns:
            Configuration string for the active SIEM
        """
        try:
            # Get active SIEM from settings
            settings = settings_service.get_all_settings()
            active_siem = settings.get('activeSiem', 'elastic')
            
            if active_siem == "splunk":
                return self.create_splunk_rule_config(entry_ids)
            elif active_siem == "elastic":
                return self.create_elastic_rule_config(entry_ids)
            else:
                self.log_error(f"Unsupported SIEM type: {active_siem}")
                return "# Unsupported SIEM type"
                
        except Exception as e:
            self.log_error(f"Error creating rule config: {str(e)}", e)
            return "# Error creating rule configuration"
    
    def create_splunk_rule_config(self, sigma_ids: List[str]) -> str:
        """Creates Splunk savedsearches.conf configuration from sigma rules.
        
        Args:
            sigma_ids: List of sigma rule IDs
            
        Returns:
            Splunk configuration string
        """
        try:
            self.log_info(f"Starting create_splunk_rule_config with sigma_ids: {sigma_ids}")
            
            savedsearches = []
            for sigma_id in sigma_ids:
                self.log_info(f"Processing sigma_id: {sigma_id}")
                
                # Get splunk and sigma documents
                splunk_document = self.db.query(self.splunk_collection, {"sigma_id": sigma_id}, limit=1)
                sigma_document = self.db.query(self.sigmarules_collection, {"id": sigma_id}, limit=1)
                
                if not splunk_document:
                    self.log_warning(f"No splunk_document found for sigma_id {sigma_id}")
                    continue
                
                title = sigma_document.get("title") if sigma_document else f"Rule {sigma_id}"
                level = sigma_document.get("level", "medium") if sigma_document else "medium"
                description = sigma_document.get("description", "No description") if sigma_document else "No description"
                rule = splunk_document.get("rule")
                cron_schedule = splunk_document.get("cron_schedule")
                earliest_time = splunk_document.get("dispatch_earliest_time")
                latest_time = splunk_document.get("dispatch_latest_time")
                deployed = splunk_document.get("deployed", False)
                
                # Skip if missing required fields
                if not rule:
                    self.log_warning(f"Skipping sigma_id {sigma_id} due to missing rule")
                    continue
                if not cron_schedule:
                    self.log_warning(f"Skipping sigma_id {sigma_id} due to missing cron_schedule")
                    continue
                if not earliest_time or not latest_time:
                    self.log_warning(f"Skipping sigma_id {sigma_id} due to missing earliest/latest time")
                    continue
                
                # Optional: skip if already deployed
                if deployed:
                    self.log_info(f"Skipping already deployed rule for sigma_id {sigma_id}")
                    continue
                
                # Normalize search name and stanza
                stanza = f"[{title}]"
                
                savedsearch_block = f"""{stanza}
alert.severity = {LEVEL_TO_NUMERIC_SPLUNK.get(level, 3)}
alert.track = 1
counttype = number of events
cron_schedule = {cron_schedule}
description = {description}
dispatch.earliest_time = {earliest_time}
dispatch.latest_time = {latest_time}
enableSched = 1
quantity = 0
relation = greater than
search = {rule}
"""
                self.log_info(f"Generated savedsearch block for {sigma_id}")
                savedsearches.append(savedsearch_block.strip())
            
            if not savedsearches:
                self.log_warning("No valid savedsearches found. Returning empty config.")
                return "# No valid savedsearches found."
            
            # Assemble the configuration file
            configuration = ["### savedsearches.conf", "\n\n".join(savedsearches)]
            return "\n".join(configuration)
            
        except Exception as e:
            self.log_error(f"Error creating Splunk rule config: {str(e)}", e)
            return "# Error creating Splunk configuration"
    
    def create_elastic_rule_config(self, sigma_ids: List[str]) -> str:
        """Creates Elasticsearch detection rules configuration from sigma rules.
        
        Args:
            sigma_ids: List of sigma rule IDs
            
        Returns:
            JSON configuration string for Elasticsearch
        """
        try:
            self.log_info(f"Starting create_elastic_rule_config with sigma_ids: {sigma_ids}")
            
            rules = []
            for sigma_id in sigma_ids:
                self.log_info(f"Processing sigma_id: {sigma_id}")
                
                # Get elastic and sigma documents
                elastic_document = self.db.query(self.elastic_collection, {"sigma_id": sigma_id}, limit=1)
                sigma_document = self.db.query(self.sigmarules_collection, {"id": sigma_id}, limit=1)
                
                if not elastic_document:
                    self.log_warning(f"No elastic_document found for sigma_id {sigma_id}")
                    continue
                
                title = sigma_document.get("title", f"Untitled Rule {sigma_id}") if sigma_document else f"Untitled Rule {sigma_id}"
                rule = elastic_document.get("rule")
                index = elastic_document.get("index", "logs-*")
                interval = elastic_document.get("interval", "5m")
                earliest_time = elastic_document.get("dispatch_earliest_time", "now-15m")
                latest_time = elastic_document.get("dispatch_latest_time", "now")
                severity = sigma_document.get("level", "medium") if sigma_document else "medium"
                risk_score = elastic_document.get("risk_score", 50)
                description = sigma_document.get("description", "No description provided.") if sigma_document else "No description provided."
                deployed = elastic_document.get("deployed", False)
                
                if not rule:
                    self.log_warning(f"Skipping sigma_id {sigma_id} due to missing rule")
                    continue
                
                if deployed:
                    self.log_info(f"Skipping already deployed rule for sigma_id {sigma_id}")
                    continue
                
                rule_config = {
                    "name": title,
                    "description": description,
                    "risk_score": risk_score,
                    "severity": severity,
                    "type": "query",
                    "query": rule,
                    "index": index,
                    "interval": interval,
                    "from": earliest_time,
                    "to": latest_time,
                    "language": "kuery",
                    "enabled": True,
                    "rule_id": sigma_id,
                    "tags": ["auto-generated", "from-sigma"],
                    "actions": [],
                    "throttle": "no_actions",
                    "exceptions_list": []
                }
                
                self.log_info(f"Generated rule config for {sigma_id}")
                rules.append(rule_config)
            
            if not rules:
                self.log_warning("No valid rules found. Returning empty config.")
                return "[]"
            
            # Return pretty-printed multiline JSON
            return json.dumps(rules, indent=2)
            
        except Exception as e:
            self.log_error(f"Error creating Elastic rule config: {str(e)}", e)
            return "[]"
    
    def get_config_data_by_ids(self, siem: str, ids: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Retrieve configuration data for specified rule IDs from the appropriate SIEM collection.
        
        Args:
            siem: The SIEM type ('splunk' or 'elastic')
            ids: List of rule IDs from the sigmarules collection
            
        Returns:
            List of rule configuration data with appropriate fields for the SIEM
        """
        try:
            self.log_info(f"get_config_data_by_ids called with siem={siem}, ids={ids}")
            
            # First, get the sigma rules to find their sigma_id values
            sigma_rules = list(self.db.query(
                self.sigmarules_collection,
                {'id': {'$in': ids}},
                projection={'id': 1, 'title': 1}
            ))
            
            if not sigma_rules:
                self.log_warning("No matching sigma rules found")
                return None
            
            # Extract the sigma IDs (which should be the same as the rule IDs for mapping)
            sigma_ids = [rule['id'] for rule in sigma_rules]
            sigma_titles = {rule['id']: rule.get('title', 'Untitled Rule') for rule in sigma_rules}
            
            # Choose the appropriate collection based on SIEM type
            if siem == 'splunk':
                collection = self.splunk_collection
                projection = {
                    'sigma_id': 1,
                    'title': 1,
                    'cron_schedule': 1,
                    'dispatch_earliest_time': 1,
                    'dispatch_latest_time': 1,
                    'deployed': 1
                }
            elif siem == 'elastic':
                collection = self.elastic_collection
                projection = {
                    'sigma_id': 1,
                    'title': 1,
                    'interval': 1,
                    'dispatch_earliest_time': 1,
                    'dispatch_latest_time': 1,
                    'risk_score': 1,
                    'deployed': 1
                }
            else:
                return None
            
            # Query the SIEM collection using sigma_id field
            query = {'sigma_id': {'$in': sigma_ids}}
            rules = list(self.db.query(collection, query, projection=projection))
            
            # Convert to format expected by frontend
            config_data = []
            for rule in rules:
                sigma_id = rule.get('sigma_id')
                data = {
                    'id': sigma_id,
                    'title': rule.get('title') or sigma_titles.get(sigma_id, 'Untitled Rule')
                }
                
                if siem == 'splunk':
                    data.update({
                        'cron_schedule': rule.get('cron_schedule', ''),
                        'dispatch_earliest_time': rule.get('dispatch_earliest_time', ''),
                        'dispatch_latest_time': rule.get('dispatch_latest_time', ''),
                        'deployed': rule.get('deployed', '')
                    })
                elif siem == 'elastic':
                    data.update({
                        'interval': rule.get('interval', ''),
                        'dispatch_earliest_time': rule.get('dispatch_earliest_time', ''),
                        'dispatch_latest_time': rule.get('dispatch_latest_time', ''),
                        'risk_score': rule.get('risk_score', ''),
                        'deployed': rule.get('deployed', '')
                    })
                
                config_data.append(data)
            
            # Also add entries for sigma rules that don't have corresponding SIEM rules yet
            existing_sigma_ids = {rule.get('sigma_id') for rule in rules}
            for sigma_id in sigma_ids:
                if sigma_id not in existing_sigma_ids:
                    self.log_info(f"Adding missing SIEM rule for sigma_id: {sigma_id}")
                    data = {
                        'id': sigma_id,
                        'title': sigma_titles.get(sigma_id, 'Untitled Rule')
                    }
                    
                    if siem == 'splunk':
                        data.update({
                            'cron_schedule': '',
                            'dispatch_earliest_time': '',
                            'dispatch_latest_time': '',
                            'deployed': False
                        })
                    elif siem == 'elastic':
                        data.update({
                            'interval': '',
                            'dispatch_earliest_time': '',
                            'dispatch_latest_time': '',
                            'risk_score': '',
                            'deployed': False
                        })
                    
                    config_data.append(data)
            
            return config_data
            
        except Exception as e:
            self.log_error(f"Error in get_config_data_by_ids: {str(e)}", e)
            return []


# Create service instance
smartuc_service = SmartUCService()