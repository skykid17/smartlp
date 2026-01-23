"""
SIEM connection services for SmartSOC application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pcre2
from collections import defaultdict
import requests

from .base import BaseService

from elasticsearch import Elasticsearch
import splunklib.client as splunk_client
import splunklib.results as splunk_results

from config.environment import env_manager
from database.connection import db_connection

class SIEMConnectionError(Exception):
    """Exception for SIEM connection errors."""
    pass


class BaseSIEMService(BaseService, ABC):
    """Abstract base class for SIEM services."""
    
    def __init__(self, service_name: str):
        """Initialize SIEM service and reuse base service logging/db plumbing.
        
        This makes SIEM services behave like other application services and
        avoids mixing in the stdlib logging module directly.
        """
        super().__init__(service_name)
        self._connection = None
    
    @abstractmethod
    def connect(self, config_override: Optional[Dict[str, Any]] = None) -> bool:
        """Establish connection to SIEM.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connection(self, config_override: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Test SIEM connection.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            Tuple of (success, message, details)
        """
        pass
    
    @abstractmethod
    def search(self, index: str, query: str, max_results: int = 100, config_override: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict], Optional[str]]:
        """Execute search query.
        
        Args:
            query: Search query
            index: Index/sourcetype to search
            max_results: Maximum number of results
            config_override: Optional configuration to use instead of self.settings
            
        Returns:
            Tuple of (results, error_message)
        """
        pass
    
    def disconnect(self) -> None:
        """Disconnect from SIEM."""
        if self._connection:
            try:
                if hasattr(self._connection, 'close'):
                    self._connection.close()
                self._connection = None
                self.logger.info("Disconnected from %s", self.service_name)
            except Exception as e:
                self.logger.error("Error disconnecting from %s: %s", self.service_name, e)


class SplunkService(BaseSIEMService):
    """Splunk SIEM service."""
    
    def __init__(self):
        """Initialize Splunk service."""
        super().__init__("splunk")
        self.settings = env_manager.splunk
    
    def connect(self, config_override: Optional[Dict[str, Any]] = None) -> bool:
        """Connect to Splunk.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if config_override:
                port = config_override.get("port")
                # Handle port conversion carefully
                if port is None:
                    port = "8089"  # Default Splunk port
                elif not isinstance(port, str):
                    port = str(port)
                
                self._connection = splunk_client.connect(
                    host=config_override.get("host"),
                    port=port,
                    username=config_override.get("user"),
                    password=config_override.get("password")
                )
            else:
                self._connection = splunk_client.connect(
                    host=self.settings.host,
                    port=self.settings.port,
                    username=self.settings.username,
                    password=self.settings.password
                )
            self.logger.info("Successfully connected to Splunk")
            return True
        except Exception as e:
            self.logger.error("Failed to connect to Splunk: %s", e)
            self._connection = None
            return False
    
    def test_connection(self, config_override: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Test Splunk connection.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            Tuple of (success, message, details)
        """
        import time
        
        try:
            # If config_override is provided, create a temporary connection
            if config_override:
                port = config_override.get("port")
                # Handle port conversion carefully
                if port is None:
                    port = "8089"  # Default Splunk port
                elif not isinstance(port, str):
                    port = str(port)
                
                conn = splunk_client.connect(
                    host=config_override.get("host"),
                    port=port,
                    username=config_override.get("user"),
                    password=config_override.get("password")
                )
                info = conn.info()
            else:
                if not self._connection:
                    if not self.connect():
                        return False, "Failed to connect to Splunk", {}
                conn = self._connection
                info = conn.info()
            
            version = info.get("version")
            build = info.get("build")
            
            # If config_override includes query validation parameters, test the query
            if config_override:
                search_index = config_override.get("search_index", "").strip()
                search_query = config_override.get("search_query", "").strip()
                search_entry_count = config_override.get("search_entry_count", 10)
                
                if search_index and search_query:
                    try:
                        # Convert search_entry_count to int, default to 10 if invalid
                        entry_count = int(search_entry_count) if search_entry_count else 10
                    except (ValueError, TypeError):
                        entry_count = 10
                    
                    try:
                        # Construct search query
                        search_string = f"search index={search_index} {search_query} | head {entry_count}"
                        
                        # Execute search
                        job = conn.jobs.create(search_string)
                        
                        # Wait for search to complete with timeout protection
                        max_wait_time = 30  # seconds
                        poll_interval = 0.1
                        start_time = time.time()
                        
                        while not job.is_done():
                            if time.time() - start_time >= max_wait_time:
                                job.cancel()
                                return False, "Query validation timed out after 30 seconds", {}
                            time.sleep(poll_interval)
                        
                        # Get result count efficiently without iterating through all results
                        result_count = int(job["resultCount"])
                        
                        return True, "Connected and query executed successfully", {
                            "version": version,
                            "build": build,
                            "result_count": result_count,
                        }
                    except Exception as query_error:
                        return False, f"Query validation failed: {str(query_error)}", {}
            
            return True, "Connected to Splunk", {"version": version, "build": build}
            
        except Exception as e:
            self.logger.error("Splunk connection test failed: %s", e)
            return False, f"Splunk connection failed: {str(e)}", {}
    
    def search(self, index: str, query: str, max_results: int = 100, config_override: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict], Optional[str]]:
        """Execute Splunk search.
        
        Args:
            query: Splunk search query
            index: Splunk index to search
            max_results: Maximum number of results
            config_override: Optional configuration to use instead of self.settings
            
        Returns:
            Tuple of (results, error_message)
        """
        # If config_override is provided, create a temporary connection
        if config_override:
            try:
                port = config_override.get("port")
                # Handle port conversion carefully
                if port is None:
                    port = "8089"  # Default Splunk port
                elif not isinstance(port, str):
                    port = str(port)
                
                conn = splunk_client.connect(
                    host=config_override.get("host"),
                    port=port,
                    username=config_override.get("user"),
                    password=config_override.get("password")
                )
            except Exception as e:
                error_msg = f"Failed to connect to Splunk with override config: {e}"
                self.logger.error("%s", error_msg)
                return [], error_msg
        else:
            if not self._connection and not self.connect():
                return [], "Failed to connect to Splunk"
            conn = self._connection
        
        try:
            # Construct search query
            search_query = f"search index={index} {query} | head {max_results}"
            
            # Execute search
            job = conn.jobs.create(search_query)
            
            # Wait for search to complete
            while not job.is_done():
                pass
            
            # Get results
            results = []
            for result in splunk_results.ResultsReader(job.results()):
                if isinstance(result, dict):
                    results.append(result)
            
            self.logger.info("Splunk search returned %s results", len(results))
            return results, None
            
        except Exception as e:
            error_msg = f"Splunk search failed: {e}"
            self.logger.error("%s", error_msg)
            return [], error_msg
    
    def get_indexes(self) -> List[str]:
        """Get list of available Splunk indexes.
        
        Returns:
            List of index names
        """
        if not self._connection and not self.connect():
            return []
        
        try:
            indexes = []
            for index in self._connection.indexes:
                indexes.append(index.name)
            return indexes
        except Exception as e:
            self.logger.error("Failed to get Splunk indexes: %s", e)
            return []
        
    def get_splunk_settings(self) -> Dict[str, Any]:
        """Get Splunk settings from database."""
        return db_connection.query("settings", {"category": "siem_settings", "id": "splunk"},)[0]

    def create_config_splunk(self, entry_ids: List[str]) -> Dict[str, str]:
        """Create Splunk configuration for SmartLP entries.
        
        Args:
            entry_ids: List of entry IDs
            
        Returns:
            Dictionary containing 'props_conf' and 'transforms_conf' strings
        """
        try:
            self.logger.info("Creating Splunk config for %s entries", len(entry_ids))
            
            # Get entries from database
            entries = []
            for entry_id in entry_ids:
                entry = db_connection.query(
                    self.collection_name,
                    {"id": entry_id},
                    projection={"_id": 0},
                    limit=1
                )
                if entry:
                    entries.append(entry)
                else:
                    self.logger.warning("Entry not found: %s", entry_id)
            
            if not entries:
                self.logger.warning("No valid entries found for config generation")
                return {
                    "props_conf": "# No valid entries found", 
                    "transforms_conf": "# No valid entries found"
                }
            
            # Prepare configuration components
            sh_props_conf = defaultdict(list)
            sh_transforms_conf = []
            hf_transforms_conf = []
            hf_index_routes = []
            hf_sourcetype_routes = []
            
            for entry in entries:
                source_type = entry.get("source_type", "<source_type>")
                log_type = entry.get("logtype", "<log_type>")
                entry_id = entry.get("id", "<entries.id>")
                regex = entry.get("regex", "<entries.regex>")
                index = entry.get("index", "<index>")
                
                transform_name = f"{log_type}_{entry_id}"
                route_index = f"{log_type}_route_index_{entry_id}"
                route_sourcetype = f"{log_type}_route_sourcetype_{entry_id}"
                
                # SH props.conf grouping
                sh_props_conf[source_type].append(transform_name)
                
                # SH transforms.conf
                sh_transforms_conf.append(f"\n[{transform_name}]\nREGEX = {regex}")
                
                # HF props.conf route names
                hf_index_routes.append(route_index)
                hf_sourcetype_routes.append(route_sourcetype)
                
                # HF transforms.conf
                hf_transforms_conf.extend([
                    f"\n[{route_index}]\nREGEX = {regex}\nDEST_KEY = _MetaData:Index\nFORMAT = {index}",
                    f"\n[{route_sourcetype}]\nREGEX = {regex}\nDEST_KEY = MetaData:Sourcetype\nFORMAT = sourcetype::{source_type}"
                ])
            
            # --- Build props.conf content ---
            props_blocks = []
            
            # SH props.conf
            props_blocks.append("### SH props.conf")
            for source_type, transforms in sh_props_conf.items():
                props_blocks.append(f"\n[{source_type}]\nREPORT-smartsoc = {', '.join(transforms)}")
            
            # HF props.conf
            props_blocks.append("\n### HF props.conf")
            props_blocks.append("\n[catchall]")
            props_blocks.append(f"TRANSFORMS-catchallindex = {', '.join(hf_index_routes)}")
            props_blocks.append(f"TRANSFORMS-catchallsourcetype = {', '.join(hf_sourcetype_routes)}")
            
            # --- Build transforms.conf content ---
            transforms_blocks = []
            
            # SH transforms.conf
            transforms_blocks.append("### SH transforms.conf")
            transforms_blocks.extend(sh_transforms_conf)
            
            # HF transforms.conf
            transforms_blocks.append("\n### HF transforms.conf")
            transforms_blocks.extend(hf_transforms_conf)
            
            self.logger.info("Generated Splunk config dict with %s entries", len(entries))
            
            return {
                "props_conf": "\n".join(props_blocks),
                "transforms_conf": "\n".join(transforms_blocks)
            }
            
        except Exception as e:
            self.logger.exception("Error creating Splunk config")
            error_msg = f"# Error creating Splunk configuration: {str(e)}"
            return {
                "props_conf": error_msg,
                "transforms_conf": error_msg
            }
    

    def deploy_config_splunk(self, entry_ids: List[str]) -> Tuple[bool, str]:
        """Deploy SmartLP configuration to Splunk by writing to props.conf and transforms.conf.
        
        Args:
            entry_ids: List of entry IDs to deploy
        """
        pass
    
    def create_rule_splunk(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detection rule in Splunk.
        
        Args:
            rule: Rule dictionary
        Returns:

            Created rule response
        """
        pass

    def deploy_rule_splunk(self, rule: Dict[str, Any]) -> Tuple[bool, str]:
        """Deploy a detection rule to Splunk.
        
        Args:
            rule: Rule dictionary
            
        Returns:
            Tuple of (success, message)
        """
        pass

class ElasticsearchService(BaseSIEMService):
    """Elasticsearch SIEM service."""
    
    def __init__(self):
        """Initialize Elasticsearch service."""
        super().__init__("elasticsearch")
        self.settings = env_manager.elastic
        self.ssl_verified = False  # Track whether SSL verification is being used
    
    def _build_auth_kwargs(self, config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build authentication kwargs for Elasticsearch connection.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            Dictionary with authentication parameters
        """
        if config_override:
            api_key = (config_override.get('api_key', '') or '').strip()
            if api_key:
                return {"api_key": api_key}
            
            username = (config_override.get('user', '') or '').strip()
            password = config_override.get('password', '') or ''
            if username and password:
                return {"basic_auth": (username, password)}
            return {}
        else:
            api_key = (getattr(self.settings, 'api_key', '') or '').strip()
            if api_key:
                return {"api_key": api_key}

            username = (getattr(self.settings, 'username', '') or '').strip()
            password = getattr(self.settings, 'password', '') or ''
            if username and password:
                return {"basic_auth": (username, password)}
            return {}
    
    def connect(self, config_override: Optional[Dict[str, Any]] = None) -> bool:
        """Connect to Elasticsearch.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # First try with certificate verification
            if config_override:
                host = config_override.get("host")
                cert_path = (config_override.get("cert_path", '') or '').strip()
            else:
                host = self.settings.host
                cert_path = (getattr(self.settings, 'cert_path', '') or '').strip()
            
            auth_kwargs = self._build_auth_kwargs(config_override)

            if cert_path:
                self._connection = Elasticsearch(
                    host,
                    ca_certs=cert_path,
                    verify_certs=True,
                    **auth_kwargs,
                )
            else:
                # No cert configured; treat this as "no verification" path.
                raise ValueError("No cert_path configured")
            
            # Test connection
            if self._connection.ping():
                self.ssl_verified = True
                self.logger.info(
                    "Successfully connected to Elasticsearch with certificate verification"
                )
                return True
            else:
                self.logger.warning(
                    "Elasticsearch ping failed with certificate verification"
                )
                
        except Exception as e:
            self.logger.warning("Certificate verification failed: %s", e)
            
        # If certificate verification fails, try without it (for self-signed certificates)
        try:
            self.logger.info("Attempting connection without certificate verification")
            if config_override:
                host = config_override.get("host")
            else:
                host = self.settings.host
            
            auth_kwargs = self._build_auth_kwargs(config_override)
            self._connection = Elasticsearch(
                host,
                verify_certs=False,
                **auth_kwargs,
            )
            
            # Test connection
            if self._connection.ping():
                self.ssl_verified = False
                self.logger.info(
                    "Successfully connected to Elasticsearch without certificate verification"
                )
                return True
            else:
                self.logger.error(
                    "Elasticsearch ping failed even without certificate verification"
                )
                return False
                
        except Exception as e:
            self.logger.error("Failed to connect to Elasticsearch: %s", e)
            self._connection = None
            self.ssl_verified = False
            return False
    
    def test_connection(self, config_override: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Test Elasticsearch connection.
        
        Args:
            config_override: Optional configuration to use instead of self.settings
        
        Returns:
            Tuple of (success, message, details)
        """
        import json
        
        try:
            # If config_override is provided, create a temporary connection
            if config_override:
                # Use relaxed validation - allow connection attempt without strict requirements
                # This matches the behavior of the connect() method
                host = config_override.get("host")
                cert_path = (config_override.get("cert_path") or "").strip()
                auth_kwargs = self._build_auth_kwargs(config_override)
                
                # Try with certificate first if provided
                es = None
                if cert_path:
                    try:
                        es_kwargs: Dict[str, Any] = {
                            "request_timeout": 10,
                            "verify_certs": True,
                            "ca_certs": cert_path,
                        }
                        es_kwargs.update(auth_kwargs)
                        es = Elasticsearch(host, **es_kwargs)
                        if not es.ping():
                            es = None
                    except Exception:
                        es = None
                
                # Fall back to no verification if cert didn't work
                if es is None:
                    try:
                        es_kwargs: Dict[str, Any] = {
                            "request_timeout": 10,
                            "verify_certs": False,
                        }
                        es_kwargs.update(auth_kwargs)
                        es = Elasticsearch(host, **es_kwargs)
                        if not es.ping():
                            return False, "Failed to connect to Elasticsearch", {}
                    except Exception as e:
                        return False, f"Elasticsearch connection failed: {str(e)}", {}
                
                info = es.info()
                cluster_name = info.get("cluster_name")
                version = (info.get("version") or {}).get("number")
                
                # If config_override includes query validation parameters, test the query
                search_index = config_override.get("search_index", "").strip()
                search_query = config_override.get("search_query", "").strip()
                
                if search_index and search_query:
                    # Parse query if it's a string
                    try:
                        query_dict = json.loads(search_query)
                        # Extract just the query portion
                        query_body = query_dict.get("query", {"match_all": {}})
                    except json.JSONDecodeError:
                        # Treat as simple query string
                        query_body = {
                            "query_string": {
                                "query": search_query
                            }
                        }
                    
                    # Use count API for accurate result counting without retrieving documents
                    try:
                        count_response = es.count(index=search_index, query=query_body)
                        result_count = count_response.get("count", 0)
                        
                        return True, "Connected and query executed successfully", {
                            "cluster_name": cluster_name,
                            "version": version,
                            "result_count": result_count,
                        }
                    except Exception as query_error:
                        return False, f"Query validation failed: {str(query_error)}", {}
                
                return True, "Connected to Elasticsearch", {
                    "cluster_name": cluster_name,
                    "version": version,
                }
            else:
                if not self._connection:
                    if not self.connect():
                        return False, "Failed to connect to Elasticsearch", {}
                
                if self._connection.ping():
                    info = self._connection.info()
                    return True, "Connected to Elasticsearch", {
                        "cluster_name": info.get("cluster_name"),
                        "version": (info.get("version") or {}).get("number"),
                    }
                else:
                    return False, "Elasticsearch ping failed", {}
            
        except Exception as e:
            self.logger.error("Elasticsearch connection test failed: %s", e)
            return False, f"Elasticsearch connection failed: {str(e)}", {}
    
    def search(self, index: str, query: str, max_results: int = 100, config_override: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict], Optional[str]]:
        """Execute Elasticsearch search.
        
        Args:
            query: Elasticsearch query (JSON string or dict)
            index: Elasticsearch index pattern
            max_results: Maximum number of results
            config_override: Optional configuration to use instead of self.settings
            
        Returns:
            Tuple of (results, error_message)
        """
        # If config_override is provided, create a temporary connection
        if config_override:
            try:
                cert_path = (config_override.get("cert_path", '') or '').strip()
                auth_kwargs = self._build_auth_kwargs(config_override)
                
                if cert_path:
                    conn = Elasticsearch(
                        config_override.get("host"),
                        ca_certs=cert_path,
                        verify_certs=True,
                        **auth_kwargs,
                    )
                else:
                    conn = Elasticsearch(
                        config_override.get("host"),
                        verify_certs=False,
                        **auth_kwargs,
                    )
            except Exception as e:
                error_msg = f"Failed to connect to Elasticsearch with override config: {e}"
                self.logger.error("%s", error_msg)
                return [], error_msg
        else:
            if not self._connection and not self.connect():
                return [], "Failed to connect to Elasticsearch"
            conn = self._connection
        
        try:
            # Parse query if it's a string
            if isinstance(query, str):
                import json
                try:
                    query_dict = json.loads(query)
                except json.JSONDecodeError:
                    # Treat as simple query string
                    query_dict = {
                        "query": {
                            "query_string": {
                                "query": query
                            }
                        }
                    }
            else:
                query_dict = query
            
            # Add size limit
            query_dict["size"] = max_results
            
            # Execute search
            self.logger.debug(f"Executing ES search: index={index} body={query_dict}")
            response = conn.search(
                index=index,
                body=query_dict
            )
            
            # Extract results
            results = []
            # Defensive handling of response structure
            try:
                hits_container = response.get('hits', {})
                hit_items = hits_container.get('hits', []) if isinstance(hits_container, dict) else []
                for hit in hit_items:
                    result = hit.get('_source', {})
                    result.update({
                        '_index': hit.get('_index'),
                        '_id': hit.get('_id'),
                        '_score': hit.get('_score')
                    })
                    results.append(result)
            except Exception as e:
                self.logger.error("Failed to parse ES response hits: %s", e)

            # If no results, log raw response for debugging
            if not results:
                self.logger.debug(f"Elasticsearch empty result. Raw response: {response}")

            self.logger.info("Elasticsearch search returned %s results", len(results))
            return results, None
            
        except Exception as e:
            error_msg = f"Elasticsearch search failed: {e}"
            self.logger.error("%s", error_msg)
            return [], error_msg
    
    def get_indices(self) -> List[str]:
        """Get list of available Elasticsearch indices.
        
        Returns:
            List of index names
        """
        if not self._connection and not self.connect():
            return []
        
        try:
            indices_info = self._connection.cat.indices(format='json')
            return [idx['index'] for idx in indices_info]
        except Exception as e:
            self.logger.error("Failed to get Elasticsearch indices: %s", e)
            return []
        
    def get_elastic_settings(self) -> Dict[str, Any]:
        """Get Elasticsearch settings from database."""
        return db_connection.query("settings", {"category": "siem_settings", "id": "elastic"},)[0]
    
    def create_config_elastic(self, entry_ids: List[str]) -> str:
        """Create Elasticsearch Logstash configuration for SmartLP entries."""
        try:
            self.logger.info("Creating Elastic config for %s entries", len(entry_ids))
            
            # Fetch selected entries
            selected_entries = db_connection.query(
                collection_name="logs",
                # `entry_ids` are SmartLP's user-facing IDs (field `id`), not Mongo `_id`.
                filter_dict={"id": {"$in": entry_ids}},
            )

            # Fetch deployed entries
            deployed_entries = db_connection.query(
                collection_name="logs",
                filter_dict={"status": "Deployed"},
            )

            # Merge + dedupe (by _id)
            # Convert to list immediately so we can index it [0] and [1:]
            all_entries = list({
                str(e.get("id") or e.get("_id")): e
                for e in (selected_entries + deployed_entries)
            }.values())

            if not all_entries:
                self.logger.warning("No valid entries found for config generation")
                return "No valid entries found"

            # Build Logstash pipeline
            pipeline = []
            
            # 1. Input section
            pipeline.append(r'''input {
    tcp {
        port => 1701
        codec => multiline {
        pattern => "^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\s(.*?)\s[A-Z]+|^<Event xmlns|^\S{3}\s+\d+\s\d{2}:\d{2}:\d{2}|^<\d+>\S{3}\s+\d+\s\d{2}:\d{2}:\d{2}|^<\d+>\d\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d+\s\w+\s\w+:\d+"
        negate => true
        what => "previous"
        }
    }
    }''')
            
            # 2. Filter section
            pipeline.append("\nfilter {")
            
            # Add first grok pattern
            first_entry = all_entries[0]
            regex_config = self._format_regex_for_logstash(first_entry.get('regex', ''))
            source_type = first_entry.get('source_type', 'unknown')
            
            pipeline.append(f'''
    grok {{
        match => {{ "message" => {regex_config} }}
        add_field => {{ "source_type" => "{source_type}" }}
    }}''')
            
            # Add additional grok patterns for subsequent entries
            for entry in all_entries[1:]:
                regex_config = self._format_regex_for_logstash(entry.get('regex', ''))
                source_type = entry.get('source_type', 'unknown')
                
                pipeline.append(f'''
    if "_grokparsefailure" in [tags] {{
        grok {{
        match => {{ "message" => {regex_config} }}
        add_field => {{ "source_type" => "{source_type}" }}
        remove_tag => ["_grokparsefailure"]
        }}
    }}''')
            
            pipeline.append("\n}")
            
            # 3. Output section
            elastic_settings = self.get_elastic_settings()
            elastic_host = elastic_settings.get("host")
            elastic_user = elastic_settings.get("user")
            elastic_password = elastic_settings.get("password")

            # 2. Build the dynamic output section
            pipeline.append(f'''
output {{
    stdout {{ codec => rubydebug }}

    if "_grokparsefailure" not in [tags] {{
        elasticsearch {{
        hosts => ["{elastic_host}"]
        ssl_enabled => true
        ssl_certificate_authorities => "/etc/logstash/certs/cyberlab-rca-ica-chain.cer"
        user => "{elastic_user}"
        password => "{elastic_password}"
        data_stream => true
        data_stream_type => "logs"
        data_stream_dataset => "parsed"
        data_stream_namespace => "default"
        }}
    }} else {{
        elasticsearch {{
        hosts => ["{elastic_host}"]
        ssl_enabled => true
        ssl_certificate_authorities => "/etc/logstash/certs/cyberlab-rca-ica-chain.cer"
        user => "{elastic_user}"
        password => "{elastic_password}"
        data_stream => true
        data_stream_type => "logs"
        data_stream_dataset => "unparsed"
        data_stream_namespace => "default"
        }}
    }}
}}''')
            
            config = "".join(pipeline)
            self.logger.info("Generated Elastic config with %s entries", len(all_entries))
            return config

        except Exception as e:
            self.logger.exception("Error generating Elastic config")
            return f"# Error: {str(e)}"
    
    def _format_regex_for_logstash(self, regex: str) -> str:
        """Format regex pattern for Logstash configuration.
        
        Args:
            regex: The regex pattern to format
            
        Returns:
            Properly formatted regex for Logstash
        """
        if not regex:
            return '".*"'
        
        # If regex contains double quotes, wrap in single quotes
        if '"' in regex:
            return f"'{regex}'"
        else:
            return f'"{regex}"'

    def _normalize_regex_for_ingest(self, regex: str) -> str:
        """
        Convert Logstash/PCRE-style regex into Elasticsearch ingest-compatible regex.
        """
        if not regex:
            return regex

        # Convert (?P<name>...) → (?<name>...)
        regex = pcre2.sub(r"\(\?P<([^>]+)>", r"(?<\1>", regex)

        return regex
    
    def deploy_config_elastic(self, pipeline_config: str) -> tuple[bool, str]:
        """Deploy a Logstash pipeline to Elasticsearch (Centralized Pipeline Management)."""

        try:
            elastic_settings = self.get_elastic_settings()
            elastic_host = elastic_settings.get("host")
            elastic_api_key = elastic_settings.get("api_key")
            elastic_user = elastic_settings.get("user") or "smartlp"
            pipeline_id = elastic_settings.get("pipeline_id") or "smartlp"

            if not elastic_host:
                return False, "Elasticsearch host not configured"
            if not elastic_api_key:
                return False, "Elasticsearch API key not configured"
            if not pipeline_config or pipeline_config.startswith("#"):
                return False, "Invalid or empty Logstash pipeline config"

            pipeline_body = {
                "description": "SmartLP generated Logstash pipeline",
                "last_modified": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z",
                "pipeline_metadata": {
                    "type": "logstash_pipeline",
                    "version": 1
                },
                "username": elastic_user,
                "pipeline": pipeline_config,
                "pipeline_settings": {
                    "pipeline.workers": 1,
                    "pipeline.batch.size": 125,
                    "pipeline.batch.delay": 50,
                    "queue.type": "memory"
                }
            }

            es = Elasticsearch(
                hosts=[elastic_host],
                headers={"Authorization": f"ApiKey {elastic_api_key}"},
                verify_certs=False
            )

            response = es.logstash.put_pipeline(
                id=pipeline_id,
                body=pipeline_body
            )

            # CPM returns None on success
            if response is None:
                return True, f"SmartLP pipeline '{pipeline_id}' deployed successfully"
            
            # Some ES versions may return an ack dict
            if isinstance(response, dict) and response.get("acknowledged") is True:
                return True, f"SmartLP pipeline '{pipeline_id}' deployed successfully"
            
            # Safety Net
            return True, f"SmartLP pipeline '{pipeline_id}' deployed successfully"

        except Exception as e:
            self.logger.exception("Elasticsearch deployment failed")
            return False, f"Failed to deploy Logstash pipeline: {e}"

    def create_rule_elastic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detection rule in Elasticsearch."""
        siem_rule = db_connection.query('knowledge_base', {'sigma_id': data.get('id'),'metadata.category': 'elastic_rules'}, projection={'_id': 0}, limit =1)
        sigma_rule = db_connection.query('knowledge_base', {'id': data.get('id'),'metadata.category': 'sigma_rules'}, projection={'_id': 0}, limit =1)
        elastic_rule = {
            'rule_id': siem_rule.get('id', data.get('id')),
            'entry_id': data.get('entry_id'),
            'name': siem_rule.get('title'),
            'description': sigma_rule.get('description'),
            'severity': data.get('severity', 'medium'),
            'risk_score': data.get('risk_score', 50),
            'from': f"{data.get('dispatch_latest_time', 'now')}{data.get('dispatch_earliest_time', '-15m')}",
            'interval': data.get('interval', "5m"),
            'deployed': True,
            'type': "esql",
            'language': "esql",
            'enabled': True,
            'query': "FROM logs-parsed* \n| " + siem_rule.get('rule'),
            'tags': sigma_rule.get('tags', []),
        }
        return elastic_rule

    def deploy_rule_elastic(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy detection rule to Elasticsearch."""
        try:

            elastic_settings = self.get_elastic_settings()
            kibana_url = elastic_settings.get("kibana_url")
            api_key = elastic_settings.get("api_key")
            HEADERS = {
                "kbn-xsrf": "true",
                "Authorization": f"ApiKey {api_key}",
                "Content-Type": "application/json"
            }

            url = f"{kibana_url}/api/detection_engine/rules"
            resp = requests.post(url, headers=HEADERS, json=rule, verify=False)
            
            # If rule already exists, use PUT _update
            if resp.status_code == 409:  # Conflict = already exists
                update_url = f"{kibana_url}/api/detection_engine/rules/_update"
                resp = requests.put(update_url, headers=HEADERS, json=rule, verify=False)
            
            # Update database records to mark rule as deployed
            db_connection.update_one("knowledge_base", {"sigma_id": rule.get("rule_id"), "metadata.category": "elastic_rules"}, {"$set": {"deployed": True}})
            db_connection.update_one("logs", {"id": rule.get("entry_id"), "detection_rules.sigma_id": rule.get("rule_id")}, {"$set": {"detection_rules.$.deployed": True}})
            
            return {"success": True, "message": f"Rule deployed successfully", "response": resp.json()}
        
        except Exception as e:
            error_msg = f"Failed to deploy rule to Elasticsearch: {e}"
            self.logger.error("%s", error_msg)
            return {"success": False, "message": error_msg}

class SIEMServiceFactory:
    """Factory for creating SIEM service instances."""
    
    _services = {
        'splunk': SplunkService,
        'elastic': ElasticsearchService,
        'elasticsearch': ElasticsearchService,
    }
    
    @classmethod
    def create_service(cls, siem_type: str) -> Optional[BaseSIEMService]:
        """Create SIEM service instance.
        
        Args:
            siem_type: Type of SIEM ('splunk', 'elastic', 'elasticsearch')
            
        Returns:
            SIEM service instance or None if type not supported
        """
        service_class = cls._services.get(siem_type.lower())
        if service_class:
            return service_class()
        return None
    
    @classmethod
    def get_service(cls, siem_type: str) -> Optional[BaseSIEMService]:
        """Get SIEM service instance (alias for create_service for backward compatibility).
        
        Args:
            siem_type: Type of SIEM ('splunk', 'elastic')
            
        Returns:
            SIEM service instance or None if type not supported
        """
        return cls.create_service(siem_type)
    
    @classmethod
    def get_supported_siems(cls) -> List[str]:
        """Get list of supported SIEM types.
        
        Returns:
            List of supported SIEM type names
        """
        return list(cls._services.keys())

# Global SIEM service instances
splunk_service = SplunkService()
elasticsearch_service = ElasticsearchService()