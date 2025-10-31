"""
SmartUC (Use Case) API routes for SmartSOC.

This module handles routing for SmartUC functionality including:
- Sigma rule management and browsing
- MITRE ATT&CK Navigator integration
- Rule content and SIEM rule retrieval APIs
"""

import json
from flask import Flask, render_template, request, jsonify
from bson import json_util

# Import services
from services.smartuc import smartuc_service
from utils.logging import app_logger


def register_smartuc_routes(app: Flask) -> None:
    """Register SmartUC routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/smartuc")
    def smartuc():
        """SmartUC main page with rules, search, filters, and pagination."""
        # Get request parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', None, type=str)
        main_type_filter = request.args.get('main_type', 'all', type=str)
        sub_type_filter = request.args.get('sub_type', 'all', type=str)
        
        # Get data from service
        data = smartuc_service.get_rules_with_pagination(
            page=page,
            per_page=per_page,
            search_query=search_query,
            main_type_filter=main_type_filter,
            sub_type_filter=sub_type_filter
        )
        
        # Add page title
        data['page_title'] = "SmartSOC Use Case"
        
        return render_template('smartuc.html', **data)
    
    @app.route('/smartuc/rule/<rule_id>')
    def rule_detail(rule_id):
        """SmartUC rule detail page."""
        rule = smartuc_service.get_rule_by_id(rule_id)
        if not rule:
            return "Rule not found", 404
        
        rule_json = json_util.dumps(rule)
        return render_template('smartuc_rule_detail.html',
                               rule=rule_json,
                               page_title="Rule Detail")
    
    @app.route('/smartuc/attacknavigator')
    def attacknavigator():
        """SmartUC attack navigator page."""
        data = smartuc_service.get_attack_navigator_data()
        data['page_title'] = "Attack Navigator"
        return render_template('smartuc_attacknavigator.html', **data)
    
    # SmartUC API Endpoints
    @app.route('/api/rule/<rule_id>/content', methods=['GET'])
    def api_rule_content(rule_id):
        """Get rule content by ID."""
        try:
            rule = smartuc_service.get_rule_by_id(rule_id)
            if not rule:
                return jsonify({"error": "Rule not found"}), 404
                
            # Try different possible field names for rule content
            content = None
            
            # First try string fields
            if rule.get('original_content'):
                content = rule.get('original_content')
            elif rule.get('rule_content'):
                content = rule.get('rule_content') 
            elif rule.get('raw_content'):
                content = rule.get('raw_content')
            elif rule.get('yaml_content'):
                content = rule.get('yaml_content')
            elif rule.get('content'):
                content = rule.get('content')
            elif rule.get('detection'):
                # If detection is a dict, format it as YAML-like content
                detection = rule.get('detection')
                if isinstance(detection, dict):
                    import json
                    content = f"# Sigma Rule Detection Logic\n\n{json.dumps(detection, indent=2)}"
                else:
                    content = str(detection)
            else:
                content = 'Rule content not available'
            
            title = rule.get('title', 'Rule Content')
            
            return jsonify({
                "content": content,
                "title": title
            })
        except Exception as e:
            return jsonify({"error": f"Failed to get rule content: {str(e)}"}), 500
    
    @app.route('/api/rule/<rule_id>/<active_siem>', methods=['GET'])
    def api_siem_rule(rule_id, active_siem):
        """Get SIEM rule for a specific Sigma rule.
        
        Args:
            rule_id: Sigma rule identifier
            active_siem: SIEM type (splunk, elastic, qradar)
            
        Returns:
            JSON response with SIEM rule content
        """
        try:
            # Map SIEM type to collection with validation
            siem_collections = {
                'splunk': 'splunk_rules',
                'elastic': 'elastic_rules', 
                'qradar': 'qradar_rules'
            }
            
            active_siem_lower = active_siem.lower()
            collection = siem_collections.get(active_siem_lower)
            if not collection:
                return jsonify({
                    "error": f"Invalid SIEM type: {active_siem}. Supported types: {list(siem_collections.keys())}"
                }), 400
            
            # Get SIEM rule using service
            rule = smartuc_service.get_siem_rule(collection, rule_id)
            if not rule:
                return jsonify({"error": f"SIEM rule not found for {active_siem}"}), 404
            
            # Extract content with multiple field name attempts
            content_fields = ['rule_content', 'content', 'rule', 'query', 'search', 'detection']
            content = None
            
            for field in content_fields:
                if field in rule and rule[field]:
                    content = rule[field]
                    break
            
            if content is None:
                content = 'Rule content not available'
            
            # If content is a dict, serialize it as JSON
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
                
            return jsonify(content)
            
        except Exception as e:
            app_logger.log_message("log", f"Error in api_siem_rule: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to get SIEM rule: {str(e)}"}), 500
    
    @app.route('/api/rule', methods=['GET'])
    def api_rules():
        """Get rules with pagination and filters."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_query = request.args.get('search', None, type=str)
        main_type_filter = request.args.get('main_type', 'all', type=str)
        sub_type_filter = request.args.get('sub_type', 'all', type=str)
        
        try:
            # Get data from service
            data = smartuc_service.get_rules_with_pagination(
                page=page,
                per_page=per_page,
                search_query=search_query,
                main_type_filter=main_type_filter,
                sub_type_filter=sub_type_filter
            )
            
            rules_json = json_util.dumps(data['rules'])
            
            return jsonify({
                "rules": json.loads(rules_json),
                "total_rules": data['total_rules'],
                "page": page,
                "per_page": per_page,
                "filters": {
                    "search": search_query,
                    "main_type": main_type_filter,
                    "sub_type": sub_type_filter
                }
            })
        except Exception as e:
            return jsonify({
                "rules": [],
                "total_rules": 0,
                "page": page,
                "per_page": per_page,
                "error": f"Failed to get rules: {str(e)}"
            }), 500
    
    @app.route('/api/rule/configs', methods=['GET'])
    def get_multiple_config_fields():
        """Get config information for multiple Sigma rules by IDs."""
        try:
            ids_param = request.args.get('ids', '')
            if not ids_param:
                return jsonify({"error": "Rule IDs are required"}), 400
            
            # Parse comma-separated IDs
            rule_ids = [id.strip() for id in ids_param.split(',') if id.strip()]
            if not rule_ids:
                return jsonify({"error": "At least one valid rule ID is required"}), 400
            
            # Get active SIEM from settings
            from services.settings import settings_service
            settings = settings_service.get_global_settings()
            active_siem = settings.get('activeSiem', 'elastic')
            
            # Get configuration data using service method
            config_data = smartuc_service.get_config_data_by_ids(active_siem, rule_ids)
            
            if config_data is None:
                return jsonify({"error": "Failed to retrieve configuration data"}), 500
            
            return jsonify({"data": config_data})
            
        except Exception as e:
            app_logger.log_message("log", f"Error in get_multiple_config_fields: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to get config: {str(e)}"}), 500
    
    @app.route('/api/rule/<rule_id>/config', methods=['GET'])
    def get_config_fields(rule_id):
        """Get config information for a specific Sigma rule."""
        try:
            rule = smartuc_service.get_rule_by_id(rule_id)
            if not rule:
                return jsonify({"error": "Rule not found"}), 404
                
            # Extract configuration fields from the rule
            config_fields = {
                "id": rule.get("_id"),
                "title": rule.get("title"),
                "status": rule.get("status"),
                "level": rule.get("level"),
                "logsource": rule.get("logsource", {}),
                "tags": rule.get("tags", []),
                "references": rule.get("references", [])
            }
            
            return jsonify(config_fields)
        except Exception as e:
            return jsonify({"error": f"Failed to get config: {str(e)}"}), 500
    
    @app.route('/api/rule/<rule_id>/config', methods=['PATCH'])
    def update_config_field(rule_id):
        """Update config field for a specific Sigma rule."""
        try:
            data = request.get_json()
            if not data or not isinstance(data, list):
                return jsonify({"error": "Invalid request format. Expected array of [field, value] pairs"}), 400
            
            # Get active SIEM from settings
            from services.settings import settings_service
            settings = settings_service.get_global_settings()
            active_siem = settings.get('activeSiem', 'elastic')
            
            # Determine the target collection based on SIEM type
            if active_siem == 'splunk':
                collection = 'splunk_rules'
            elif active_siem == 'elastic':
                collection = 'elastic_rules'
            else:
                return jsonify({"error": f"Unsupported SIEM type: {active_siem}"}), 400
            
            # Process each field update
            update_data = {}
            for change in data:
                if len(change) != 2:
                    continue
                field, value = change
                update_data[field] = value
            
            if not update_data:
                return jsonify({"error": "No valid field updates provided"}), 400
            
            # Update the SIEM rule using the sigma_id
            result = smartuc_service.db.update_one(
                collection,
                {'sigma_id': rule_id},
                {'$set': update_data}
            )
            
            if result.matched_count == 0:
                # If no existing rule, create a new one
                new_rule = {'sigma_id': rule_id, **update_data}
                smartuc_service.db.insert_one(collection, new_rule)
                app_logger.log_message("log", f"Created new {active_siem} rule for sigma_id: {rule_id}", "INFO")
            else:
                app_logger.log_message("log", f"Updated {active_siem} rule for sigma_id: {rule_id}", "INFO")
            
            return jsonify({"success": True, "updated_fields": list(update_data.keys())})
            
        except Exception as e:
            app_logger.log_message("log", f"Error updating config field: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to update config: {str(e)}"}), 500
    
    @app.route('/api/smartuc/generate_config', methods=['POST'])
    def generate_smartuc_config():
        """Generate configuration file for SmartUC rules."""
        try:
            data = request.get_json()
            if not data or 'ids' not in data:
                return jsonify({"error": "Rule IDs are required"}), 400
            
            rule_ids = data.get('ids', [])
            if not rule_ids:
                return jsonify({"error": "At least one rule ID is required"}), 400
            
            # Generate the configuration using the service
            config_content = smartuc_service.create_rule_config(rule_ids)
            
            # Determine filename based on active SIEM
            from services.settings import settings_service
            settings = settings_service.get_global_settings()
            active_siem = settings.get('activeSiem', 'elastic')
            
            if active_siem == 'splunk':
                filename = f"savedsearches_{len(rule_ids)}_rules.conf"
            else:
                filename = f"detection_rules_{len(rule_ids)}_rules.json"
            
            return jsonify({
                "config": config_content,
                "filename": filename,
                "siem": active_siem
            })
            
        except Exception as e:
            app_logger.log_message("log", f"Error generating SmartUC config: {str(e)}", "ERROR")
            return jsonify({"error": f"Failed to generate config: {str(e)}"}), 500