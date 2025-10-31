"""
SmartLP (Log Parser) API routes for SmartSOC.

This module provides REST API endpoints for:
- Log entry management (CRUD operations)
- Parsing and regex matching functionality
- Report generation and statistics
- Background ingestion control
"""

import os
import uuid
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect

# Import services
from services.smartlp import smartlp_service
from utils.logging import app_logger


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
    
    @app.route("/smartlp/prefix")
    def smartlp_prefix():
        """SmartLP prefix page - redirect to unified dashboard with prefix section."""
        return redirect("/#prefix")
    
    @app.route("/smartlp/report")
    def smartlp_report():
        """SmartLP report page."""
        return render_template("smartlp_report.html", page_title="SmartSOC Log Parser Report")
    
    # SmartLP API Endpoints
    @app.route("/api/entries", methods=["GET"])
    def get_entries():
        """Get log entries with pagination and filters."""
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
            
        return jsonify({"results": paginated_results, "total_entries": total_entries}), 200

    @app.route("/api/entries", methods=["POST"])
    def create_entry():
        """Create a new log entry."""
        log = request.json.get("log")
        regex = request.json.get("regex")
        
        if not log:
            return jsonify({"message": "Log not defined"}), 400
        if not regex:
            return jsonify({"message": "Regex not defined"}), 400
        
        try:
            # Determine status by testing regex match
            status = "Matched" if re.fullmatch(regex, log) else "Unmatched"
            
            # Create new entry
            entry_data = {
                "id": str(uuid.uuid4()),
                "log": log,
                "regex": regex,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            entry_id = smartlp_service.create(entry_data)
            return jsonify({"message": f"New entry {entry_id} added to database", "id": entry_id}), 201
            
        except Exception as e:
            return jsonify({"message": f"Failed to create entry: {str(e)}"}), 500
        
    @app.route("/api/entries/<entry_id>", methods=["PUT"])
    def update_entry(entry_id):
        """Update an existing log entry."""
        try:
            to_update = request.json.copy()

            # Check if log & regex is being updated - recalculate status
            log = request.json.get("log")
            regex = request.json.get("regex")
            if log and regex:
                status = "Matched" if re.fullmatch(regex, log) else "Unmatched"
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

    @app.route("/api/entries/<entry_id>", methods=["DELETE"])
    def delete_entry(entry_id):
        """Delete a log entry."""
        try:
            success = smartlp_service.delete(entry_id)
            if success:
                return jsonify({"logger": "Entry deleted."}), 200
            else:
                return jsonify({"logger": "Entry not found."}), 404
                
        except Exception as e:
            return jsonify({"logger": f"Failed to delete entry: {str(e)}"}), 500

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
                count = smartlp_service.db.count_documents(
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

    # Prefix API Endpoints
    @app.route("/api/prefix", methods=["GET"])
    def get_prefixes():
        """Get all prefix entries."""
        try:
            prefixes = smartlp_service.get_prefixes()
            total_count = smartlp_service.get_prefix_count()
            
            return jsonify({
                "prefix": prefixes,
                "total_count": total_count,
                "retrieved_at": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            app_logger.log_message("log", f"Error retrieving prefixes: {str(e)}", "ERROR")
            return jsonify({"message": f"Failed to retrieve prefixes: {str(e)}"}), 500

    @app.route("/api/prefix", methods=["POST"])
    def add_prefix():
        """Add a new prefix entry."""
        try:
            data = request.get_json()
            if not data or not data.get('regex'):
                return jsonify({"message": "Regex is required"}), 400
            
            regex = data.get('regex')
            description = data.get('description')
            
            prefix_id = smartlp_service.add_prefix(regex, description)
            
            if prefix_id:
                return jsonify({
                    "message": "Prefix added successfully",
                    "id": prefix_id
                }), 201
            else:
                return jsonify({"message": "Failed to add prefix"}), 500
                
        except Exception as e:
            app_logger.log_message("log", f"Error adding prefix: {str(e)}", "ERROR")
            return jsonify({"message": f"Failed to add prefix: {str(e)}"}), 500

    @app.route("/api/prefix/<prefix_id>", methods=["DELETE"])
    def delete_prefix(prefix_id):
        """Delete a prefix entry."""
        try:
            success = smartlp_service.delete_prefix(prefix_id)
            
            if success:
                return jsonify({"message": "Prefix deleted successfully"}), 200
            else:
                return jsonify({"message": "Prefix not found"}), 404
                
        except Exception as e:
            app_logger.log_message("log", f"Error deleting prefix: {str(e)}", "ERROR")
            return jsonify({"message": f"Failed to delete prefix: {str(e)}"}), 500

    @app.route("/api/prefix/<prefix_id>", methods=["PUT"])
    def update_prefix(prefix_id):
        """Update a prefix entry."""
        try:
            data = request.get_json()
            if not data or not data.get('regex'):
                return jsonify({"message": "Regex is required"}), 400
            
            regex = data.get('regex')
            description = data.get('description')
            
            success = smartlp_service.update_prefix(prefix_id, regex, description)
            
            if success:
                return jsonify({"message": "Prefix updated successfully"}), 200
            else:
                return jsonify({"message": "Prefix not found"}), 404
                
        except Exception as e:
            app_logger.log_message("log", f"Error updating prefix: {str(e)}", "ERROR")
            return jsonify({"message": f"Failed to update prefix: {str(e)}"}), 500

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
            from services.settings import settings_service
            settings = settings_service.get_global_settings()
            
            # Get ingestion status information
            is_running = smartlp_service._ingestion_running
            is_enabled = settings.get('ingestOn', False)
            active_siem = settings.get('activeSiem', 'elastic')
            frequency = settings.get('ingestFrequency', 30)
            
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
            config_content = smartlp_service.create_rule_config(entry_ids)
            
            # Determine filename based on active SIEM
            from services.settings import settings_service
            settings = settings_service.get_global_settings()
            active_siem = settings.get('activeSiem', 'elastic')
            
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
    
    # Elasticsearch Deployment Endpoints
    @app.route('/api/smartlp/deploy/elasticsearch', methods=['POST'])
    def deploy_to_elasticsearch():
        """Deploy SmartLP entries to Elasticsearch as Logstash pipeline."""
        try:
            data = request.get_json()
            if not data or 'ids' not in data:
                return jsonify({"error": "Entry IDs are required"}), 400
            
            entry_ids = data.get('ids', [])
            if not entry_ids:
                return jsonify({"error": "At least one entry ID is required"}), 400
            
            pipeline_id = data.get('pipeline_id')  # Optional custom pipeline ID
            
            # Deploy to Elasticsearch
            success, message = smartlp_service.deploy_to_elasticsearch(entry_ids, pipeline_id)
            
            if success:
                app_logger.log_message("log", f"Elasticsearch deployment successful: {message}", "INFO")
                return jsonify({
                    "success": True,
                    "message": message,
                    "pipeline_id": pipeline_id or os.getenv('ELASTIC_PIPELINE_ID', 'smartsoc-smartlp-pipeline'),
                    "entries_deployed": len(entry_ids)
                }), 200
            else:
                app_logger.log_message("log", f"Elasticsearch deployment failed: {message}", "ERROR")
                return jsonify({
                    "success": False,
                    "error": message
                }), 500
                
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            app_logger.log_message("log", error_msg, "ERROR")
            return jsonify({"error": error_msg}), 500
    
    @app.route('/api/smartlp/pipelines/elasticsearch', methods=['GET'])
    def list_elasticsearch_pipelines():
        """List all Elasticsearch Logstash pipelines."""
        try:
            pipelines, error = smartlp_service.list_elasticsearch_pipelines()
            
            if error:
                return jsonify({"error": error}), 500
            
            # Format pipeline data for frontend
            pipeline_list = []
            if pipelines:
                for pipeline_id, pipeline_data in pipelines.items():
                    pipeline_info = {
                        "id": pipeline_id,
                        "description": pipeline_data.get("description", ""),
                        "last_modified": pipeline_data.get("last_modified", ""),
                        "username": pipeline_data.get("username", ""),
                        "settings": pipeline_data.get("pipeline_settings", {}),
                        "metadata": pipeline_data.get("pipeline_metadata", {})
                    }
                    pipeline_list.append(pipeline_info)
            
            return jsonify({
                "pipelines": pipeline_list,
                "total_count": len(pipeline_list)
            }), 200
            
        except Exception as e:
            error_msg = f"Error listing pipelines: {str(e)}"
            app_logger.log_message("log", error_msg, "ERROR")
            return jsonify({"error": error_msg}), 500
    
    @app.route('/api/smartlp/pipelines/elasticsearch/<pipeline_id>', methods=['GET'])
    def get_elasticsearch_pipeline(pipeline_id):
        """Get details of a specific Elasticsearch Logstash pipeline."""
        try:
            pipeline_data, error = smartlp_service.get_elasticsearch_pipeline(pipeline_id)
            
            if error:
                return jsonify({"error": error}), 404 if "not found" in error.lower() else 500
            
            return jsonify({
                "pipeline": {
                    "id": pipeline_id,
                    "description": pipeline_data.get("description", ""),
                    "last_modified": pipeline_data.get("last_modified", ""),
                    "username": pipeline_data.get("username", ""),
                    "pipeline_config": pipeline_data.get("pipeline", ""),
                    "settings": pipeline_data.get("pipeline_settings", {}),
                    "metadata": pipeline_data.get("pipeline_metadata", {})
                }
            }), 200
            
        except Exception as e:
            error_msg = f"Error getting pipeline: {str(e)}"
            app_logger.log_message("log", error_msg, "ERROR")
            return jsonify({"error": error_msg}), 500
    
    @app.route('/api/smartlp/pipelines/elasticsearch/<pipeline_id>', methods=['DELETE'])
    def delete_elasticsearch_pipeline(pipeline_id):
        """Delete a specific Elasticsearch Logstash pipeline."""
        try:
            success, message = smartlp_service.delete_elasticsearch_pipeline(pipeline_id)
            
            if success:
                app_logger.log_message("log", f"Pipeline deletion successful: {message}", "INFO")
                return jsonify({
                    "success": True,
                    "message": message,
                    "pipeline_id": pipeline_id
                }), 200
            else:
                app_logger.log_message("log", f"Pipeline deletion failed: {message}", "ERROR")
                return jsonify({
                    "success": False,
                    "error": message
                }), 500
                
        except Exception as e:
            error_msg = f"Error deleting pipeline: {str(e)}"
            app_logger.log_message("log", error_msg, "ERROR")
            return jsonify({"error": error_msg}), 500