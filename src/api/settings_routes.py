"""
Settings API routes for SmartSOC.
"""

import logging
from flask import Flask, request, jsonify, redirect

from services.settings import settings_service
from services.llm import llm_service


logger = logging.getLogger(__name__)

def register_settings_routes(app: Flask) -> None:
    """Register settings routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/settings")
    def settings():
        """Settings page - redirect to unified dashboard (settings in modal)."""
        return redirect("/")
    
    @app.route('/api/settings', methods=['GET'])
    def get_settings_route():
        """Get all application settings."""
        try:
            all_settings = settings_service.get_all_settings()
            return jsonify(all_settings), 200
        except Exception as e:
            return jsonify({"error": f"Failed to get settings: {str(e)}"}), 500
    
    @app.route('/api/settings', methods=['PUT'])
    def save_settings():
        """Save application settings."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Expect structure like:
            # {
            #   "globalSettings": {...},
            #   "siems": {...},
            #   "llmEndpoints": {...},
            #   "llmModels": {...}
            # }
            changes_list = settings_service.update_settings(data)
            return jsonify({"changes": changes_list}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500
    
    @app.route('/api/test_llm_connection', methods=['POST'])
    def test_llm_connection():
        """
        Test LLM connectivity.
        Expects:
        {
            "task": "string",
            "endpoint_id": "llm endpoint id",
            "model_id": "llm model id"
        }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"status_code": 400, "error": {"error": "No data provided"}}), 400

            required_fields = ['task', 'endpoint_id', 'model_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({"status_code": 400, "error": {"error": f"Missing required field: {field}"}}), 400

            # Fetch prompt for testing
            user_prompt = settings_service.get_prompts_settings("test")

            # Fetch endpoint & model details from settings
            llm_endpoint = settings_service.get_llm_endpoints(data['endpoint_id'])
            llm_model = settings_service.get_llm_models(data['model_id'])

            if not llm_endpoint:
                return jsonify({
                    "status_code": 404,
                    "error": {"error": f"LLM endpoint '{data['endpoint_id']}' not found"}
                }), 404

            if not llm_model:
                return jsonify({
                    "status_code": 404,
                    "error": {"error": f"LLM model '{data['model_id']}' not found"}
                }), 404
            # OVERRIDE the model + URL + API key being used.
            result = llm_service.query_llm(
                user_prompt=user_prompt,
                model_override=llm_model.get('model_name'),
                url_override=llm_endpoint.get('url'),
                api_key_override=llm_endpoint.get('api_key')
            )

            return jsonify(result), (result.get("status_code") or 500)

        except Exception as e:
            logger.exception("LLM test failed")
            return jsonify({
                "status_code": 500,
                "error": {"error": f"LLM test failed: {str(e)}"}
            }), 500

    @app.route('/api/test_siem_connection', methods=['POST'])
    def test_siem_connection():
        """Test SIEM connection with comprehensive diagnostics."""
        try:
            data = request.get_json() or {}
            siem_type = data.get('siem', 'all')
            
            # Import services
            from services.siem import SIEMServiceFactory
            
            results = {}
            
            # Test all SIEMs or specific one
            siems_to_test = ['elastic', 'splunk'] if siem_type == 'all' else [siem_type]
            
            for siem in siems_to_test:
                try:
                    # Get SIEM service
                    siem_service = SIEMServiceFactory.get_service(siem)
                    if not siem_service:
                        results[siem] = {
                            "status": "error", 
                            "message": f"Unsupported SIEM type: {siem}",
                            "details": {}
                        }
                        continue
                    
                    # Test connection
                    if siem_service.test_connection():
                        # Get additional info if available
                        info = {}
                        try:
                            if siem == 'elastic':
                                if hasattr(siem_service, '_connection') and siem_service._connection:
                                    cluster_info = siem_service._connection.info()
                                    info['cluster_name'] = cluster_info.get('cluster_name', 'Unknown')
                                    info['version'] = cluster_info.get('version', {}).get('number', 'Unknown')
                                    info['tagline'] = cluster_info.get('tagline', '')
                                    info['host'] = getattr(siem_service.config, 'host', 'Unknown')
                                    # Check actual SSL verification status
                                    ssl_verified = getattr(siem_service, 'ssl_verified', False)
                                    info['ssl_verified'] = ssl_verified
                                    cert_path = getattr(siem_service.config, 'cert_path', 'Unknown')
                                    if cert_path and cert_path != 'Unknown':
                                        info['cert_path'] = cert_path
                            elif siem == 'splunk':
                                if hasattr(siem_service, '_connection') and siem_service._connection:
                                    splunk_info = siem_service._connection.info()
                                    info['version'] = splunk_info.get('version', 'Unknown')
                                    info['build'] = splunk_info.get('build', 'Unknown')
                                    info['host'] = getattr(siem_service.config, 'host', 'Unknown')
                                    info['port'] = getattr(siem_service.config, 'port', 'Unknown')
                        except Exception as e:
                            logger.warning("Failed to get %s info: %s", siem, str(e))
                            info['info_error'] = str(e)
                        
                        results[siem] = {
                            "status": "connected", 
                            "message": f"Successfully connected to {siem.upper()}",
                            "details": info
                        }
                    else:
                        # Connection failed
                        config_info = {}
                        try:
                            if hasattr(siem_service, 'config'):
                                config_info['host'] = getattr(siem_service.config, 'host', 'Unknown')
                                if siem == 'splunk':
                                    config_info['port'] = getattr(siem_service.config, 'port', 'Unknown')
                                elif siem == 'elastic':
                                    config_info['username'] = getattr(siem_service.config, 'username', 'Unknown')
                        except Exception:
                            pass
                            
                        results[siem] = {
                            "status": "failed", 
                            "message": f"Failed to connect to {siem.upper()} - check credentials and network",
                            "details": config_info
                        }
                        
                except Exception as e:
                    logger.exception("Connection test failed for %s", siem)
                    results[siem] = {
                        "status": "error", 
                        "message": f"Error testing {siem.upper()} connection: {str(e)}",
                        "details": {"error": str(e)}
                    }
            
            # Return appropriate response format
            if siem_type == 'all':
                return jsonify(results), 200
            else:
                return jsonify(results.get(siem_type, {
                    "status": "error",
                    "message": f"Unknown SIEM type: {siem_type}"
                })), 200
                
        except Exception as e:
            logger.exception("Connection test failed")
            return jsonify({
                "status": "error", 
                "message": f"Connection test failed: {str(e)}"
            }), 500
    
    @app.route('/api/test_query', methods=['POST'])
    def test_query():
        """Test SIEM query connectivity."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            required_fields = ['siem', 'searchQuery', 'searchIndex', 'entriesCount']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Import here to avoid circular imports
            from services.smartlp import smartlp_service
            
            # Test the query
            response, error = smartlp_service.test_siem_query(
                data['siem'],
                data['searchQuery'],
                data['searchIndex'],
                data['entriesCount']
            )
            
            if response:
                return jsonify({"status_code": 200}), 200
            else:
                return jsonify({"status_code": 500, "error": error}), 500
                
        except Exception as e:
            return jsonify({"error": f"Query test failed: {str(e)}"}), 500