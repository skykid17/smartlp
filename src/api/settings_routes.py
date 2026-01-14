"""
Settings API routes for SmartSOC.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from flask import Flask, request, jsonify, redirect

from services.settings import settings_service
from services.llm import llm_service
from database.connection import db_connection


logger = logging.getLogger(__name__)


def _required(data: Dict[str, Any], field: str) -> Optional[str]:
    value = data.get(field)
    if value is None:
        return f"Missing required field: {field}"
    if isinstance(value, str) and not value.strip():
        return f"Missing required field: {field}"
    return None


def _refresh_siem_runtime_cache() -> None:
    """Refresh cached SIEM settings/services after a settings write."""
    try:
        from config.environment import env_manager

        # Clear cached dataclass snapshots
        if hasattr(env_manager, '_splunk_settings'):
            env_manager._splunk_settings = None
        if hasattr(env_manager, '_elastic_settings'):
            env_manager._elastic_settings = None

        # Refresh any module-level singleton services (if imported)
        try:
            from services import siem as siem_module

            if hasattr(siem_module, 'splunk_service'):
                siem_module.splunk_service.settings = env_manager.splunk
                siem_module.splunk_service._connection = None

            if hasattr(siem_module, 'elasticsearch_service'):
                siem_module.elasticsearch_service.settings = env_manager.elastic
                siem_module.elasticsearch_service._connection = None
                siem_module.elasticsearch_service.ssl_verified = False
        except Exception:
            pass

    except Exception:
        # Best-effort only.
        return

def register_settings_routes(app: Flask) -> None:
    """Register settings routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/settings")
    def settings():
        """Settings page - redirect to unified dashboard (settings in modal)."""
        return redirect("/")

    @app.route('/api/settings/global', methods=['GET'])
    def get_global_settings_route():
        """Get global settings (single document)."""
        try:
            settings = settings_service.get_global_settings() or {}
            return jsonify(settings), 200
        except Exception as e:
            return jsonify({"error": f"Failed to get global settings: {str(e)}"}), 500
    
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
                    
                    # Test connection (no config_override, use saved settings)
                    success, message, details = siem_service.test_connection()
                    
                    if success:
                        results[siem] = {
                            "status": "connected", 
                            "message": message,
                            "details": details
                        }
                    else:
                        results[siem] = {
                            "status": "failed", 
                            "message": message,
                            "details": details
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

    @app.route('/api/settings/siem/test', methods=['POST'])
    def test_siem_connection_candidate():
        """Test a candidate SIEM configuration (not yet saved)."""
        try:
            from services.siem import SIEMServiceFactory
            
            data = request.get_json() or {}
            siem_type = (data.get('siem_type') or '').strip().lower()
            if siem_type not in {'elastic', 'splunk'}:
                return jsonify({"success": False, "error": "Invalid siem_type"}), 400

            if siem_type == 'elastic':
                cfg = data.get('elastic') or {}
                for f in ["host", "kibana_url", "api_key", "cert_path", "search_index", "search_query"]:
                    err = _required(cfg, f)
                    if err:
                        return jsonify({"success": False, "error": err}), 400

                kibana_url = (cfg.get("kibana_url") or "").strip()
                if kibana_url and not (kibana_url.startswith("http://") or kibana_url.startswith("https://")):
                    return jsonify({"success": False, "error": "kibana_url must start with http:// or https://"}), 400

                # Use service layer to test connection with config override
                siem_service = SIEMServiceFactory.get_service('elastic')
                if not siem_service:
                    return jsonify({"success": False, "error": "Failed to create Elasticsearch service"}), 500
                
                ok, msg, details = siem_service.test_connection(config_override=cfg)
                return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)

            cfg = data.get('splunk') or {}
            for f in ["host", "port", "user", "password", "search_index", "search_query", "search_entry_count"]:
                err = _required(cfg, f)
                if err:
                    return jsonify({"success": False, "error": err}), 400

            # Use service layer to test connection with config override
            siem_service = SIEMServiceFactory.get_service('splunk')
            if not siem_service:
                return jsonify({"success": False, "error": "Failed to create Splunk service"}), 500
            
            ok, msg, details = siem_service.test_connection(config_override=cfg)
            return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)
        except Exception as e:
            logger.exception("Candidate SIEM test failed")
            return jsonify({"success": False, "error": f"SIEM test failed: {str(e)}"}), 500

    @app.route('/api/settings/siem', methods=['POST'])
    def save_siem_settings_candidate():
        """Upsert a SIEM settings document (post-initialization add/edit)."""
        try:
            from services.siem import SIEMServiceFactory
            
            data = request.get_json() or {}
            siem_type = (data.get('siem_type') or '').strip().lower()
            if siem_type not in {'elastic', 'splunk'}:
                return jsonify({"success": False, "error": "Invalid siem_type"}), 400

            # Enforce "add missing SIEM" semantics: only allow if the SIEM doc doesn't already exist.
            existing = settings_service.get_siem_settings() or []
            existing_ids = {str(s.get('id') or '').lower() for s in existing}
            if siem_type in existing_ids:
                return jsonify({"success": False, "error": f"SIEM '{siem_type}' already exists"}), 409

            # Validate + test before saving
            if siem_type == 'elastic':
                cfg = data.get('elastic') or {}
                for f in ["host", "kibana_url", "api_key", "cert_path", "search_index", "search_query"]:
                    err = _required(cfg, f)
                    if err:
                        return jsonify({"success": False, "error": err}), 400

                kibana_url = (cfg.get("kibana_url") or "").strip()
                if kibana_url and not (kibana_url.startswith("http://") or kibana_url.startswith("https://")):
                    return jsonify({"success": False, "error": "kibana_url must start with http:// or https://"}), 400

                # Use service layer to test connection with config override
                siem_service = SIEMServiceFactory.get_service('elastic')
                if not siem_service:
                    return jsonify({"success": False, "error": "Failed to create Elasticsearch service"}), 500
                
                ok, msg, _details = siem_service.test_connection(config_override=cfg)
                if not ok:
                    return jsonify({"success": False, "error": msg}), 400

                now = datetime.now().isoformat()
                siem_doc: Dict[str, Any] = {
                    "category": "siem_settings",
                    "id": "elastic",
                    "name": "ELASTIC",
                    "updated_at": now,
                    "host": cfg.get("host"),
                    "kibana_url": (cfg.get("kibana_url") or "").strip(),
                    "api_key": (cfg.get("api_key") or "").strip(),
                    "user": (cfg.get("user") or "").strip(),
                    "password": cfg.get("password") or "",
                    "search_index": (cfg.get("search_index") or "").strip(),
                    "search_query": (cfg.get("search_query") or "").strip(),
                    "pipeline_id": "smartlp",
                    "cert_path": (cfg.get("cert_path") or "").strip(),
                }
            else:
                cfg = data.get('splunk') or {}
                for f in ["host", "port", "user", "password", "search_index", "search_query", "search_entry_count"]:
                    err = _required(cfg, f)
                    if err:
                        return jsonify({"success": False, "error": err}), 400

                # Use service layer to test connection with config override
                siem_service = SIEMServiceFactory.get_service('splunk')
                if not siem_service:
                    return jsonify({"success": False, "error": "Failed to create Splunk service"}), 500
                
                ok, msg, _details = siem_service.test_connection(config_override=cfg)
                if not ok:
                    return jsonify({"success": False, "error": msg}), 400

                now = datetime.now().isoformat()
                siem_doc = {
                    "category": "siem_settings",
                    "id": "splunk",
                    "name": "SPLUNK",
                    "updated_at": now,
                    "host": (cfg.get("host") or "").strip(),
                    "port": str(cfg.get("port") or "8089"),
                    "user": (cfg.get("user") or "").strip(),
                    "password": cfg.get("password") or "",
                    "search_index": (cfg.get("search_index") or "").strip(),
                    "search_query": (cfg.get("search_query") or "").strip(),
                    "search_entry_count": int(cfg.get("search_entry_count") or 0),
                }

            db_connection.get_collection('settings').update_one(
                {"category": "siem_settings", "id": siem_doc["id"]},
                {"$set": siem_doc},
                upsert=True,
            )

            _refresh_siem_runtime_cache()

            return jsonify({"success": True}), 200

        except Exception as e:
            logger.exception("Failed to save SIEM settings")
            return jsonify({"success": False, "error": f"Failed to save SIEM settings: {str(e)}"}), 500