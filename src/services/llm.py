"""LLM Service for SmartSOC Application

This module provides a centralized service for interacting with Large Language Models (LLMs)
for various tasks including regex generation, log type determination, and general queries.
"""

import time
import requests
import urllib3
import json
from typing import Dict, Any, Tuple, Optional
from .base import BaseService
from .settings import settings_service
from utils.logging import app_logger
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class LLMService(BaseService):
    """Service for interacting with Large Language Models."""
    
    def __init__(self):
        super().__init__('llm')
        self.temperature = 0.1  # Low temperature for consistent output
        
    def _get_active_llm_config(self) -> Optional[Dict[str, Any]]:
        """Get the configuration for the active LLM endpoint.
        
        Returns:
            Dictionary containing LLM configuration or None if not found
        """
        try:
            # Read active endpoint id from global settings (accept snake_case and camelCase)
            global_settings = settings_service.get_global_settings()
            active_endpoint_id = None

            if isinstance(global_settings, dict):
                active_endpoint_id = global_settings.get('active_llm_endpoint')

            if not active_endpoint_id:
                self.log_warning("No active LLM endpoint configured")
                return None

            # Get list of endpoints (stored as-is in DB). Be defensive about key names.
            endpoints = settings_service.get_llm_settings()
            for endpoint in endpoints:
                if not isinstance(endpoint, dict):
                    continue
                eid = endpoint.get('id') or endpoint.get('ID') or endpoint.get('Id')
                name = endpoint.get('name') or endpoint.get('Name')

                try:
                    if eid and str(eid).lower() == str(active_endpoint_id).lower():
                        return endpoint
                    if name and str(name).lower() == str(active_endpoint_id).lower():
                        return endpoint
                except Exception:
                    continue

            self.log_warning(f"Active LLM endpoint '{active_endpoint_id}' not found in configuration")
            return None

        except Exception as e:
            self.log_error(f"Error getting active LLM config: {str(e)}", e)
            return None
    
    def _build_llm_client(self, model_override=None, url_override=None, api_key_override=None):
        """Build a ChatOpenAI client from DB settings or frontend overrides."""
        config = self._get_active_llm_config()
        global_settings = settings_service.get_global_settings()
        active_llm = global_settings.get('active_llm', '') if isinstance(global_settings, dict) else None

        if not config:
            return None, {
                "success": False,
                "content": None,
                "status_code": 500,
                "error": "No active LLM endpoint configured",
                "latency": 0
            }

        try:
            model = model_override or active_llm or config.get("model")[0]
            url = url_override or config.get("url")
            api_key = api_key_override or config.get("api_key", "test")
            temperature = config.get("temperature", 0.1)

            llm = ChatOpenAI(
                model=model,
                base_url=url,
                api_key=api_key,
                temperature=temperature,
                timeout=30,
            )

            return llm, None

        except Exception as e:
            return None, {
                "success": False,
                "content": None,
                "status_code": 500,
                "error": f"Failed to initialize LLM client: {str(e)}",
                "latency": 0
            }

    def query_llm(self, user_prompt: str, system_prompt: str = None, model_override=None, url_override=None, api_key_override=None):
    
        start_time = time.time()

        llm, error_response = self._build_llm_client(
            model_override=model_override,
            url_override=url_override,
            api_key_override=api_key_override
        )

        if error_response:
            return error_response

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_prompt))

        try:
            response = llm.invoke(messages)
            latency = round(time.time() - start_time, 4)

            return {
                "success": True,
                "content": response.content.strip(),
                "status_code": 200,
                "error": None,
                "latency": latency
            }

        except Exception as e:
            latency = round(time.time() - start_time, 4)
            status = getattr(e, "status_code", 500)
            
            app_logger.log_message("llm", f"LLM query failed: {str(e)}", "ERROR")
            
            return {
                "success": False,
                "content": None,
                "status_code": status,
                "error": str(e),
                "latency": latency
            }

# Create service instance
llm_service = LLMService()