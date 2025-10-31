"""
SmartLP (Log Parser) service for SmartSOC application.

This service handles:
- Log entry management and CRUD operations
- Background log ingestion processes
- Parsing and regex matching functionality
- Report generation and statistics
"""

import threading
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .base import BaseService, CRUDService
from models.core import LogEntry, RuleStatus, PrefixEntry
from .siem import SIEMServiceFactory
from .settings import settings_service

# Import for Elasticsearch deployment
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False


class SmartLPService(CRUDService):
    """Service for SmartLP log parsing functionality."""
    
    def __init__(self):
        """Initialize SmartLP service."""
        super().__init__("smartlp", "parser_entries")
        self._prefix_collection = "prefix_entries"
        self._ingestion_thread: Optional[threading.Thread] = None
        self._stop_ingestion = threading.Event()
        self._ingestion_running = False
    
    def start_log_ingestion(self) -> None:
        """Start background log ingestion."""
        if self._ingestion_running:
            self.log_warning("Log ingestion already running")
            return
        
        self._stop_ingestion.clear()
        self._ingestion_thread = threading.Thread(target=self.ingestion_loop, daemon=True)
        self._ingestion_thread.start()
        self._ingestion_running = True
        self.log_info("[INGESTION] Background log ingestion started")
    
    def stop_log_ingestion(self) -> None:
        """Stop background log ingestion."""
        if not self._ingestion_running:
            return
        
        self._stop_ingestion.set()
        if self._ingestion_thread and self._ingestion_thread.is_alive():
            self._ingestion_thread.join(timeout=5)
        
        self._ingestion_running = False
        self.log_info("[INGESTION] Background log ingestion stopped")
    
    def ingestion_loop(self) -> None:
        """Main ingestion loop running in background thread."""
        while not self._stop_ingestion.wait(timeout=30):  # Check every 30 seconds
            try:
                self.perform_ingestion()
            except Exception as e:
                self.log_error("[INGESTION] Error during log ingestion", e)
    
    def perform_ingestion(self) -> None:
        """Perform a single ingestion cycle."""
        try:
            # Get settings for ingestion configuration
            from services.settings import settings_service
            settings = settings_service.get_global_settings()
            self.log_info("[INGESTION] Checking ingestion settings...")
            
            if not settings.get('ingestOn', False):
                self.log_info("[INGESTION] Log ingestion is disabled in settings")
                return
            
            # Get ingestion parameters
            active_siem = settings.get('activeSiem', 'elastic')
            ingest_frequency = int(settings.get('ingestFrequency', 30))
            similarity_check = settings.get('similarityCheck', False)
            similarity_threshold = float(settings.get('similarityThreshold', 0.8))
            fix_count = int(settings.get('fixCount', 3))
            
            self.log_info(f"[INGESTION] Starting ingestion cycle for SIEM: {active_siem}")
            
            # Get SIEM-specific search configuration
            siem_settings = settings_service.get_siem_settings()
            siem_config = next((s for s in siem_settings if s['id'] == active_siem), None)
            
            if not siem_config:
                self.log_error(f"[INGESTION] No configuration found for SIEM: {active_siem}")
                return
            
            # Perform log ingestion
            self.log_info(f"[INGESTION] Connecting to {active_siem} SIEM...")
            logs, error = self.ingest_from_siem(
                active_siem, 
                siem_config.get('search_query', ''),
                siem_config.get('search_index', ''),
                siem_config.get('search_entry_count', 10)
            )
            
            if error:
                self.log_error(f"[INGESTION] SIEM ingestion failed: {error}")
                return
            
            if not logs:
                self.log_info(f"[INGESTION] No new logs retrieved from {active_siem}")
                return
            
            # Process each ingested log
            processed_count = 0
            for log_entry in logs:
                try:
                    # Check for similarity if enabled
                    if similarity_check and self.check_log_similarity(log_entry, similarity_threshold):
                        self.log_info(f"[INGESTION] Skipped similar log: {log_entry[:50]}...")
                        continue
                    
                    # Generate regex for the log
                    regex = self.generate_regex_for_log(log_entry, fix_count)
                    
                    # Determine log type and source type
                    log_type, source_type = self.determine_log_type(log_entry)
                    
                    # Create log entry in database
                    entry_data = {
                        'log': log_entry,
                        'regex': regex,
                        'status': 'Matched' if regex else 'Unmatched',
                        'log_type': log_type,
                        'source_type': source_type,
                        'timestamp': datetime.now().isoformat(),
                        'ingestion_method': 'automatic'
                    }
                    
                    entry_id = self.create(entry_data)
                    if entry_id:
                        processed_count += 1
                        self.log_info(f"[INGESTION] Processed log entry: {entry_id}")
                    
                except Exception as e:
                    self.log_error(f"[INGESTION] Failed to process log entry: {str(e)}", e)
                    continue
            
            self.log_info(f"[INGESTION] Cycle completed: {processed_count} logs processed from {active_siem}")
            
        except Exception as e:
            self.log_error(f"[INGESTION] Error during ingestion cycle: {str(e)}", e)
    
    def get_entries(self, page: int = 1, per_page: int = 15, 
                   search_filters: Optional[Dict[str, str]] = None) -> Tuple[List[Dict], int]:
        """Get log entries with pagination and filtering.
        
        Args:
            page: Page number
            per_page: Entries per page
            search_filters: Optional search filters
            
        Returns:
            Tuple of (entries, total_count)
        """
        try:
            # Build filter query
            filter_query = {}
            if search_filters:
                if search_filters.get('search_id'):
                    search_id = search_filters['search_id']
                    # Check if search_id contains commas (multiple IDs for config panel)
                    if ',' in search_id:
                        # Split comma-separated IDs and use exact matching
                        ids = [id.strip() for id in search_id.split(',') if id.strip()]
                        filter_query['id'] = {'$in': ids}
                    else:
                        # Single ID - use regex for partial matching
                        filter_query['id'] = {'$regex': search_id, '$options': 'i'}
                if search_filters.get('search_log'):
                    filter_query['log'] = {'$regex': search_filters['search_log'], '$options': 'i'}
                if search_filters.get('search_regex'):
                    filter_query['regex'] = {'$regex': search_filters['search_regex'], '$options': 'i'}
                if search_filters.get('filter_status'):
                    filter_query['status'] = search_filters['filter_status']
            
            # Get paginated results
            entries, total = self.get_paginated(
                page=page,
                per_page=per_page,
                filter_dict=filter_query,
                sort=[("timestamp", -1)],
                projection={"_id": 0}
            )
            
            self.log_info(f"Retrieved {len(entries)} entries (page {page}, {per_page} per page)")
            return entries, total
            
        except Exception as e:
            self.log_error("Failed to get entries", e)
            return [], 0
    
    def get_oldest_unmatched_entry(self) -> Optional[Dict[str, Any]]:
        """Get oldest unmatched entry from the database.
        
        Retrieves the oldest log entry that has 'Unmatched' status,
        ordered by timestamp in ascending order.
        
        Returns:
            Dictionary containing entry data (id, log, regex) or None if not found
        """
        try:
            self.log_info("Searching for oldest unmatched entry")
            
            entry = self.db.query(
                self.collection_name,
                {"status": RuleStatus.UNMATCHED.value},
                projection={"_id": 0, "id": 1, "log": 1, "regex": 1, "timestamp": 1},
                sort=[("timestamp", 1)],  # Ascending order (oldest first)
                limit=1
            )
            
            if entry:
                self.log_info(f"Found oldest unmatched entry: {entry.get('id', 'unknown')}")
                return entry
            else:
                self.log_info("No unmatched entries found in database")
                return None
                
        except Exception as e:
            self.log_error(f"Failed to get oldest unmatched entry: {str(e)}", e)
            return None

    def get_unmatched_entries_count(self) -> int:
        """Get total count of unmatched entries.
        
        Returns:
            Number of unmatched entries in database
        """
        try:
            count = self.db.count_documents(
                self.collection_name,
                {"status": RuleStatus.UNMATCHED.value}
            )
            self.log_info(f"Found {count} unmatched entries in database")
            return count
        except Exception as e:
            self.log_error(f"Failed to count unmatched entries: {str(e)}", e)
            return 0

    def get_all_statuses(self) -> List[str]:
        """Get all unique statuses.
        
        Returns:
            List of unique status values
        """
        try:
            statuses = self.db.get_distinct_values(self.collection_name, "status")
            self.log_info(f"Retrieved {len(statuses)} unique statuses: {statuses}")
            return statuses
        except Exception as e:
            self.log_error(f"Failed to get all statuses: {str(e)}", e)
            return []
    
    def get_entry_status(self, ids: List[str]) -> Dict[str, str]:
        """Fetch statuses of the given entry IDs.
        
        Args:
            ids: List of entry IDs to get statuses for
            
        Returns:
            Dictionary mapping entry ID to status
        """
        try:
            if not ids:
                return {}
            
            # Query entries with specified IDs
            query = {"id": {"$in": ids}}
            entries = self.db.query(
                self.collection_name,
                query,
                projection={"_id": 0, "id": 1, "status": 1}
            )
            
            # Convert to dictionary mapping id -> status
            status_map = {}
            for entry in entries:
                status_map[entry['id']] = entry.get('status', 'Unknown')
            
            self.log_info(f"Retrieved statuses for {len(status_map)} entries")
            return status_map
            
        except Exception as e:
            self.log_error(f"Failed to get entry statuses: {str(e)}", e)
            return {}

    def get_report_data(self) -> Dict[str, Any]:
        """Generate report data for SmartLP report.
        
        Returns:
            Dictionary containing report statistics compatible with frontend
        """
        try:
            self.log_info("Generating SmartLP report data")
            
            # Get all entries
            all_entries = self.db.query(self.collection_name, {})
            
            # Initialize counters
            parsed_count = 0
            unparsed_count = 0
            logtype_stats = {}
            
            # Process entries
            for entry in all_entries:
                status = entry.get('status', 'Unmatched')
                log_type = entry.get('logtype', 'Unknown')
                
                # Count parsed vs unparsed
                if status == 'Matched':
                    parsed_count += 1
                else:
                    unparsed_count += 1
                    
                    # Count unparsed by logtype for top 5
                    if log_type not in logtype_stats:
                        logtype_stats[log_type] = 0
                    logtype_stats[log_type] += 1
            
            # Get top 5 unparsed logtypes
            sorted_logtypes = sorted(logtype_stats.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Format for frontend compatibility
            report_data = {
                'parsed': parsed_count,
                'unparsed': unparsed_count,
                'logtypes': sorted_logtypes,  # Array of [logtype, count] pairs
                'total': parsed_count + unparsed_count,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.log_info(f"Report generated successfully: {parsed_count} parsed, {unparsed_count} unparsed entries")
            return report_data
            
        except Exception as e:
            self.log_error(f"Failed to generate report data: {str(e)}", e)
            return {
                'parsed': 0,
                'unparsed': 0,
                'logtypes': [],
                'total': 0,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e)
            }

    # Prefix Management Methods
    def get_prefixes(self) -> List[Dict[str, Any]]:
        """Get all prefix entries from database.
        
        Returns:
            List of prefix entries
        """
        try:
            self.log_info("Retrieving all prefix entries")
            
            prefixes = self.db.query(
                self._prefix_collection,
                {},
                projection={"_id": 0},
                sort=[("created_at", -1)]
            )
            
            self.log_info(f"Retrieved {len(prefixes)} prefix entries")
            return prefixes
            
        except Exception as e:
            self.log_error(f"Failed to get prefixes: {str(e)}", e)
            return []

    def add_prefix(self, regex: str, description: Optional[str] = None) -> Optional[str]:
        """Add a new prefix entry.
        
        Args:
            regex: The prefix regex pattern
            description: Optional description
            
        Returns:
            ID of created prefix or None if failed
        """
        try:
            import uuid
            from datetime import datetime
            
            prefix_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            prefix_data = {
                "id": prefix_id,
                "regex": regex,
                "description": description,
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            self.log_info(f"Adding new prefix entry: {prefix_id}")
            
            # Insert into database
            result = self.db.insert_one(self._prefix_collection, prefix_data)
            
            if result:
                self.log_info(f"Successfully added prefix entry: {prefix_id}")
                return prefix_id
            else:
                self.log_error("Failed to insert prefix entry")
                return None
                
        except Exception as e:
            self.log_error(f"Failed to add prefix: {str(e)}", e)
            return None

    def delete_prefix(self, prefix_id: str) -> bool:
        """Delete a prefix entry by ID.
        
        Args:
            prefix_id: ID of prefix to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.log_info(f"Deleting prefix entry: {prefix_id}")
            
            result = self.db.delete_one(self._prefix_collection, {"id": prefix_id})
            
            if result:
                self.log_info(f"Successfully deleted prefix entry: {prefix_id}")
                return True
            else:
                self.log_warning(f"Prefix entry not found: {prefix_id}")
                return False
                
        except Exception as e:
            self.log_error(f"Failed to delete prefix {prefix_id}: {str(e)}", e)
            return False

    def update_prefix(self, prefix_id: str, regex: str, description: Optional[str] = None) -> bool:
        """Update an existing prefix entry.
        
        Args:
            prefix_id: ID of prefix to update
            regex: New regex pattern
            description: New description
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            from datetime import datetime
            
            self.log_info(f"Updating prefix entry: {prefix_id}")
            
            update_data = {
                "regex": regex,
                "description": description,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.db.update_one(
                self._prefix_collection,
                {"id": prefix_id},
                {"$set": update_data}
            )
            
            if result:
                self.log_info(f"Successfully updated prefix entry: {prefix_id}")
                return True
            else:
                self.log_warning(f"Prefix entry not found for update: {prefix_id}")
                return False
                
        except Exception as e:
            self.log_error(f"Failed to update prefix {prefix_id}: {str(e)}", e)
            return False

    def get_prefix_count(self) -> int:
        """Get total count of prefix entries.
        
        Returns:
            Number of prefix entries
        """
        try:
            count = self.db.count_documents(self._prefix_collection, {})
            self.log_info(f"Found {count} prefix entries")
            return count
        except Exception as e:
            self.log_error(f"Failed to count prefixes: {str(e)}", e)
            return 0

    def test_llm_model(self, task: str, model: str, url: str, llm_endpoint: str) -> Tuple[Optional[str], Optional[str]]:
        """Test LLM model connectivity and functionality.
        
        Args:
            task: Task type (e.g., 'test')
            model: Model name to test
            url: LLM endpoint URL
            llm_endpoint: LLM endpoint identifier
            
        Returns:
            Tuple of (response, error) - one will be None
        """
        try:
            self.log_info(f"Testing LLM model: {model} at {url}")
            
            # Use the new LLM service for testing
            from .llm import llm_service
            
            # Test the connection with the specific URL and model
            result = llm_service.test_connection(url=url, model=model)
            
            if result['success']:
                response = result['response']
                self.log_info(f"LLM model test successful: {model}")
                return response, None
            else:
                error_msg = result['error']
                self.log_error(f"LLM model test failed: {error_msg}")
                return None, error_msg
                
        except Exception as e:
            error_msg = f"LLM model test failed: {str(e)}"
            self.log_error(error_msg, e)
            return None, error_msg

    def test_siem_query(self, siem_type: str, search_query: str, search_index: str, entries_count: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Test SIEM query connectivity and functionality.
        
        Args:
            siem_type: Type of SIEM (e.g., 'elastic', 'splunk')
            search_query: Query string to test
            search_index: Index/sourcetype to search
            entries_count: Number of entries to retrieve
            
        Returns:
            Tuple of (response, error) - one will be None
        """
        try:
            self.log_info(f"Testing SIEM query: {siem_type}")
            
            # Get SIEM service
            siem_service = SIEMServiceFactory.get_service(siem_type)
            if not siem_service:
                error = f"Unsupported SIEM type: {siem_type}"
                self.log_error(error)
                return None, error
            
            # Test the query
            try:
                # Convert entries_count to int
                limit = int(entries_count) if entries_count else 10
                
                # Execute test query
                results, error = siem_service.search(
                    query=search_query,
                    index=search_index,
                    max_results=limit
                )
                
                if error:
                    error_msg = f"SIEM query failed: {error}"
                    self.log_error(error_msg)
                    return None, error_msg
                
                if results:
                    response = {
                        "status": "success",
                        "count": len(results),
                        "sample": results[:3]  # Return first 3 results as sample
                    }
                    self.log_info(f"SIEM query test successful: {len(results)} results")
                    return response, None
                else:
                    error = "Query returned no results"
                    self.log_warning(f"SIEM query test: {error}")
                    return None, error
                    
            except ValueError as e:
                error = f"Invalid entries count: {entries_count}"
                self.log_error(error)
                return None, error
                
        except Exception as e:
            error_msg = f"SIEM query test failed: {str(e)}"
            self.log_error(error_msg, e)
            return None, error_msg

    def ingest_from_siem(self, siem_type: str, search_query: str, search_index: str, entry_count: int) -> Tuple[Optional[List[str]], Optional[str]]:
        """Ingest logs from the specified SIEM.
        
        Args:
            siem_type: Type of SIEM (elastic, splunk)
            search_query: Query to execute
            search_index: Index/sourcetype to search
            entry_count: Number of entries to retrieve
            
        Returns:
            Tuple of (logs_list, error_message)
        """
        try:
            siem_service = SIEMServiceFactory.get_service(siem_type)
            if not siem_service:
                return None, f"Unsupported SIEM type: {siem_type}"
            
            # Execute search query
            results, error = siem_service.search(
                query=search_query,
                index=search_index,
                max_results=entry_count
            )
            
            if error:
                return None, error
            
            if not results:
                return [], None
            
            # Extract raw log messages from results
            logs = []
            for result in results:
                # Try to extract the raw log message
                raw_log = (
                    result.get('_source', {}).get('message', '') or
                    result.get('message', '') or
                    result.get('_raw', '') or
                    str(result)
                )
                if raw_log and raw_log.strip():
                    logs.append(raw_log.strip())
            
            self.log_info(f"[INGESTION] Retrieved {len(logs)} logs from {siem_type}")
            return logs, None
            
        except Exception as e:
            error_msg = f"[INGESTION] Failed to ingest from {siem_type}: {str(e)}"
            self.log_error(error_msg, e)
            return None, error_msg

    def check_log_similarity(self, log_entry: str, threshold: float) -> bool:
        """Check if a log entry is similar to existing entries.
        
        Args:
            log_entry: The log entry to check
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if similar log found, False otherwise
        """
        try:
            from difflib import SequenceMatcher
            
            # Get recent log entries for comparison
            recent_entries = self.db.query(
                self.collection_name,
                {},
                projection={"log": 1},
                sort=[("timestamp", -1)],
                limit=100  # Check against last 100 entries
            )
            
            # Mask the log entry for comparison
            masked_log = self.mask_log_entry(log_entry)
            
            for entry in recent_entries:
                existing_log = entry.get('log', '')
                masked_existing = self.mask_log_entry(existing_log)
                
                # Calculate similarity ratio
                similarity = SequenceMatcher(None, masked_log, masked_existing).ratio()
                
                if similarity >= threshold:
                    self.log_info(f"Found similar log with similarity: {similarity:.2f}")
                    return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error checking log similarity: {str(e)}", e)
            return False

    def mask_log_entry(self, log: str) -> str:
        """Mask IP addresses in log entries for similarity comparison.
        
        Args:
            log: The log entry to mask
            
        Returns:
            Masked log entry
        """
        import re
        
        # Mask IP addresses
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        masked = re.sub(ip_pattern, '1.1.1.1', log)
        
        # Mask timestamps (common patterns)
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',   # US format
            r'\w{3} \d{1,2} \d{2}:\d{2}:\d{2}',       # Syslog format
        ]
        
        for pattern in timestamp_patterns:
            masked = re.sub(pattern, 'TIMESTAMP', masked)
        
        return masked

    def generate_regex_for_log(self, log_entry: str, fix_count: int) -> str:
        """Generate regex pattern for a log entry.
        
        Args:
            log_entry: The log entry to generate regex for
            fix_count: Number of fix iterations to perform
            
        Returns:
            Generated regex pattern
        """
        try:
            # Import the LLM service (now available)
            from .llm import llm_service
            
            # Use the LLM service to generate regex
            response = llm_service.generate_regex(log_entry, fix_count)
            
            if response and response.get('success'):
                regex = response.get('regex', '')
                self.log_info(f"Generated regex for log: {regex[:100]}...")
                return self.resolve_duplicate_capture_groups(regex)
            else:
                self.log_warning(f"Failed to generate regex: {response.get('error', 'Unknown error')}")
                
                # Fallback to simple pattern-based approach
                return self.generate_fallback_regex(log_entry)
                
        except Exception as e:
            self.log_error(f"Error generating regex: {str(e)}", e)
            # Fallback to simple pattern-based approach
            return self.generate_fallback_regex(log_entry)
    
    def generate_fallback_regex(self, log_entry: str) -> str:
        """Generate a simple fallback regex when LLM is not available.
        
        Args:
            log_entry: The log entry to generate regex for
            
        Returns:
            Simple regex pattern
        """
        import re
        
        # Very simple approach: just escape the entire log
        regex = re.escape(log_entry)
        
        # Ensure regex ends with $
        if not regex.endswith("$"):
            regex += "$"
            
        return regex
    
    def generate_regex_v1(self, log_entry: str, fix_count: int) -> str:
        """Generate regex using iterative fix approach (legacy v1 algorithm).
        
        Args:
            log_entry: The log entry to generate regex for
            fix_count: Number of fix iterations to perform
            
        Returns:
            Generated regex pattern
        """
        try:
            from .llm import llm_service
            
            # Initial regex generation
            response = llm_service.generate_regex(log_entry, 0)
            if not response.get('success'):
                return ''
            
            regex = response.get('regex', '')
            
            # Iterative fixing
            for count in range(fix_count):
                if self.is_fully_matched(log_entry, regex):
                    self.log_info(f"Regex is fully matched after round {count}.")
                    break
                    
                self.log_info(f"Fixing regex for round {count+1}...")
                reduced = self.reduce_regex(log_entry, regex)
                
                # Send fix request to LLM
                payload = {
                    "model": "default",
                    "messages": [
                        {"role": "system", "content": "You are an expert in fixing PCRE2 regex patterns. Fix the provided regex to match the log entry completely."},
                        {"role": "user", "content": f"Log: {log_entry}\nRegex: {reduced}"}
                    ],
                    "temperature": 0.1
                }
                
                # This would need LLM service enhancement for fix requests
                # For now, just use the reduced regex
                regex = reduced
                self.log_info(f"New regex after round {count+1}: {regex}")
            
            return self.resolve_duplicate_capture_groups(regex)
            
        except Exception as e:
            self.log_error(f"Error in regex generation v1: {str(e)}", e)
            return ''
    
    def generate_regex_v2(self, log_entry: str, fix_count: int) -> str:
        """Generate regex using progressive matching approach (legacy v2 algorithm).
        
        Args:
            log_entry: The log entry to generate regex for
            fix_count: Number of fix iterations to perform
            
        Returns:
            Generated regex pattern
        """
        try:
            from .llm import llm_service
            import re
            
            regex = ""
            remaining_log = log_entry
            count = 0
            
            while remaining_log and count <= fix_count:
                if count == 0:
                    self.log_info(f"Generating regex for log: {remaining_log}")
                else:
                    self.log_info(f"Fixing regex for round {count}...")
                
                # Generate regex for remaining log
                response = llm_service.generate_regex(remaining_log, 0)
                if not response.get('success'):
                    break
                
                current_regex = response.get('regex', '')
                current_regex = current_regex.replace("```", "").replace("\n", "")
                
                if current_regex.startswith("regex"):
                    current_regex = current_regex[len("regex"):]
                
                if not current_regex.endswith("$"):
                    current_regex += "$"
                
                if count != fix_count:
                    reduced_regex = self.reduce_regex(remaining_log, current_regex)
                    self.log_info(f"Reduced regex: {reduced_regex}")
                else:
                    reduced_regex = current_regex
                
                # Try to match the reduced regex
                try:
                    match = re.search(reduced_regex, remaining_log)
                    if not match:
                        break
                    
                    matched_part = match.group(0)
                    self.log_info(f"Matched part of log: {matched_part}")
                    
                    remaining_log = remaining_log[match.end():].replace("\n", "")
                    self.log_info(f"Remaining log after match: {remaining_log}")
                    
                    if regex:
                        regex += (r"\s?" + reduced_regex)
                    else:
                        regex = reduced_regex
                        
                    self.log_info(f"New regex after round {count+1}: {regex}")
                    count += 1
                    
                except re.error as e:
                    self.log_error(f"Regex error: {str(e)}")
                    break
            
            if count >= fix_count:
                self.log_info(f"Reached maximum fix count of {fix_count}.")
            else:
                self.log_info(f"Regex is fully matched after round {count}.")
            
            regex = self.resolve_duplicate_capture_groups(regex)
            
            # Escape unescaped double quotes
            if '"' in regex:
                index_counter = 0
                while True:
                    try:
                        double_quote_index = regex.index('"', index_counter + 1, len(regex))
                        if regex[double_quote_index - 1] != '\\':
                            regex = regex[:double_quote_index] + '\\"' + regex[double_quote_index + 1:]
                        index_counter = double_quote_index + 1
                    except ValueError:
                        break
            
            return regex
            
        except Exception as e:
            self.log_error(f"Error in regex generation v2: {str(e)}", e)
            return ''
    
    def is_fully_matched(self, log: str, regex: str) -> bool:
        """Check if regex fully matches the log entry.
        
        Args:
            log: The log entry to test
            regex: The regex pattern to test
            
        Returns:
            True if fully matched, False otherwise
        """
        try:
            import re
            match = re.search(regex, log)
            if match:
                return match.group(0) == log
            return False
        except re.error:
            return False
    
    def reduce_regex(self, log: str, regex: str) -> str:
        """Reduce regex pattern until it matches the log.
        
        Args:
            log: The log entry to match
            regex: The regex pattern to reduce
            
        Returns:
            Reduced regex pattern
        """
        import re
        
        # Ensure regex is a string
        if not isinstance(regex, str):
            self.log_warning(f"Expected regex to be a string, got {type(regex)}. Converting to string.")
            regex = str(regex)
        
        while regex:
            try:
                if re.search(regex, log):
                    break
            except re.error:
                pass  # Skip invalid patterns silently
            regex = regex[:-1]
        
        return regex

    def determine_log_type(self, log_entry: str) -> Tuple[str, str]:
        """Determine the log type and source type for a log entry.
        
        Args:
            log_entry: The log entry to analyze
            
        Returns:
            Tuple of (log_type, source_type)
        """
        try:
            # Import the LLM service (now available)
            from .llm import llm_service
            
            # Use LLM to determine log type
            response = llm_service.determine_log_type(log_entry)
            
            if response and response.get('success'):
                result = response.get('result', '')
                if ',' in result:
                    source_type, log_type = [part.strip() for part in result.split(',', 1)]
                    return log_type, source_type
                else:
                    return result, 'unknown'
            else:
                self.log_warning(f"Failed to determine log type: {response.get('error', 'Unknown error')}")
                # Fallback to heuristic approach
                return self.determine_log_type_heuristic(log_entry)
                
        except Exception as e:
            self.log_error(f"Error determining log type: {str(e)}", e)
            # Fallback to heuristic approach
            return self.determine_log_type_heuristic(log_entry)
    
    def determine_log_type_heuristic(self, log_entry: str) -> Tuple[str, str]:
        """Determine log type using simple heuristics as fallback.
        
        Args:
            log_entry: The log entry to analyze
            
        Returns:
            Tuple of (log_type, source_type)
        """
        log_lower = log_entry.lower()
        
        # Simple heuristics for common log types
        if 'failed' in log_lower or 'error' in log_lower or 'authentication' in log_lower:
            return 'security', 'auth'
        elif 'get' in log_lower or 'post' in log_lower or 'http' in log_lower:
            return 'web', 'access'
        elif 'firewall' in log_lower or 'blocked' in log_lower:
            return 'network', 'firewall'
        elif 'syslog' in log_lower or 'kernel' in log_lower:
            return 'system', 'syslog'
        else:
            return 'unknown', 'generic'

    def resolve_duplicate_capture_groups(self, regex: str) -> str:
        """Resolve duplicate named capture groups by appending incremental numbers.
        
        Args:
            regex: The regex pattern to process
            
        Returns:
            Processed regex with unique capture group names
        """
        import re
        
        # Pattern to match named capture groups like (?P<name> or (?<name>
        pattern = re.compile(r'(\(\?P?<)(\w+)(>)')
        seen = {}
        offset = 0

        # Iterate over matches
        for match in list(pattern.finditer(regex)):
            group_name = match.group(2)
            if group_name in seen:
                # Increment counter for duplicate names
                seen[group_name] += 1
                new_name = f"{group_name}_{seen[group_name]}"
                
                # Replace the duplicate name
                start, end = match.span(2)
                regex = regex[:start + offset] + new_name + regex[end + offset:]
                offset += len(new_name) - len(group_name)
            else:
                seen[group_name] = 0
        
        self.log_info(f"Resolved duplicate capture groups: {seen}")
        return regex
    
    def create_rule_config(self, entry_ids: List[str]) -> str:
        """Create configuration for SmartLP entries based on active SIEM.
        
        Args:
            entry_ids: List of entry IDs to create config for
            
        Returns:
            Configuration string for the active SIEM
        """
        try:
            self.log_info(f"Creating SmartLP config for {len(entry_ids)} entries")
            
            # Get active SIEM from settings
            from .settings import settings_service
            settings = settings_service.get_global_settings()
            active_siem = settings.get('activeSiem', 'elastic')
            
            self.log_info(f"Active SIEM: {active_siem}")
            
            if active_siem == "splunk":
                return self.create_splunk_config(entry_ids)
            elif active_siem == "elastic":
                return self.create_elastic_config(entry_ids)
            else:
                self.log_error(f"Unsupported SIEM type: {active_siem}")
                return "# Unsupported SIEM type"
                
        except Exception as e:
            self.log_error(f"Error creating SmartLP config: {str(e)}", e)
            return f"# Error creating configuration: {str(e)}"
    
    def create_elastic_config(self, entry_ids: List[str]) -> str:
        """Create Elasticsearch Logstash configuration for SmartLP entries.
        
        Args:
            entry_ids: List of entry IDs
            
        Returns:
            Logstash pipeline configuration string
        """
        try:
            self.log_info(f"Creating Elastic config for {len(entry_ids)} entries")
            
            # Get entries from database
            entries = []
            for entry_id in entry_ids:
                entry = self.db.query(
                    self.collection_name,
                    {"id": entry_id},
                    projection={"_id": 0},
                    limit=1
                )
                if entry:
                    entries.append(entry)
                else:
                    self.log_warning(f"Entry not found: {entry_id}")
            
            if not entries:
                self.log_warning("No valid entries found for config generation")
                return "# No valid entries found"
            
            # Build Logstash pipeline
            pipeline = []
            
            # Input section
            pipeline.append(r'''input {
  tcp {
    port => 1700
    codec => multiline {
      pattern => "^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\s(.*?)\s[A-Z]+|^<Event xmlns|^\S{3}\s+\d+\s\d{2}:\d{2}:\d{2}|^<\d+>\S{3}\s+\d+\s\d{2}:\d{2}:\d{2}|^<\d+>\d\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d+\s\w+\s\w+:\d+"
      negate => true
      what => "previous"
    }
  }
}''')
            
            # Filter section
            pipeline.append("\nfilter {")
            
            # Add first grok pattern
            first_entry = entries[0]
            regex_config = self._format_regex_for_logstash(first_entry.get('regex', ''))
            source_type = first_entry.get('source_type', 'unknown')
            
            pipeline.append(f'''\n  grok {{
    match => {{
      message => {regex_config}
    }}
    add_field => {{"source_type" => "{source_type}"}}
  }}''')
            
            # Add additional grok patterns for subsequent entries
            for entry in entries[1:]:
                regex_config = self._format_regex_for_logstash(entry.get('regex', ''))
                source_type = entry.get('source_type', 'unknown')
                
                pipeline.append(f'''\n  if "_grokparsefailure" in [tags] {{
    grok {{
      match => {{
        message => {regex_config}
      }}
      add_field => {{"source_type" => "{source_type}"}}
      remove_tag => ["_grokparsefailure"]
    }}
  }}''')
            
            pipeline.append("}")
            
            # Output section
            pipeline.append("\noutput {")
            pipeline.append("  stdout { codec => rubydebug }")
            
            # Add elasticsearch outputs for each entry
            for entry in entries:
                source_type = entry.get('source_type', 'unknown')
                index = entry.get('index', 'unparsed')
                
                elastic_host = os.getenv('ELASTIC_HOST', 'localhost:9200')
                elastic_user = os.getenv('ELASTIC_USER', 'elastic')
                elastic_password = os.getenv('ELASTIC_PASSWORD', 'password')
                
                pipeline.append(f'''\n  if [source_type] == "{source_type}" {{
    elasticsearch {{
      hosts => ["{elastic_host}"]
      ssl_enabled => true
      ssl_certificate_authorities => "/etc/logstash/certs/cyberlab-rca-ica-chain.cer"
      user => "{elastic_user}"
      password => "{elastic_password}"
      data_stream => true
      data_stream_type => "logs"
      data_stream_dataset => "{index}"
      data_stream_namespace => "default"
    }}
  }}''')
            
            # Default output for unparsed logs
            elastic_host = os.getenv('ELASTIC_HOST', 'localhost:9200')
            elastic_user = os.getenv('ELASTIC_USER', 'elastic')
            elastic_password = os.getenv('ELASTIC_PASSWORD', 'password')
            
            pipeline.append(f'''\n  else {{
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
  }}''')
            
            pipeline.append("}")
            
            config = "".join(pipeline)
            self.log_info(f"Generated Elastic config with {len(entries)} entries")
            return config
            
        except Exception as e:
            self.log_error(f"Error creating Elastic config: {str(e)}", e)
            return f"# Error creating Elastic configuration: {str(e)}"
    
    def create_splunk_config(self, entry_ids: List[str]) -> str:
        """Create Splunk configuration for SmartLP entries.
        
        Args:
            entry_ids: List of entry IDs
            
        Returns:
            Splunk configuration string
        """
        try:
            self.log_info(f"Creating Splunk config for {len(entry_ids)} entries")
            
            # Get entries from database
            entries = []
            for entry_id in entry_ids:
                entry = self.db.query(
                    self.collection_name,
                    {"id": entry_id},
                    projection={"_id": 0},
                    limit=1
                )
                if entry:
                    entries.append(entry)
                else:
                    self.log_warning(f"Entry not found: {entry_id}")
            
            if not entries:
                self.log_warning("No valid entries found for config generation")
                return "# No valid entries found"
            
            # Prepare configuration components
            sh_props_conf = defaultdict(list)
            sh_transforms_conf = []
            hf_transforms_conf = []
            hf_index_routes = []
            hf_sourcetype_routes = []
            config_blocks = []
            
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
            
            # Build configuration blocks
            
            # SH props.conf
            config_blocks.append("### SH props.conf")
            for source_type, transforms in sh_props_conf.items():
                config_blocks.append(f"\n[{source_type}]\nREPORT-smartsoc = {', '.join(transforms)}")
            config_blocks.append("")  # Blank line after SH props.conf
            
            # SH transforms.conf
            config_blocks.append("### SH transforms.conf")
            config_blocks.extend(sh_transforms_conf)
            config_blocks.append("")  # Blank line after SH transforms.conf
            
            # HF props.conf
            config_blocks.append("### HF props.conf")
            config_blocks.append("\n[catchall]")
            config_blocks.append(f"TRANSFORMS-catchallindex = {', '.join(hf_index_routes)}")
            config_blocks.append(f"TRANSFORMS-catchallsourcetype = {', '.join(hf_sourcetype_routes)}")
            config_blocks.append("")  # Blank line after HF props.conf
            
            # HF transforms.conf
            config_blocks.append("### HF transforms.conf")
            config_blocks.extend(hf_transforms_conf)
            config_blocks.append("")  # Optional: Blank line at end
            
            config = "\n".join(config_blocks)
            self.log_info(f"Generated Splunk config with {len(entries)} entries")
            return config
            
        except Exception as e:
            self.log_error(f"Error creating Splunk config: {str(e)}", e)
            return f"# Error creating Splunk configuration: {str(e)}"
    
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
    
    def deploy_to_elasticsearch(self, entry_ids: List[str], pipeline_id: Optional[str] = None) -> Tuple[bool, str]:
        """Deploy SmartLP configuration to Elasticsearch as a Logstash pipeline.
        
        Args:
            entry_ids: List of entry IDs to deploy
            pipeline_id: Custom pipeline ID (uses environment default if None)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not ELASTICSEARCH_AVAILABLE:
                return False, "Elasticsearch library not available. Please install elasticsearch package."
            
            self.log_info(f"Starting Elasticsearch deployment for {len(entry_ids)} entries")
            
            # Get Elasticsearch configuration from environment
            elastic_host = os.getenv('ELASTIC_HOST')
            elastic_user = os.getenv('ELASTIC_USER')
            elastic_api_token = os.getenv('ELASTIC_API_TOKEN')
            elastic_cert_path = os.getenv('ELASTIC_CERT_PATH')
            default_pipeline_id = os.getenv('ELASTIC_PIPELINE_ID', 'smartsoc-smartlp-pipeline')
            
            # Validate required configuration
            if not elastic_host:
                return False, "ELASTIC_HOST environment variable not set"
            if not elastic_api_token:
                return False, "ELASTIC_API_TOKEN environment variable not set"
            
            # Use provided pipeline ID or default
            target_pipeline_id = pipeline_id or default_pipeline_id
            
            # Generate the Logstash pipeline configuration
            pipeline_config = self.create_elastic_config(entry_ids)
            
            if not pipeline_config or pipeline_config.startswith("# No valid entries"):
                return False, "No valid configuration generated. Check that entries exist and have required fields."
            
            # Create pipeline data structure
            pipeline_data = {
                "description": f"SmartSOC SmartLP pipeline - {len(entry_ids)} entries",
                "last_modified": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                "pipeline_metadata": {
                    "type": "logstash_pipeline",
                    "version": 1
                },
                "username": elastic_user or "smartsoc",
                "pipeline": pipeline_config,
                "pipeline_settings": {
                    "pipeline.workers": 1,
                    "pipeline.batch.size": 125,
                    "pipeline.batch.delay": 50,
                    "queue.type": "memory",
                    "queue.max_bytes": "1gb",
                    "queue.checkpoint.writes": 1024
                }
            }
            
            # Create Elasticsearch client
            es_client_config = {
                "hosts": [elastic_host],
                "headers": {
                    "Authorization": f"ApiKey {elastic_api_token}"
                }
            }
            
            # Add SSL configuration if certificate path is provided
            if elastic_cert_path and os.path.exists(elastic_cert_path):
                es_client_config["ca_certs"] = elastic_cert_path
                es_client_config["verify_certs"] = True
            else:
                self.log_warning("ELASTIC_CERT_PATH not set or certificate not found. Using insecure connection.")
                es_client_config["verify_certs"] = False
            
            service_elastic = Elasticsearch(**es_client_config)
            
            # Deploy the pipeline
            self.log_info(f"Deploying pipeline '{target_pipeline_id}' to Elasticsearch")
            response = service_elastic.logstash.put_pipeline(id=target_pipeline_id, body=pipeline_data)
            
            # Check response (Elasticsearch returns None for successful operations)
            if response is None or (isinstance(response, dict) and response.get('acknowledged', False)):
                success_msg = f"Pipeline '{target_pipeline_id}' deployed successfully to Elasticsearch"
                self.log_info(success_msg)
                return True, success_msg
            else:
                error_msg = f"Unexpected response from Elasticsearch: {response}"
                self.log_error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Failed to deploy to Elasticsearch: {str(e)}"
            self.log_error(error_msg, e)
            return False, error_msg
    
    def list_elasticsearch_pipelines(self) -> Tuple[Optional[Dict], Optional[str]]:
        """List all Logstash pipelines in Elasticsearch.
        
        Returns:
            Tuple of (pipelines_dict, error_message)
        """
        try:
            if not ELASTICSEARCH_AVAILABLE:
                return None, "Elasticsearch library not available"
            
            # Get Elasticsearch configuration
            elastic_host = os.getenv('ELASTIC_HOST')
            elastic_api_token = os.getenv('ELASTIC_API_TOKEN')
            elastic_cert_path = os.getenv('ELASTIC_CERT_PATH')
            
            if not elastic_host or not elastic_api_token:
                return None, "Elasticsearch configuration not available"
            
            # Create Elasticsearch client
            es_client_config = {
                "hosts": [elastic_host],
                "headers": {
                    "Authorization": f"ApiKey {elastic_api_token}"
                }
            }
            
            if elastic_cert_path and os.path.exists(elastic_cert_path):
                es_client_config["ca_certs"] = elastic_cert_path
                es_client_config["verify_certs"] = True
            else:
                es_client_config["verify_certs"] = False
            
            service_elastic = Elasticsearch(**es_client_config)
            
            # Get all pipelines
            response = service_elastic.logstash.get_pipeline()
            
            if response:
                self.log_info(f"Retrieved {len(response)} pipelines from Elasticsearch")
                return response, None
            else:
                return {}, None
                
        except Exception as e:
            error_msg = f"Failed to list Elasticsearch pipelines: {str(e)}"
            self.log_error(error_msg, e)
            return None, error_msg
    
    def delete_elasticsearch_pipeline(self, pipeline_id: str) -> Tuple[bool, str]:
        """Delete a Logstash pipeline from Elasticsearch.
        
        Args:
            pipeline_id: ID of the pipeline to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not ELASTICSEARCH_AVAILABLE:
                return False, "Elasticsearch library not available"
            
            # Get Elasticsearch configuration
            elastic_host = os.getenv('ELASTIC_HOST')
            elastic_api_token = os.getenv('ELASTIC_API_TOKEN')
            elastic_cert_path = os.getenv('ELASTIC_CERT_PATH')
            
            if not elastic_host or not elastic_api_token:
                return False, "Elasticsearch configuration not available"
            
            # Create Elasticsearch client
            es_client_config = {
                "hosts": [elastic_host],
                "headers": {
                    "Authorization": f"ApiKey {elastic_api_token}"
                }
            }
            
            if elastic_cert_path and os.path.exists(elastic_cert_path):
                es_client_config["ca_certs"] = elastic_cert_path
                es_client_config["verify_certs"] = True
            else:
                es_client_config["verify_certs"] = False
            
            service_elastic = Elasticsearch(**es_client_config)
            
            # Delete the pipeline
            self.log_info(f"Deleting pipeline '{pipeline_id}' from Elasticsearch")
            response = service_elastic.logstash.delete_pipeline(id=pipeline_id)
            
            if response is None or (isinstance(response, dict) and response.get('acknowledged', False)):
                success_msg = f"Pipeline '{pipeline_id}' deleted successfully from Elasticsearch"
                self.log_info(success_msg)
                return True, success_msg
            else:
                error_msg = f"Failed to delete pipeline '{pipeline_id}': {response}"
                self.log_error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Failed to delete pipeline '{pipeline_id}': {str(e)}"
            self.log_error(error_msg, e)
            return False, error_msg
    
    def get_elasticsearch_pipeline(self, pipeline_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get details of a specific Logstash pipeline from Elasticsearch.
        
        Args:
            pipeline_id: ID of the pipeline to retrieve
            
        Returns:
            Tuple of (pipeline_dict, error_message)
        """
        try:
            if not ELASTICSEARCH_AVAILABLE:
                return None, "Elasticsearch library not available"
            
            # Get Elasticsearch configuration
            elastic_host = os.getenv('ELASTIC_HOST')
            elastic_api_token = os.getenv('ELASTIC_API_TOKEN')
            elastic_cert_path = os.getenv('ELASTIC_CERT_PATH')
            
            if not elastic_host or not elastic_api_token:
                return None, "Elasticsearch configuration not available"
            
            # Create Elasticsearch client
            es_client_config = {
                "hosts": [elastic_host],
                "headers": {
                    "Authorization": f"ApiKey {elastic_api_token}"
                }
            }
            
            if elastic_cert_path and os.path.exists(elastic_cert_path):
                es_client_config["ca_certs"] = elastic_cert_path
                es_client_config["verify_certs"] = True
            else:
                es_client_config["verify_certs"] = False
            
            service_elastic = Elasticsearch(**es_client_config)
            
            # Get the specific pipeline
            response = service_elastic.logstash.get_pipeline(id=pipeline_id)
            
            if response and pipeline_id in response:
                self.log_info(f"Retrieved pipeline '{pipeline_id}' from Elasticsearch")
                return response[pipeline_id], None
            else:
                return None, f"Pipeline '{pipeline_id}' not found"
                
        except Exception as e:
            error_msg = f"Failed to get pipeline '{pipeline_id}': {str(e)}"
            self.log_error(error_msg, e)
            return None, error_msg


# Create service instance
smartlp_service = SmartLPService()