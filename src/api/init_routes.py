"""First-run initialization wizard routes."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, render_template, request, redirect

from database.connection import db_connection
from services.settings import settings_service

logger = logging.getLogger(__name__)

SETTINGS_COLLECTION = "settings"

CATEGORY_GLOBAL = "global_settings"
ID_GLOBAL = "global"

CATEGORY_SIEM = "siem_settings"
SIEM_ELASTIC = "elastic"
SIEM_SPLUNK = "splunk"

CATEGORY_LLM_ENDPOINT = "llm_endpoint"
CATEGORY_LLM_MODEL = "llm_model"

ALLOWED_LLM_PROVIDERS = {"vllm", "lmstudio", "ollama", "openai"}

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


def _test_splunk(cfg: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        import splunklib.client as splunk_client
        import splunklib.results as splunk_results

        conn = splunk_client.connect(
            host=cfg["host"],
            port=str(cfg["port"]),
            username=cfg["user"],
            password=cfg["password"],
        )
        info = conn.info()
        version = info.get("version")
        build = info.get("build")

        # After successful connection, execute query validation
        search_index = cfg.get("search_index", "").strip()
        search_query = cfg.get("search_query", "").strip()
        search_entry_count = cfg.get("search_entry_count", 10)

        if not search_index or not search_query:
            return False, "Missing search_index or search_query for validation", {}

        try:
            # Convert search_entry_count to int if it's a string
            try:
                entry_count = int(search_entry_count)
            except (ValueError, TypeError):
                entry_count = 10

            # Construct search query
            search_string = f"search index={search_index} {search_query} | head {entry_count}"
            
            # Execute search
            job = conn.jobs.create(search_string)
            
            # Wait for search to complete
            while not job.is_done():
                pass
            
            # Get results and count
            result_count = 0
            for result in splunk_results.ResultsReader(job.results()):
                if isinstance(result, dict):
                    result_count += 1

            return True, "Connected and query executed successfully", {
                "version": version,
                "build": build,
                "result_count": result_count,
            }
        except Exception as query_error:
            return False, f"Query validation failed: {str(query_error)}", {}

    except Exception as e:
        return False, f"Splunk connection failed: {str(e)}", {}


def _test_elastic(cfg: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        from elasticsearch import Elasticsearch
        import json

        es_kwargs: Dict[str, Any] = {
            "request_timeout": 10,
        }

        api_key = (cfg.get("api_key") or "").strip()
        if not api_key:
            return False, "Missing required field: api_key", {}
        es_kwargs["api_key"] = api_key

        cert_path = (cfg.get("cert_path") or "").strip()
        if not cert_path:
            return False, "Missing required field: cert_path", {}

        es_kwargs["verify_certs"] = True
        es_kwargs["ca_certs"] = cert_path

        es = Elasticsearch(cfg["host"], **es_kwargs)
        info = es.info()

        cluster_name = info.get("cluster_name")
        version = (info.get("version") or {}).get("number")

        # After successful connection, execute query validation
        search_index = cfg.get("search_index", "").strip()
        search_query = cfg.get("search_query", "").strip()

        if not search_index or not search_query:
            return False, "Missing search_index or search_query for validation", {}

        # Parse query if it's a string
        try:
            query_dict = json.loads(search_query)
        except json.JSONDecodeError:
            # Treat as simple query string
            query_dict = {
                "query": {
                    "query_string": {
                        "query": search_query
                    }
                }
            }

        # Limit to 1 result for testing
        query_dict["size"] = 1

        try:
            response = es.search(index=search_index, body=query_dict)
            
            # Extract result count
            result_count = 0
            hits_container = response.get('hits', {})
            if isinstance(hits_container, dict):
                total = hits_container.get('total')
                if isinstance(total, dict):
                    result_count = total.get('value', 0)
                elif isinstance(total, int):
                    result_count = total

            return True, "Connected and query executed successfully", {
                "cluster_name": cluster_name,
                "version": version,
                "result_count": result_count,
            }
        except Exception as query_error:
            return False, f"Query validation failed: {str(query_error)}", {}

    except Exception as e:
        return False, f"Elasticsearch connection failed: {str(e)}", {}


def _test_llm(endpoint_url: str, model_name: str, api_key: str, test_prompt: str) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        from langchain_openai import ChatOpenAI

        # Some OpenAI-compatible servers require a non-empty key even if they ignore it.
        client_key = api_key if api_key is not None and str(api_key).strip() else "not-needed"

        llm = ChatOpenAI(
            model=model_name,
            base_url=endpoint_url,
            api_key=client_key,
            temperature=0,
            timeout=20,
        )

        resp = llm.invoke(test_prompt)
        content = getattr(resp, "content", "")
        return True, "LLM test succeeded", {"sample": (content or "").strip()[:200]}

    except Exception as e:
        return False, f"LLM test failed: {str(e)}", {}


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
        data = request.get_json() or {}
        siem = (data.get("siem") or "").strip().lower()

        if siem not in {SIEM_ELASTIC, SIEM_SPLUNK}:
            return jsonify({"success": False, "error": "Invalid SIEM type"}), 400

        if siem == SIEM_ELASTIC:
            for f in ["host", "kibana_url", "api_key", "cert_path", "search_index", "search_query"]:
                err = _required(data, f)
                if err:
                    return jsonify({"success": False, "error": err}), 400

            kibana_url = (data.get("kibana_url") or "").strip()
            if kibana_url and not (kibana_url.startswith("http://") or kibana_url.startswith("https://")):
                return jsonify({"success": False, "error": "kibana_url must start with http:// or https://"}), 400

            ok, msg, details = _test_elastic(data)
            return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)

        for f in ["host", "port", "user", "password", "search_index", "search_query", "search_entry_count"]:
            err = _required(data, f)
            if err:
                return jsonify({"success": False, "error": err}), 400

        ok, msg, details = _test_splunk(data)
        return jsonify({"success": ok, "message": msg, "details": details}), (200 if ok else 400)

    @app.route("/api/init/siem/save", methods=["POST"])
    def init_siem_save():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
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
        siem_doc: Dict[str, Any] = {
            "category": CATEGORY_SIEM,
            "id": siem,
            "name": siem.upper(),
            "updated_at": now,
        }

        if siem == SIEM_ELASTIC:
            siem_doc.update(
                {
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
            )
        else:
            siem_doc.update(
                {
                    "host": data.get("host"),
                    "port": str(data.get("port")),
                    "user": data.get("user"),
                    "password": data.get("password"),
                    "search_index": data.get("search_index"),
                    "search_query": data.get("search_query"),
                    "search_entry_count": int(data.get("search_entry_count")),
                }
            )

        coll = db_connection.get_collection(SETTINGS_COLLECTION)
        coll.update_one(
            {"category": CATEGORY_SIEM, "id": siem},
            {"$set": siem_doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

        coll.update_one(
            {"category": CATEGORY_GLOBAL, "id": ID_GLOBAL},
            {"$set": {"active_siem": siem, "updated_at": now}},
            upsert=True,
        )

        return jsonify({"success": True}), 200

    @app.route("/api/init/llm/test", methods=["POST"])
    def init_llm_test():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        data = request.get_json() or {}
        provider = (data.get("provider") or "").strip().lower()
        endpoint_url = (data.get("endpoint_url") or "").strip()
        api_key = (data.get("api_key") or "").strip()
        model_name = (data.get("model_name") or "").strip()

        if provider not in ALLOWED_LLM_PROVIDERS:
            return jsonify({"success": False, "error": "Invalid LLM provider"}), 400

        if not endpoint_url:
            return jsonify({"success": False, "error": "Missing required field: endpoint_url"}), 400

        if not model_name:
            return jsonify({"success": False, "error": "Missing required field: model_name"}), 400

        test_prompt = settings_service.get_prompts_settings("test") or DEFAULT_TEST_PROMPT

        ok, msg, details = _test_llm(endpoint_url, model_name, api_key, test_prompt)
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

        endpoint_id = f"{provider}"
        model_id = f"{provider}-{_slugify(model_name)}"

        now = datetime.now().isoformat()
        coll = db_connection.get_collection(SETTINGS_COLLECTION)

        endpoint_doc = {
            "category": CATEGORY_LLM_ENDPOINT,
            "id": endpoint_id,
            "name": provider.upper(),
            "url": endpoint_url,
            "api_key": api_key or "",
            "updated_at": now,
        }
        coll.update_one(
            {"category": CATEGORY_LLM_ENDPOINT, "id": endpoint_id},
            {"$set": endpoint_doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

        model_doc = {
            "category": CATEGORY_LLM_MODEL,
            "id": model_id,
            "model_name": model_name,
            "display_name": model_name,
            "endpoint_id": endpoint_id,
            "provider": provider,
            "updated_at": now,
        }
        coll.update_one(
            {"category": CATEGORY_LLM_MODEL, "id": model_id},
            {"$set": model_doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

        coll.update_one(
            {"category": CATEGORY_GLOBAL, "id": ID_GLOBAL},
            {"$set": {"active_llm_model_id": model_id, "updated_at": now}},
            upsert=True,
        )

        return jsonify({"success": True, "model_id": model_id, "endpoint_id": endpoint_id}), 200

    @app.route("/api/init/finish", methods=["POST"])
    def init_finish():
        blocked = _block_if_initialized()
        if blocked:
            return blocked
        now = datetime.now().isoformat()
        global_settings = settings_service.get_global_settings() or {}

        active_siem = global_settings.get("active_siem")
        active_llm_model_id = global_settings.get("active_llm_model_id")

        if not active_siem:
            return jsonify({"success": False, "error": "Active SIEM not set"}), 400

        if not active_llm_model_id:
            return jsonify({"success": False, "error": "Active LLM model not set"}), 400

        coll = db_connection.get_collection(SETTINGS_COLLECTION)
        siem_doc = coll.find_one({"category": CATEGORY_SIEM, "id": active_siem}, {"_id": 0})
        model_doc = coll.find_one({"category": CATEGORY_LLM_MODEL, "id": active_llm_model_id}, {"_id": 0})

        if not siem_doc:
            return jsonify({"success": False, "error": "SIEM settings not saved"}), 400
        if not model_doc:
            return jsonify({"success": False, "error": "LLM settings not saved"}), 400

        coll.update_one(
            {"category": CATEGORY_GLOBAL, "id": ID_GLOBAL},
            {"$set": {"initialized": True, "updated_at": now}},
            upsert=True,
        )

        return jsonify({"success": True}), 200
