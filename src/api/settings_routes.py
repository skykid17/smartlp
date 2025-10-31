"""
Settings API routes for SmartSOC.
"""

from flask import Flask, render_template, request, jsonify

from services.settings import settings_service
from utils.logging import app_logger


def register_settings_routes(app: Flask) -> None:
    """Register settings routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/settings")
    def settings():
        """Settings page."""
        return render_template("settings.html", page_title="SmartSOC Settings")
    
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
            
            changes_list = settings_service.update_settings(data)
            return jsonify({"changes": changes_list}), 200
            
        except Exception as e:
            return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500
    
    @app.route('/api/query_llm', methods=['POST'])
    def query_llm_route():
        """Test LLM model connectivity."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            required_fields = ['task', 'model', 'url', 'llmEndpoint']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Import here to avoid circular imports
            from services.smartlp import smartlp_service
            
            # Test the LLM model
            response, error = smartlp_service.test_llm_model(
                data['task'],
                data['model'],
                data['url'],
                data['llmEndpoint']
            )
            
            if response:
                return jsonify({"status_code": 200, "response": response}), 200
            else:
                return jsonify({"status_code": 500, "error": {"error": error}}), 500
                
        except Exception as e:
            return jsonify({"status_code": 500, "error": {"error": f"LLM test failed: {str(e)}"}}, 500), 500
    
    @app.route('/api/test_connection', methods=['POST'])
    def test_connection():
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
                            app_logger.log_message("log", f"Failed to get {siem} info: {str(e)}", "WARNING")
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
                    app_logger.log_message("log", f"Connection test failed for {siem}: {str(e)}", "ERROR")
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
            app_logger.log_message("log", f"Connection test failed: {str(e)}", "ERROR")
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