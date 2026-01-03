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
import pcre2
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, List
from collections import defaultdict

from .base import BaseService, CRUDService
from models.core import LogEntry, RuleStatus
from .siem import SIEMServiceFactory
from .settings import settings_service
from .regex_engine import regex_engine_service
from .rag import rag_service
from .llm import llm_service
from utils.formatters import generate_alphanumeric_id, clean_response

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
        super().__init__("smartlp", "logs")
        self._ingestion_thread: Optional[threading.Thread] = None
        self._stop_ingestion = threading.Event()
        self._ingestion_running = False
        self.logger.propagate = False  # Prevent double logging
    
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
        from services.settings import settings_service

        while not self._stop_ingestion.is_set():
            # Load settings every cycle
            settings = settings_service.get_global_settings()
            interval = int(settings.get("ingest_frequency", 30)) * 60 

            try:
                self.perform_ingestion()
            except Exception as e:
                self.log_error("[INGESTION] Error during log ingestion", e)

            # Sleep with exit awareness
            if self._stop_ingestion.wait(timeout=interval):
                break

    
    def perform_ingestion(self) -> None:
        """Perform a single ingestion cycle."""
        try:
            # Get settings for ingestion configuration
            from services.settings import settings_service
            settings = settings_service.get_global_settings()

            # Backend uses snake_case keys for settings
            if not settings.get('ingest_on', False):
                return

            # Get ingestion parameters (snake_case)
            active_siem = settings.get('active_siem', 'elastic')
            similarity_check = settings.get('similarity_check', False)
            similarity_threshold = float(settings.get('similarity_threshold', 0.8))
            fix_count = int(settings.get('fix_count', 3))
            
            self.log_info(f"[INGESTION] Starting ingestion cycle for SIEM: {active_siem}")
            
            # Get SIEM-specific search configuration
            siem_settings = settings_service.get_siem_settings()
            siem_settings = next((s for s in siem_settings if s['id'] == active_siem), None)
            
            if not siem_settings:
                self.log_error(f"[INGESTION] No configuration found for SIEM: {active_siem}")
                return

            logs, error = self.ingest_from_siem(
                active_siem,
                siem_settings.get('search_index', ''),
                siem_settings.get('search_query', ''),
                int(siem_settings.get('search_entry_count', 10) or 10)
            )
            
            if error:
                self.log_error(f"[INGESTION] SIEM ingestion failed: {error}")
                return
            
            if not logs:
                self.log_info(f"[INGESTION] No new logs retrieved from {active_siem}")
                return
            
            # Process each ingested log
            processed_count = 0
            for log in logs:
                try:
                    # Generate embedding
                    embedding = rag_service.generate_embeddings(log)

                    # Check for similarity if enabled
                    if similarity_check and self.check_log_similarity(log, similarity_threshold):
                        self.log_info(f"[INGESTION] Skipped similar log: {log[:50]}...")
                        continue
                    
                    # Determine log type and source type
                    results = self.determine_log_type(log)
                    log_type = results["log_type"]
                    source_type = results["source_type"]

                    # Identify package for log
                    package = self.resolve_native_package(log, source_type, active_siem)
                    regex = None

                    if not package:
                        package = self.identify_package(log, log_type, source_type, active_siem)
                    if not package['found']:
                        # Generate regex for the log
                        results = self.generate_regex(log, fix_count)
                        regex = results['regex']
                        
                        # Run regex match to get status
                        match_result = regex_engine_service.run_regex_match(log, regex)
                        status = match_result['status']
                    else:
                        status = "Pending"

                    # Create log entry in database
                    entry_data = {
                        'id': generate_alphanumeric_id(8),
                        'log': log,
                        'regex': regex,
                        'status': status,
                        'log_type': log_type,
                        'source_type': source_type,
                        'timestamp': datetime.now().isoformat(),
                        'package_name': package.get('package_name', None),
                        'package_url': package.get('package_url', None),
                        'embedding': embedding
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
                    # Check if search_id contains commas (multiple IDs for settings panel)
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
                if status == 'Unmatched' or status == "Partially Matched":
                    unparsed_count += 1
                else:
                    parsed_count += 1
                    
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
                    index=search_index,
                    query=search_query,
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

    def ingest_from_siem(self, siem_type: str, search_index: str, search_query: str, entry_count: int) -> Tuple[Optional[List[str]], Optional[str]]:
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
                index=search_index,
                query=search_query,
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

    def check_log_similarity(self, log: str, threshold: float) -> bool:
        """Check if a log entry is similar to existing entries using
        both text and semantic similarity."""
        try:
            from difflib import SequenceMatcher

            # Fetch recent entries
            recent_entries = self.db.query(
                self.collection_name,
                {},
                projection={"log": 1},
                sort=[("timestamp", -1)],
                limit=100
            )

            masked_log = self.mask_log_entry(log)

            # Precompute embedding for incoming log
            semantic_log_emb = rag_service.generate_embeddings([masked_log])[0]

            for entry in recent_entries:
                if isinstance(entry, tuple):
                    entry = entry[1]  # or whatever contains the actual dict

                existing_log = entry.get("log", "")
                masked_existing = self.mask_log_entry(existing_log)

                # ---- Text similarity ----
                text_sim = SequenceMatcher(None, masked_log, masked_existing).ratio()

                # ---- Semantic similarity ----
                existing_emb = rag_service.generate_embeddings([masked_existing])[0]
                semantic_sim = rag_service.cosine(semantic_log_emb, existing_emb)

                # ---- Final combined similarity ----
                final_sim = (text_sim + semantic_sim) / 2.0

                if final_sim >= threshold:
                    self.log_info(
                        f"Similar log found (text={text_sim:.2f}, "
                        f"semantic={semantic_sim:.2f}, avg={final_sim:.2f})"
                    )
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
        # Mask IP addresses
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        masked = pcre2.sub(ip_pattern, '1.1.1.1', log)
        
        # Mask timestamps (common patterns)
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',   # US format
            r'\w{3} \d{1,2} \d{2}:\d{2}:\d{2}',       # Syslog format
        ]
        
        for pattern in timestamp_patterns:
            masked = pcre2.sub(pattern, 'TIMESTAMP', masked)
        
        return masked

    

    def generate_regex(self, log: str, fix_count: int = 3) -> Dict[str, Any]:
        """Unified entrypoint for regex generation."""
        settings = settings_service.get_global_settings()
        algo = settings.get("ingest_algo_version", "v2")

        if algo == "v2":
            return self.generate_regex_v2(log, fix_count)
        return self.generate_regex_v1(log)

    def generate_regex_v1(self, log: str) -> Dict[str, Any]:
        self.log_info("Generating regex (v1)...")

        system_prompt = settings_service.get_prompts_settings("generate_regex")

        result = rag_service.query_rag(
            user_prompt=log, 
            system_prompt=system_prompt
        )

        if not result["success"]:
            return {
                "success": False,
                "regex": None,
                "error": result["error"],
                "latency": result["latency"]
            }

        # Clean
        regex = clean_response(result["content"])
        if not regex.endswith("$"):
            regex += "$"

        return {
            "success": True,
            "regex": regex,
            "error": None,
            "latency": result["latency"]
        }
    
    
    def generate_regex_v2(self, log: str, fix_count: int) -> Dict[str, Any]:
        self.log_info("Generating regex (v2)...")

        system_prompt = settings_service.get_prompts_settings("generate_regex")

        remaining = log
        final_regex = ""
        total_latency = 0.0

        for i in range(fix_count):
            # Ask LLM for this segment
            self.log_info(f"Generating regex round {i+1}...")
            result = rag_service.query_rag(
                user_prompt=remaining, 
                system_prompt=system_prompt
            )

            total_latency += result.get("latency", 0)

            if not result["success"]:
                return {
                    "success": False,
                    "regex": final_regex or None,
                    "error": result["error"],
                    "latency": total_latency
                }

            raw = clean_response(result["content"])
            if not raw.endswith("$"):
                raw += "$"

            # reduce to longest valid partial match
            reduced = regex_engine_service.run_reduce_regex(remaining, raw)
            reduced = reduced["regex"]
            self.log_info(f"Reduced regex: {reduced}")

            # match it
            match_info = regex_engine_service.run_regex_match(remaining, reduced)
            if match_info["status"] == "Not Matched":
                self.log_warning("Reduced regex no longer matches, stopping.")
                break

            matched = match_info["full"]["value"]
            end = match_info["full"]["end"]

            # append
            if final_regex:
                final_regex += r"\s?" + reduced
            else:
                final_regex = reduced

            # move forward
            remaining = remaining[end:]
            if not remaining:
                break

        # post-process result
        final_regex = self.resolve_duplicate_capture_groups(final_regex)

        return {
            "success": True,
            "regex": final_regex,
            "error": None,
            "latency": total_latency
        }

    def fix_regex(self, log: str, regex: str) -> Dict[str, Any]:
        system_prompt = settings_service.get_prompts_settings("fix_regex")

        # shrink to longest matching core
        longest = regex_engine_service.run_reduce_regex(log, regex)
        longest = longest["regex"]

        result = rag_service.query_rag(
            user_prompt=f"log: {log}\ncurrent regex: {regex}\nreduced core: {longest}", 
            system_prompt=system_prompt
        )

        if not result["success"]:
            return {
                "success": False,
                "regex": None,
                "error": result["error"],
                "latency": result["latency"]
            }

        fixed = clean_response(result["content"])
        if not fixed.endswith("$"):
            fixed += "$"

        return {
            "success": True,
            "regex": fixed,
            "error": None,
            "latency": result["latency"]
        }

    def determine_log_type(self, log: str) -> Dict[str, Any]:
        """Return { success, source_type, log_type, error }"""

        try:
            self.log_info("Determining log type for entry")
            
            system_prompt = settings_service.get_prompts_settings("detect_type")
            response = llm_service.query_llm(log, system_prompt)

            if not response["success"]:
                return {
                    "success": False,
                    "error": response["error"],
                    "source_type": "unknown",
                    "log_type": "unknown"
                }

            # Parse JSON
            try:
                result = json.loads(clean_response(response["content"]))
                return {
                    "success": True,
                    "source_type": result.get("source_type", "unknown"),
                    "log_type": result.get("log_type", "unknown"),
                    "error": None
                }

            except Exception as e:
                self.log_warning(f"LLM returned invalid JSON: {response['content']}")
                return {
                    "success": False,
                    "error": f"Invalid JSON from LLM: {str(e)}",
                    "source_type": "unknown",
                    "log_type": "unknown"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source_type": "unknown",
                "log_type": "unknown"
            }

    
    def determine_log_type_heuristic(self, log: str) -> Tuple[str, str]:
        """Determine log type using simple heuristics as fallback.
        
        Args:
            log: The log entry to analyze
            
        Returns:
            Tuple of (log_type, source_type)
        """
        log_lower = log.lower()
        
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
    
    def get_package_url(self, package_name: str, siem: str) -> str:
        """Get package URL based on SIEM type."""
        if siem == "elastic":
            return f"https://www.elastic.co/docs/reference/integrations/{package_name}"
        elif siem == "splunk":
            package_number = {
                "TA-Windows": "742",
            }.get(package_name, "unknown")
            return f"https://splunkbase.splunk.com/app/{package_number}"
        return ""
    
    def resolve_native_package(self, log: str, source_type: str, active_siem: str) -> Optional[Dict[str, Any]]:
        """
        Refactored package resolution using regex for channel extraction 
        and dictionary-based lookups for cleaner logic.
        """
        if source_type.lower() != "windows":
            return None

        # 1. Extract the Channel name using Regex (faster than full XML parsing)
        channel_match = re.search(r"<Channel>(.*?)</Channel>", log, re.IGNORECASE)
        channel = channel_match.group(1) if channel_match else ""

        # 2. Define the logic for package selection
        # Standard channels go to 'windows', everything else to 'winlog'
        standard_channels = {"application", "security", "system"}
        
        is_elastic = (active_siem.lower() == "elastic")
        
        # Determine package name based on SIEM and Channel
        if channel.lower() in standard_channels:
            pkg_name = "windows" if is_elastic else "TA-Windows"
            confidence = 0.9  # High confidence for standard logs
        else:
            pkg_name = "winlog" if is_elastic else "TA-Windows"
            confidence = 0.7  # Lower confidence for custom channels

        # 3. Construct and return the response
        return {
            "is_native": True,
            "package_name": pkg_name,
            "package_url": self.get_package_url(pkg_name, active_siem),
            "siem": active_siem,
            "confidence": confidence,
            "found": True,
            "metadata": {"extracted_channel": channel} # Useful for debugging
        }

    def identify_package(self, log: str, log_type: str, source_type: str, active_siem: str = None) -> Dict[str, Any]:
        """Identify package for the log based on log_type and source_type."""
        if not active_siem:
            active_siem = settings_service.get_global_settings().get("active_siem")
        self.log_info(f"Identifying {active_siem} package for log entry...")
        
        # Fetch Settings
        system_prompt = settings_service.get_prompts_settings("identify_package")
        
        # Prepare RAG Query
        user_prompt = f"log: {log}\nlog_type: {log_type}\nsource_type: {source_type}\nsiem: {active_siem}"
        
        # Execute RAG
        response = rag_service.query_rag(user_prompt, system_prompt, filter_category=f"{active_siem}_packages")

        # Handle RAG System Failure (Database down, Network error, etc.)
        if not response["success"]:
            return {
                "success": False,
                "found": False,
                "context": response.get("context", []),
                "error": f"RAG Service Failure: {response.get('error')}",
                "package_name": "",
                "package_url": ""
            }

        # Parse LLM Result
        try:
            content = clean_response(response["content"])
            result = json.loads(content)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "found": False,
                "context": response["context"],
                "error": f"LLM Output Parsing Failed: {str(e)} | Raw: {response['content']}",
                "package_name": "", 
                "package_url": ""
            }

        # Determine "Found" vs "Not Found"
        package_name = result.get("package_name", "")
        is_found = bool(package_name and package_name.strip())

        return {
            "success": True,          # The operation completed successfully (no crashes)
            "found": is_found,        # Did we actually find the package?
            "context": response["context"],
            "package_name": package_name,
            "package_url": result.get("package_url", ""),
            "error": None
        }

    def resolve_duplicate_capture_groups(self, regex: str) -> str:
        """Resolve duplicate named capture groups by appending incremental numbers.
        
        Args:
            regex: The regex pattern to process
            
        Returns:
            Processed regex with unique capture group names
        """
        # Pattern to match named capture groups like (?P<name> or (?<name>
        pattern = pcre2.compile(r'(\(\?(?:P?<|<))(\w+)(>)')
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
    
    def create_config(self, entry_ids: List[str]) -> str:
        """Create configuration for SmartLP entries based on active SIEM.
        
        Args:
            entry_ids: List of entry IDs to create config for
            
        Returns:
            Configuration string for the active SIEM
        """
        try:
            self.log_info(f"Creating SmartLP config for {len(entry_ids)} entries")
            
            # Get active SIEM from settings (snake_case)
            from .settings import settings_service
            settings = settings_service.get_global_settings()
            active_siem = settings.get('active_siem', 'elastic')
            
            self.log_info(f"Active SIEM: {active_siem}")
            
            if active_siem == "splunk":
                return self.create_config_splunk(entry_ids)
            elif active_siem == "elastic":
                return self.create_config_elastic(entry_ids)
            else:
                self.log_error(f"Unsupported SIEM type: {active_siem}")
                return "# Unsupported SIEM type"
                
        except Exception as e:
            self.log_error(f"Error creating SmartLP config: {str(e)}", e)
            return f"# Error creating configuration: {str(e)}"

    def create_config_elastic(self, entry_ids: List[str]) -> str:
        """Create Elasticsearch Logstash configuration for SmartLP entries."""
        try:
            self.log_info(f"Creating Elastic config for {len(entry_ids)} entries")
            
            # Fetch selected entries
            selected_entries = self.db.query(
                collection_name="logs",
                # `entry_ids` are SmartLP's user-facing IDs (field `id`), not Mongo `_id`.
                filter_dict={"id": {"$in": entry_ids}},
            )

            # Fetch deployed entries
            deployed_entries = self.db.query(
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
                self.log_warning("No valid entries found for config generation")
                return "# No valid entries found"

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
            elastic_settings = self._get_elastic_settings()
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
            self.log_info(f"Generated Elastic config with {len(all_entries)} entries")
            return config

        except Exception as e:
            self.log_error(f"Error generating Elastic config: {str(e)}")
            return f"# Error: {str(e)}"
    
    def create_config_splunk(self, entry_ids: List[str]) -> str:
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
            elastic_settings = self._get_elastic_settings()
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
            self.log_error("Elasticsearch deployment failed", e)
            return False, f"Failed to deploy Logstash pipeline: {e}"

    def _get_elastic_settings(self) -> Dict[str, Optional[str]]:
        """Return Elasticsearch connectivity details from settings or env."""
        siem_configs = settings_service.get_siem_settings() or []
        elastic_settings = next((cfg for cfg in siem_configs if cfg.get('id') == 'elastic'), {})

        resolved = {
            'host': elastic_settings.get('host') or os.getenv('ELASTIC_HOST'),
            'user': elastic_settings.get('user') or os.getenv('ELASTIC_USER'),
            'password': elastic_settings.get('password') or os.getenv('ELASTIC_PASSWORD'),
            'api_key': elastic_settings.get('api_key') or os.getenv('ELASTIC_API_TOKEN'),
            'cert_path': elastic_settings.get('cert_path') or os.getenv('ELASTIC_CERT_PATH'),
            'pipeline_id': elastic_settings.get('pipeline_id') or os.getenv('ELASTIC_PIPELINE_ID') or 'smartlp'
        }

        if not resolved['host'] or not resolved['api_key']:
            self.log_warning("Elasticsearch configuration incomplete; check SIEM settings and environment variables")

        return resolved
    
    def deploy_config_splunk(self, entry_ids: List[str]) -> Tuple[bool, str]:
        """Deploy SmartLP configuration to Splunk by writing to props.conf and transforms.conf.
        
        Args:
            entry_ids: List of entry IDs to deploy
        """
        pass

# Create service instance
smartlp_service = SmartLPService()