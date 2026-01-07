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
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, List

from .base import CRUDService
from .siem import SIEMServiceFactory, elasticsearch_service, splunk_service
from .settings import settings_service
from .regex_engine import regex_engine_service
from .rag import rag_service
from .llm import llm_service
from database.connection import db_connection
from utils.formatters import generate_alphanumeric_id, clean_response


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
                    results = self.identify_log_type(log)
                    log_type = results["log_type"]
                    source_type = results["source_type"]
                    description = results["description"]

                    # Identify package for log
                    package = self.resolve_native_package(log, source_type, active_siem)
                    regex = None

                    if not package:
                        package = self.identify_package(log, log_type, source_type, active_siem)
                    if not package['package_name'] and not package['package_url']:
                        # Generate regex for the log
                        results = self.generate_regex(log, fix_count)
                        regex = results['regex']
                        
                        # Run regex match to get status
                        match_result = regex_engine_service.run_regex_match(log, regex)
                        status = match_result['status']
                    else:
                        status = "Pending"
                    
                    results = self.identify_detection_rules(description, active_siem)
                    if not results.get("success"):
                        self.log_error(
                            f"[INGESTION] Detection rule identification failed: {results.get('error')}"
                        )

                    detection_rules = results.get('detection_rules', [])
                    
                    # Create log entry in database
                    entry_data = {
                        'id': generate_alphanumeric_id(8),
                        'log': log,
                        'regex': regex,
                        'status': status,
                        'log_type': log_type,
                        'source_type': source_type,
                        'description': description,
                        'timestamp': datetime.now().isoformat(),
                        'package_name': package.get('package_name', None),
                        'package_url': package.get('package_url', None),
                        'detection_rules': detection_rules,
                        'detection_status': (
                            "recommended" if detection_rules else "none"
                        ),
                        'max_detection_confidence': (
                            max([r["confidence"] for r in detection_rules])
                            if detection_rules else 0
                        ),
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
            
            entry = db_connection.query(
                self.collection_name,
                {"status": "Unmatched" or "Partially Matched"},
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
            count = db_connection.count_documents(
                self.collection_name,
                {"status": { "$in": ['unmatched', 'partially matched']}}
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
            statuses = db_connection.get_distinct_values(self.collection_name, "status")
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
            entries = db_connection.query(
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
            all_entries = db_connection.query(self.collection_name, {})
            
            # Initialize counters
            parsed_count = 0
            unparsed_count = 0
            logtype_stats: Dict[str, int] = {}

            # Time series aggregation inputs
            timestamp_rows: List[tuple[datetime, bool]] = []
            
            # Process entries
            for entry in all_entries:
                status_raw = entry.get('status', 'Unmatched')
                status_norm = str(status_raw).strip().lower().replace('_', '-')

                is_unparsed = status_norm in {'unmatched', 'partially matched'}

                # Dashboard uses `entry.log_type`; keep backward-compatible fallbacks.
                log_type = (
                    entry.get('log_type')
                    or entry.get('logtype')
                    or entry.get('logType')
                    or 'Unknown'
                )
                log_type = str(log_type).strip() or 'Unknown'

                # Parse timestamp for volume chart
                raw_ts = entry.get('timestamp') or entry.get('time') or entry.get('@timestamp')
                if raw_ts is not None:
                    dt: datetime | None = None
                    try:
                        if isinstance(raw_ts, (int, float)):
                            dt = datetime.fromtimestamp(float(raw_ts), tz=timezone.utc)
                        else:
                            ts_str = str(raw_ts).strip()
                            # Handle common ISO forms, including trailing 'Z'
                            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        dt = None

                    if dt is not None:
                        dt_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
                        timestamp_rows.append((dt_utc, is_unparsed))

                # Count parsed vs unparsed and aggregate unparsed log types
                if is_unparsed:
                    unparsed_count += 1
                    logtype_stats[log_type] = logtype_stats.get(log_type, 0) + 1
                else:
                    parsed_count += 1
            
            # Get top 5 unparsed logtypes
            sorted_logtypes = sorted(logtype_stats.items(), key=lambda x: x[1], reverse=True)[:5]

            # Build volume-over-time series (earliest -> latest, dynamic range)
            volume_over_time: List[Dict[str, Any]] = []
            if timestamp_rows:
                min_dt = min(dt for dt, _ in timestamp_rows)
                max_dt = max(dt for dt, _ in timestamp_rows)
                span = max_dt - min_dt

                if span <= timedelta(hours=48):
                    bucket = 'hour'
                    step = timedelta(hours=1)
                elif span <= timedelta(days=120):
                    bucket = 'day'
                    step = timedelta(days=1)
                else:
                    bucket = 'week'
                    step = timedelta(days=7)

                def floor_bucket(dt: datetime) -> datetime:
                    if bucket == 'hour':
                        return dt.replace(minute=0, second=0, microsecond=0)
                    if bucket == 'day':
                        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    # week bucket (Monday as start of week)
                    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    return start - timedelta(days=start.weekday())

                start_dt = floor_bucket(min_dt)
                end_dt = floor_bucket(max_dt)

                buckets: Dict[datetime, Dict[str, int]] = {}
                cursor = start_dt
                while cursor <= end_dt:
                    buckets[cursor] = {'parsed': 0, 'unparsed': 0}
                    cursor += step

                for dt, is_unparsed in timestamp_rows:
                    key = floor_bucket(dt)
                    if key not in buckets:
                        buckets[key] = {'parsed': 0, 'unparsed': 0}
                    if is_unparsed:
                        buckets[key]['unparsed'] += 1
                    else:
                        buckets[key]['parsed'] += 1

                for key in sorted(buckets.keys()):
                    parsed_v = buckets[key]['parsed']
                    unparsed_v = buckets[key]['unparsed']
                    if bucket == 'hour':
                        label = key.strftime('%Y-%m-%d %H:00')
                    elif bucket == 'day':
                        label = key.strftime('%Y-%m-%d')
                    else:
                        label = f"Week of {key.strftime('%Y-%m-%d')}"

                    volume_over_time.append({
                        'label': label,
                        'parsed': parsed_v,
                        'unparsed': unparsed_v,
                        'total': parsed_v + unparsed_v
                    })
            
            # Format for frontend compatibility
            report_data = {
                'parsed': parsed_count,
                'unparsed': unparsed_count,
                'logtypes': sorted_logtypes,  # Array of [logtype, count] pairs
                'volume_over_time': volume_over_time,
                'total': parsed_count + unparsed_count,
                'generated_at': datetime.utcnow().isoformat()
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
            recent_entries = db_connection.query(
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
        failure_count = 0

        for i in range(fix_count):
            remaining_stripped = remaining.strip()
            if not remaining_stripped:
                self.log_info("Remaining log empty, stopping.")
                break

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
            reduced = regex_engine_service.run_reduce_regex(remaining, raw)["regex"]
            self.log_info(f"Reduced regex: {reduced}")

            # match it
            match_info = regex_engine_service.run_regex_match(remaining, reduced)
            matched_value = match_info["full"]["value"]
            end = match_info["full"]["end"]

            # check if regex failed to advance
            if match_info["status"] == "Unmatched" or end == 0:
                failure_count += 1
                self.log_warning(f"Regex failed to match or advance. Failure count: {failure_count}")
                if failure_count >= 3:
                    final_regex += r"\s?.*"
                    self.log_warning("Too many failures, appending wildcard and stopping.")
                    break
                continue  # try next round without updating remaining

            failure_count = 0  # reset on success

            # append to final regex
            if final_regex:
                if reduced:
                    final_regex += r"\s?" + reduced
                else:
                    final_regex += reduced
            else:
                final_regex = reduced

            # move forward
            remaining = remaining[end:]
            self.log_info(f"Remaining log for next round: {remaining}")

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

    def identify_log_type(self, log: str) -> Dict[str, Any]:
        """Return { success, source_type, log_type, error }"""

        try:
            self.log_info("Identifying log type for entry")
            
            system_prompt = settings_service.get_prompts_settings("identify_type")
            response = llm_service.query_llm(log, system_prompt)

            if not response["success"]:
                return {
                    "success": False,
                    "error": response["error"],
                    "source_type": "unknown",
                    "log_type": "unknown",
                    "description": ""
                }

            # Parse JSON
            try:
                result = json.loads(clean_response(response["content"]))
                self.log_info(f"Identified log type: {str(result.get('log_type', 'unknown'))}, source type: {str(result.get('source_type', 'unknown'))}")
                return {
                    "success": True,
                    "source_type": result.get("source_type", "unknown"),
                    "log_type": result.get("log_type", "unknown"),
                    "description": result.get("description", ""),
                    "error": None
                }

            except Exception as e:
                self.log_warning(f"LLM returned invalid JSON: {response['content']}")
                return {
                    "success": False,
                    "error": f"Invalid JSON from LLM: {str(e)}",
                    "source_type": "unknown",
                    "log_type": "unknown",
                    "description": ""
                }

        except Exception as e:
            self.log_error(f"Error identifying log type: {str(e)}", e)
            return {
                "success": False,
                "error": str(e),
                "source_type": "unknown",
                "log_type": "unknown",
                "description": ""
            }
    
    def get_package_url(self, package_name: str, siem: str) -> str:
        """Get package URL based on SIEM type."""
        if siem == "elastic":
            return f"https://www.elastic.co/docs/reference/integrations/{package_name}"
        elif siem == "splunk":
            package_number = {
                "TA-Windows": "742",
                "TA-VMWare": "3215",
            }.get(package_name, "unknown")
            return f"https://splunkbase.splunk.com/app/{package_number}"
        return ""
    
    def resolve_native_package(self, log: str, source_type: str, active_siem: str) -> Optional[Dict[str, Any]]:
        siem = active_siem.lower()
        source = source_type.lower()

        if source == "windows":
            channel_match = re.search(r"<Channel>(.*?)</Channel>", log, re.IGNORECASE)
            channel = channel_match.group(1).lower() if channel_match else ""
            standard_channels = {"application", "security", "system"}

            if siem == "elastic":
                pkg_name = "windows" if channel in standard_channels else "winlog"
            elif siem == "splunk":
                pkg_name = "TA-Windows"
            else:
                return None

        elif source in {"vmware", "vsphere"}:
            if siem == "elastic":
                pkg_name = "vsphere"
            elif siem == "splunk":
                pkg_name = "TA-VMWare"
            else:
                return None
        else:
            return None

        return {
            "is_native": True,
            "package_name": pkg_name,
            "package_url": self.get_package_url(pkg_name, siem),
            "found": True
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
            content = clean_response(response.get("content", ""))
            result = json.loads(content)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "found": False,
                "context": response.get("context", []),
                "error": f"LLM Output Parsing Failed: {str(e)} | Raw: {response.get('content')}",
                "package_name": "", 
                "package_url": ""
            }

        # Determine "Found" vs "Not Found"
        package_name = result.get("package_name", "")
        is_found = bool(package_name and package_name.strip())

        return {
            "success": True,          # The operation completed successfully (no crashes)
            "found": is_found,        # Did we actually find the package?
            "context": response.get("context", []),
            "package_name": package_name,
            "package_url": result.get("package_url", ""),
            "error": None
        }

    def identify_detection_rules(
        self,
        log_description: str,
        active_siem: str = None,
        confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Identify relevant detection rules for a log using semantic RAG matching.

        This function assumes that log_description has already been generated
        during the log classification stage.
        """

        if not active_siem:
            active_siem = settings_service.get_global_settings().get("active_siem")

        self.log_info(f"Identifying {active_siem} detection rules from log description...")

        # Prepare RAG prompts
        system_prompt = settings_service.get_prompts_settings("identify_detection_rules")

        user_prompt = (
            "Evaluate relevant detection rules for the following log description:\n"
            f"{log_description}"
        )

        
        # Execute RAG
        response = rag_service.query_rag(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            filter_category="sigma_rules",
            top_k=5
        )

        context_docs = response.get("context", [])
        if not context_docs or all(not (c and c.get("content")) for c in context_docs):
            self.log_info("No relevant detection rules found in RAG context.")
            return {
                "success": True,
                "found": False,
                "detection_rules": [],
                "context": context_docs,
                "error": None
            }

        if not response["success"]:
            self.log_error(f"RAG service failure: {response.get('error')}")
            return {
                "success": False,
                "found": False,
                "detection_rules": [],
                "context": response.get("context", []),
                "error": f"RAG service failure: {response.get('error')}"
            }

        # Parse RAG output
        try:
            content = clean_response(response["content"])
            parsed = json.loads(content)

            if isinstance(parsed, dict):
                matches = parsed.get("matches", [])
            elif isinstance(parsed, list):
                matches = parsed
            else:
                raise ValueError("Unexpected RAG output format")

            if not isinstance(matches, list):
                raise ValueError("Invalid matches format")

            

            detection_rules = []
            for match in matches:
                sigma_id = match.get("id")
                confidence =  float(match.get("confidence", 0))

                if not sigma_id or confidence < confidence_threshold:
                    continue
                
                siem_rule_docs = db_connection.query(
                    collection_name="knowledge_base",
                    filter_dict={
                        "metadata.category": f"{active_siem}_rules",
                        "sigma_id": sigma_id
                    },
                    projection={"_id": 0}
                )

                siem_rule_doc = siem_rule_docs[0] if siem_rule_docs else None
                
                detection_rules.append({
                    "sigma_id": sigma_id,
                    "confidence": confidence,
                    "reason": match.get("reason", ""),
                    "title": siem_rule_doc.get("title") if siem_rule_doc else "",
                    "siem_rule": siem_rule_doc.get("rule") if siem_rule_doc else ""
                })
            self.log_info(f"Identified {len(detection_rules)} detection rules above confidence threshold {confidence_threshold}")
            return {
                "success": True,
                "found": len(detection_rules) > 0,
                "detection_rules": detection_rules,
                "context": response.get("context", []),
                "error": None
            }

        except Exception as e:
            self.log_error(f"Detection rule parsing failed: {str(e)}", e)
            return {
                "success": False,
                "found": False,
                "detection_rules": [],
                "context": response.get("context", []),
                "error": f"Detection rule parsing failed: {str(e)} | Raw: {response.get('content')}"
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
                return splunk_service.create_config_splunk(entry_ids)
            elif active_siem == "elastic":
                return elasticsearch_service.create_config_elastic(entry_ids)
            else:
                self.log_error(f"Unsupported SIEM type: {active_siem}")
                return "# Unsupported SIEM type"
                
        except Exception as e:
            self.log_error(f"Error creating SmartLP config: {str(e)}", e)
            return f"# Error creating configuration: {str(e)}"
        
    def add_context_to_prompt(self, prompt: str):
        general_settings = settings_service.get_global_settings()
        active_siem = general_settings.get("active_siem")
        active_llm = general_settings.get("active_llm")
        active_llm_endpoint = general_settings.get("active_llm_endpoint")
        enhanced_text = f"The application currently uses SIEM: {active_siem}, LLM: {active_llm} at endpoint {active_llm_endpoint}. Based on this context, answer the following prompt accordingly."
        return enhanced_text + "\n" + prompt


# Create service instance
smartlp_service = SmartLPService()