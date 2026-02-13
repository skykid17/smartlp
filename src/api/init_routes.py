"""First-run initialization wizard routes."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, render_template, request, redirect

from services.settings import settings_service

logger = logging.getLogger(__name__)

SIEM_ELASTIC = "elastic"
SIEM_SPLUNK = "splunk"

DEFAULT_TEST_PROMPT = "Hello! Reply with a short confirmation."

def _required(data: Dict[str, Any], field: str) -> Optional[str]:
    value = data.get(field)
    if value is None:
        return f"Missing required field: {field}"
    if isinstance(value, str) and not value.strip():
        return f"Missing required field: {field}"
    return None


def _slugify(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "model"


def register_init_routes(app: Flask) -> None:
    @app.route("/init")
    def init_page():
        try:
            global_settings = settings_service.get_global_settings() or {}
            if bool(global_settings.get("initialized")):
                return redirect("/")
        except Exception:
            pass

        return render_template("init.html", page_title="Initialize SmartLP")

    def _block_if_initialized():
        try:
            global_settings = settings_service.get_global_settings() or {}
            if bool(global_settings.get("initialized")):
                return jsonify({"success": False, "error": "Already initialized"}), 409
        except Exception:
            return None
        return None

    @app.route("/api/init/siem/test", methods=["POST"])
    def init_siem_test():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        
        from services.siem import SIEMServiceFactory
        
        data = request.get_json() or {}
        siem = (data.get("siem") or "").strip().lower()

        if siem not in {SIEM_ELASTIC, SIEM_SPLUNK}:
            return jsonify({"success": False, "error": "Invalid SIEM type"}), 400

        if siem == SIEM_ELASTIC:
            for f in ["host", "kibana_url", "api_key", "search_index", "search_query"]:
                err = _required(data, f)
                if err:
                    return jsonify({"success": False, "error": err}), 400

            kibana_url = (data.get("kibana_url") or "").strip()
            if kibana_url and not (kibana_url.startswith("http://") or kibana_url.startswith("https://")):
                return jsonify({"success": False, "error": "kibana_url must start with http:// or https://"}), 400

            # Use service layer to test connection with config override
            siem_service = SIEMServiceFactory.get_service('elastic')
            if not siem_service:
                return jsonify({"success": False, "error": "Failed to create Elasticsearch service"}), 500
            
            ok, msg, details = siem_service.test_connection(config_override=data)
            return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)

        for f in ["host", "port", "user", "password", "search_index", "search_query", "search_entry_count"]:
            err = _required(data, f)
            if err:
                return jsonify({"success": False, "error": err}), 400

        # Use service layer to test connection with config override
        siem_service = SIEMServiceFactory.get_service('splunk')
        if not siem_service:
            return jsonify({"success": False, "error": "Failed to create Splunk service"}), 500
        
        ok, msg, details = siem_service.test_connection(config_override=data)
        return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)

    @app.route("/api/init/siem/save", methods=["POST"])
    def init_siem_save():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        
        from services.siem import SIEMServiceFactory
        
        data = request.get_json() or {}
        siem = (data.get("siem") or "").strip().lower()

        # Always re-test before saving
        test_resp = init_siem_test()
        # init_siem_test may return (response, code) or response
        if isinstance(test_resp, tuple):
            resp, code = test_resp
            if code != 200:
                return resp, code
        else:
            resp = test_resp
            if resp.status_code != 200:
                return resp

        now = datetime.now().isoformat()
        
        # Build SIEM configuration document
        if siem == SIEM_ELASTIC:
            siem_config = {
                "id": siem,
                "name": siem.upper(),
                "host": data.get("host"),
                "kibana_url": (data.get("kibana_url") or "").strip(),
                "api_key": (data.get("api_key") or "").strip(),
                "user": data.get("user") or "",
                "password": data.get("password") or "",
                "search_index": data.get("search_index"),
                "search_query": data.get("search_query"),
                "pipeline_id": "smartlp",
                "cert_path": (data.get("cert_path") or "").strip(),
            }
        else:
            siem_config = {
                "id": siem,
                "name": siem.upper(),
                "host": data.get("host"),
                "port": str(data.get("port")),
                "user": data.get("user"),
                "password": data.get("password"),
                "search_index": data.get("search_index"),
                "search_query": data.get("search_query"),
                "search_entry_count": int(data.get("search_entry_count")),
            }
        
        # Use settings_service to save configuration
        settings_service.update_settings({
            "siem_config": siem_config,
            "active_siem": siem
        })

        return jsonify({"success": True}), 200

    @app.route("/api/init/llm/test", methods=["POST"])
    def init_llm_test():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        
        from services.llm import llm_service
        
        data = request.get_json() or {}
        endpoint_url = (data.get("endpoint_url") or "").strip()
        api_key = (data.get("api_key") or "").strip()
        model_name = (data.get("model_name") or "").strip()

        if not endpoint_url:
            return jsonify({"success": False, "error": "Missing required field: endpoint_url"}), 400

        if not model_name:
            return jsonify({"success": False, "error": "Missing required field: model_name"}), 400

        test_prompt = settings_service.get_prompts_settings("test") or DEFAULT_TEST_PROMPT

        # Use service layer to test connection
        ok, msg, details = llm_service.test_connection(endpoint_url, model_name, api_key, test_prompt)
        return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)

    @app.route("/api/init/llm/save", methods=["POST"])
    def init_llm_save():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        data = request.get_json() or {}

        # Always re-test before saving
        test_resp = init_llm_test()
        if isinstance(test_resp, tuple):
            resp, code = test_resp
            if code != 200:
                return resp, code
        else:
            resp = test_resp
            if resp.status_code != 200:
                return resp

        provider = (data.get("provider") or "").strip().lower()
        endpoint_url = (data.get("endpoint_url") or "").strip()
        api_key = (data.get("api_key") or "").strip()
        model_name = (data.get("model_name") or "").strip()

        if not provider:
            return jsonify({"success": False, "error": "Missing required field: provider"}), 400

        endpoint_id = f"{provider}"
        model_id = f"{provider}-{_slugify(model_name)}"

        # Use settings_service to save LLM endpoint and model
        settings_service.update_settings({
            "llm_endpoints": {
                endpoint_id: {
                    "id": endpoint_id,
                    "name": provider,
                    "url": endpoint_url,
                    "api_key": api_key or "",
                }
            },
            "llm_models": {
                model_id: {
                    "id": model_id,
                    "model_name": model_name,
                    "display_name": model_name,
                    "endpoint_id": endpoint_id,
                    "provider": provider,
                }
            },
            "active_llm_model_id": model_id
        })

        return jsonify({"success": True, "model_id": model_id, "endpoint_id": endpoint_id}), 200

    @app.route("/api/init/finish", methods=["POST"])
    def init_finish():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        
        global_settings = settings_service.get_global_settings() or {}

        active_siem = global_settings.get("active_siem")
        active_llm_model_id = global_settings.get("active_llm_model_id")

        if not active_siem:
            return jsonify({"success": False, "error": "Active SIEM not set"}), 400

        if not active_llm_model_id:
            return jsonify({"success": False, "error": "Active LLM model not set"}), 400

        # Verify SIEM and LLM configurations exist
        siem_settings = settings_service.get_siem_settings()
        siem_ids = {s.get('id') for s in siem_settings}
        
        if active_siem not in siem_ids:
            return jsonify({"success": False, "error": "SIEM settings not saved"}), 400
        
        llm_model = settings_service.get_llm_models(active_llm_model_id)
        if not llm_model:
            return jsonify({"success": False, "error": "LLM settings not saved"}), 400

        # Re-test SIEM connection before finalizing initialization
        try:
            from services.siem import splunk_service, elasticsearch_service

            if active_siem == "splunk":
                siem_ok, siem_msg, _ = splunk_service.test_connection()
            elif active_siem == "elastic":
                siem_ok, siem_msg, _ = elasticsearch_service.test_connection()
            else:
                siem_ok, siem_msg = False, "Unknown SIEM type"

            if not siem_ok:
                return jsonify({
                    "success": False,
                    "error": f"SIEM connection test failed: {siem_msg}",
                    "category": "siem"
                }), 400
        except Exception as e:
            logger.exception("Error testing SIEM connection during initialization")
            return jsonify({
                "success": False,
                "error": f"SIEM connection test error: {str(e)}",
                "category": "siem"
            }), 500

        # Re-test LLM connection before finalizing initialization
        try:
            from services.llm import llm_service

            endpoint_id = llm_model.get("endpoint_id")
            endpoint_doc = settings_service.get_llm_endpoints(endpoint_id)

            if endpoint_doc:
                test_prompt = settings_service.get_prompts_settings("test") or "Hello! Reply with a short confirmation."
                llm_ok, llm_msg, _ = llm_service.test_connection(
                    endpoint_doc.get("url"),
                    llm_model.get("model_name"),
                    endpoint_doc.get("api_key", ""),
                    test_prompt
                )
                if not llm_ok:
                    return jsonify({
                        "success": False,
                        "error": f"LLM connection test failed: {llm_msg}",
                        "category": "llm"
                    }), 400
        except Exception as e:
            logger.exception("Error testing LLM connection during initialization")
            return jsonify({
                "success": False,
                "error": f"LLM connection test error: {str(e)}",
                "category": "llm"
            }), 500

        # Mark system as initialized
        settings_service.update_settings({
            "initialized": True
        })

        # Dynamically register SmartLP routes now that initialization is complete
        try:
            from flask import current_app
            from core.app_factory import ApplicationFactory

            ApplicationFactory._register_smartlp_routes_safe(current_app)
            logger.info("SmartLP routes registered after initialization")
        except Exception as e:
            logger.exception("Failed to register SmartLP routes after init")
            # Don't fail the request - routes will be registered on next request via hook

        return jsonify({"success": True}), 200
