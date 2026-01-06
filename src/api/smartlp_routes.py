"""
SmartLP (Log Parser) API routes for SmartSOC.

This module provides REST API endpoints for:
- Log entry management (CRUD operations)
- Parsing and regex matching functionality
- Report generation and statistics
- Background ingestion control
"""

import pcre2
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect

# Import services
from services.smartlp import smartlp_service
from services.siem import elasticsearch_service, splunk_service
from services.settings import settings_service
from services.llm import llm_service
from services.rag import rag_service
from services.regex_engine import regex_engine_service
from utils.logging import app_logger
from database.connection import db_connection


def register_smartlp_routes(app: Flask) -> None:
    """Register SmartLP routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/smartlp")
    def smartlp():
        """SmartLP main page - redirect to unified dashboard."""
        return redirect("/")
    
    @app.route("/smartlp/parser")
    def smartlp_parser():
        """SmartLP parser page - redirect to unified dashboard with parser section."""
        return redirect("/#parser")
    
    @app.route("/smartlp/report")
    def smartlp_report():
        """SmartLP report page."""
        return render_template("smartlp_report.html", page_title="SmartSOC Log Parser Report")

    @app.route("/api/smartlp/entries", methods=["GET"])
    def get_smartlp_entries():
        """Alias for frontend dashboard requests."""
        search_id = request.args.get('search_id', '', type=str)
        search_log = request.args.get('search_log', '', type=str)
        search_regex = request.args.get('search_regex', '', type=str)
        filter_status = request.args.get('filter_status', '', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)

        # Build search filters
        search_filters = {}
        if search_id:
            search_filters['search_id'] = search_id
        if search_log:
            search_filters['search_log'] = search_log
        if search_regex:
            search_filters['search_regex'] = search_regex
        if filter_status:
            search_filters['filter_status'] = filter_status

        # Get entries from the database
        paginated_results, total_entries = smartlp_service.get_entries(
            page=page, 
            per_page=per_page, 
            search_filters=search_filters if search_filters else None
        )
        return jsonify({"entries": paginated_results, "total": total_entries}), 200
    
    @app.route("/api/smartlp/entries/<entry_id>", methods=["PUT", "PATCH"])
    def update_entry(entry_id):
        """Update an existing log entry."""
        try:
            to_update = request.json.copy()

            # Check if log & regex is being updated - recalculate status
            log = request.json.get("log")
            regex = request.json.get("regex")
            if log and regex:
                status = "Matched" if pcre2.fullmatch(regex, log) else "Unmatched"
                to_update["status"] = status
                
            # Update timestamp
            to_update["last_modified"] = datetime.utcnow().isoformat()
            
            success = smartlp_service.update(entry_id, to_update)
            if success:
                return jsonify({"message": f"Entry {entry_id} updated in database"})
            else:
                return jsonify({"message": f"No entry {entry_id} with such id found"}), 404
                
        except Exception as e:
            return jsonify({"message": f"Failed to update entry: {str(e)}"}), 500

    @app.route("/api/smartlp/entries/delete", methods=["POST"])
    def delete_entries_bulk():
        """Delete multiple log entries (frontend bulk action)."""
        try:
            payload = request.get_json() or {}
            ids = payload.get('ids', [])
            if not ids:
                return jsonify({"success": False, "message": "No entry IDs provided"}), 400

            deleted = 0
            for entry_id in ids:
                try:
                    if smartlp_service.delete(entry_id):
                        deleted += 1
                except Exception:
                    continue

            return jsonify({
                "success": True,
                "deleted": deleted,
                "requested": len(ids)
            }), 200
        except Exception as e:
            app_logger.log_message("log", f"Bulk delete failed: {str(e)}", "ERROR")
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route("/api/entries/oldest", methods=["GET"])
    def get_oldest_unmatched_entry():
        """Get the oldest unmatched entry from database.
        
        Returns:
            JSON response with entry data or error message
        """
        try:
            app_logger.log_message("log", "API request for oldest unmatched entry", "INFO")
            
            entry = smartlp_service.get_oldest_unmatched_entry()
            if entry:
                # Add additional metadata
                response_data = {
                    **entry,  # Include all entry fields
                    "total_unmatched": smartlp_service.get_unmatched_entries_count(),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                app_logger.log_message("log", f"Returned oldest unmatched entry: {entry.get('id', 'unknown')}", "INFO")
                return jsonify(response_data), 200
            else:
                app_logger.log_message("log", "No unmatched entries found in database", "INFO")
                return jsonify({
                    "message": "No unmatched entries found", 
                    "total_unmatched": 0,
                    "retrieved_at": datetime.utcnow().isoformat()
                }), 404
                
        except Exception as e:
            app_logger.log_message("log", f"Error retrieving oldest entry: {str(e)}", "ERROR")
            return jsonify({
                "message": f"Failed to retrieve oldest entry: {str(e)}",
                "error_at": datetime.utcnow().isoformat()
            }), 500

    @app.route('/api/find_match', methods=['POST'])
    def find_match():
        payload = request.get_json() or {}
        log_text = payload.get("log", "")
        pattern = payload.get("regex", "")

        if not pattern:
            return jsonify({
                "status": "Error",
                "error": "No regex provided",
                "full": None,
                "groups": []
            }), 200

        result = regex_engine_service.run_regex_match(log_text, pattern)
        return jsonify(result), 200
    
    @app.route('/api/reduce_regex', methods=['POST'])
    def reduce_regex():
        data = request.get_json()
        log_text = data.get("log", "")
        regex = data.get("regex", "")

        results = regex_engine_service.run_reduce_regex(log_text, regex)
        return jsonify(results), 200


    @app.route("/api/entries/stats", methods=["GET"])
    def get_entry_statistics():
        """Get SmartLP entry statistics.
        
        Returns:
            JSON response with entry counts and statistics
        """
        try:
            unmatched_count = smartlp_service.get_unmatched_entries_count()
            all_statuses = smartlp_service.get_all_statuses()
            
            # Get count for each status
            status_counts = {}
            for status in all_statuses:
                count = db_connection.count_documents(
                    smartlp_service.collection_name,
                    {"status": status}
                )
                status_counts[status] = count
            
            total_entries = sum(status_counts.values())
            
            statistics = {
                "total_entries": total_entries,
                "unmatched_count": unmatched_count,
                "status_counts": status_counts,
                "available_statuses": all_statuses,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return jsonify(statistics), 200
            
        except Exception as e:
            app_logger.log_message("log", f"Error getting entry statistics: {str(e)}", "ERROR")
            return jsonify({"message": f"Failed to get statistics: {str(e)}"}), 500

    @app.route("/api/report/smartlp", methods=["GET"])
    def get_report_smartlp():
        """Get SmartLP report data."""
        try:
            data = smartlp_service.get_report_data()
            return jsonify({"data": data, "logger": "Report generated successfully."}), 200
        except Exception as e:
            app_logger.log_message("log", f"Error generating SmartLP report: {str(e)}", "ERROR")
            return jsonify({"logger": f"Internal server error: {str(e)}"}), 500
    
    @app.route('/api/smartlp/ingestion/status', methods=['GET'])
    def get_ingestion_status():
        """Get ingestion status information."""
        try:
            settings = settings_service.get_global_settings()

            # Get ingestion status information (backend uses snake_case)
            is_running = smartlp_service._ingestion_running
            is_enabled = settings.get('ingest_on', False)
            active_siem = settings.get('active_siem', 'elastic')
            frequency = settings.get('ingest_frequency', 30)
            
            # Get recent log counts
            unmatched_count = smartlp_service.get_unmatched_entries_count()
            
            status_info = {
                "ingestion_running": is_running,
                "ingestion_enabled": is_enabled,
                "active_siem": active_siem,
                "frequency_minutes": frequency,
                "unmatched_entries": unmatched_count,
                "last_updated": datetime.now().isoformat()
            }
            
            return jsonify(status_info)
            
        except Exception as e:
            app_logger.log_message("log", f"Error getting ingestion status: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to get ingestion status: {str(e)}"}), 500
    
    @app.route('/api/smartlp/ingestion/start', methods=['POST'])
    def start_ingestion():
        """Start log ingestion manually."""
        try:
            smartlp_service.start_log_ingestion()
            return jsonify({"message": "Log ingestion started", "status": "success"})
        except Exception as e:
            app_logger.log_message("log", f"Error starting ingestion: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to start ingestion: {str(e)}"}), 500
    
    @app.route('/api/smartlp/ingestion/stop', methods=['POST'])
    def stop_ingestion():
        """Stop log ingestion manually."""
        try:
            smartlp_service.stop_log_ingestion()
            return jsonify({"message": "Log ingestion stopped", "status": "success"})
        except Exception as e:
            app_logger.log_message("log", f"Error stopping ingestion: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to stop ingestion: {str(e)}"}), 500
    
    @app.route('/api/smartlp/generate_config', methods=['POST'])
    def generate_smartlp_config():
        """Generate configuration file for SmartLP entries."""
        try:
            data = request.get_json()
            if not data or 'ids' not in data:
                return jsonify({"error": "Entry IDs are required"}), 400
            
            entry_ids = data.get('ids', [])
            if not entry_ids:
                return jsonify({"error": "At least one entry ID is required"}), 400
            
            # Generate the configuration using the service
            config_content = smartlp_service.create_config(entry_ids)
            
            settings = settings_service.get_global_settings()
            active_siem = settings.get('active_siem', 'elastic')
            
            if active_siem == 'splunk':
                filename = f"smartlp_splunk_{len(entry_ids)}_entries.conf"
            else:
                filename = f"smartlp_logstash_{len(entry_ids)}_entries.conf"
            
            return jsonify({
                "config": config_content,
                "filename": filename,
                "siem": active_siem
            })
            
        except Exception as e:
            app_logger.log_message("log", f"Error generating SmartLP config: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to generate config: {str(e)}"}), 500
    
    @app.route('/api/check_deployable', methods=['POST'])
    def check_deployable():
        """Check if entries can be deployed to SIEM.
        
        Returns information about which entries are ready for deployment
        based on their status ('Matched' entries are deployable).
        """
        try:
            data = request.get_json()
            if not data or 'ids' not in data:
                return jsonify({"message": "Entry IDs are required"}), 400
            
            ids = data.get('ids', [])
            if not ids:
                return jsonify({"message": "At least one entry ID is required"}), 400
            
            # Get status for all requested entries
            status_map = smartlp_service.get_entry_status(ids)
            
            # Create detailed status info for better error messages
            non_matched_entries = []
            for entry_id in ids:
                status = status_map.get(entry_id, "Unknown")
                if status != "Matched":
                    non_matched_entries.append({"id": entry_id, "status": status})
            
            if non_matched_entries:
                response_data = {
                    "logger": "Some entries cannot be pushed to Ansible.",
                    "unmatched": non_matched_entries  # All non-"Matched" entries with their statuses
                }
                return jsonify(response_data), 200
            
            return jsonify({"logger": "Entries are ready for deployment."}), 200
            
        except Exception as e:
            app_logger.log_message("log", f"Error checking deployable status: {str(e)}", "ERROR")
            return jsonify({"message": f"Failed to check deployable status: {str(e)}"}), 500
    
    @app.route('/api/smartlp/deploy_config', methods=['POST'])
    def deploy_config():
        """Deploy SmartLP entries to the active SIEM."""
        try:
            data = request.get_json()
            if not data or 'ids' not in data:
                return jsonify({"error": "Entry IDs are required"}), 400
            
            entry_ids = data.get('ids', [])
            if not entry_ids:
                return jsonify({"error": "At least one entry ID is required"}), 400

            # Get active SIEM
            active_siem = settings_service.get_active_siem()
            if not active_siem:
                return jsonify({"error": "No active SIEM configured"}), 400
            config = data.get('config', None)
            # Deploy to SIEM
            if active_siem == 'splunk':
                success, message = splunk_service.deploy_config_splunk(entry_ids)
            else: # elastic
                
                if not config:
                    return jsonify({"error": "Configuration is required for Elasticsearch deployment"}), 400
                success, message = elasticsearch_service.deploy_config_elastic(config)
            
            if success:
                app_logger.log_message("log", f"SIEM deployment successful: {message}", "INFO")
                # # update status of entries to 'Deployed'
                for entry_id in entry_ids:
                    smartlp_service.update(entry_id, {"status": "Deployed", "last_modified": datetime.utcnow().isoformat()})
                return jsonify({
                    "success": True,
                    "message": message,
                    "siem": active_siem,
                    "entries_deployed": len(entry_ids)
                }), 200
            else:
                app_logger.log_message("log", f"SIEM deployment failed: {message}", "ERROR")
                return jsonify({
                    "success": False,
                    "error": message
                }), 500
                
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            app_logger.log_message("log", error_msg, "ERROR")
            return jsonify({"error": error_msg}), 500
    
    @app.route('/api/smartlp/deploy_rule', methods=['POST'])
    def deploy_rule():
        """Deploy a single SmartLP entry as a rule to the active SIEM."""
        try:
            data = request.get_json()
            if not data or 'id' not in data:
                return jsonify({"error": "Entry ID is required"}), 400
            
            entry_id = data.get('id')
            if not entry_id:
                return jsonify({"error": "Entry ID cannot be empty"}), 400

            # Get the entry from database
            entry = smartlp_service.get_by_id(entry_id)
            if not entry:
                return jsonify({"error": f"No entry found with ID {entry_id}"}), 404
            
            # Get active SIEM
            active_siem = settings_service.get_active_siem()
            if not active_siem:
                return jsonify({"error": "No active SIEM configured"}), 400

            rule = elasticsearch_service.create_rule_elastic(data)

            # Deploy to SIEM
            if active_siem == 'splunk':
                rule = splunk_service.create_rule_splunk(data)
                success, message = splunk_service.deploy_rule_splunk(rule)
            else: # elastic
                rule = elasticsearch_service.create_rule_elastic(data)
                success, message = elasticsearch_service.deploy_rule_elastic(rule)
            
            if success:
                app_logger.log_message("log", f"SIEM rule deployment successful: {message}", "INFO")
                # update status of entry to 'Deployed'
                smartlp_service.update(entry_id, {"status": "Deployed", "last_modified": datetime.utcnow().isoformat()})
                return jsonify({
                    "success": True,
                    "message": message,
                    "siem": active_siem,
                    "rule_deployed": rule.get("rule_id")
                }), 200
            else:
                app_logger.log_message("log", f"SIEM rule deployment failed: {message}", "ERROR")
                return jsonify({
                    "success": False,
                    "error": message
                }), 500
                
        except Exception as e:
            error_msg = f"Rule deployment error: {str(e)}"
            app_logger.log_message("log", error_msg, "ERROR")
            return jsonify({"error": error_msg}), 500
        
    @app.route("/api/query", methods=['POST'])
    def query():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Test the LLM model
        match data['task']:
            
            case "generate":
                log = data.get('log', '')
                result = smartlp_service.generate_regex(log, 10)
            case "fix":
                log = data.get('log', '')
                regex = data.get('regex', '')
                result = smartlp_service.fix_regex(log, regex)
            case _:
                user_prompt = data.get("prompt", "").strip()
                result = rag_service.query_rag(
                    user_prompt=user_prompt,
                    system_prompt=settings_service.get_prompts_settings("general")
                )

        return jsonify(result)