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
    
    def _build_llm_client(self, model_override=None, url_override=None, api_key_override=None):
        """Build a ChatOpenAI client from DB settings or frontend overrides."""
        llm_settings = settings_service.get_active_llm()

        if not llm_settings:
            return None, {
                "success": False,
                "content": None,
                "status_code": 500,
                "error": "No active LLM endpoint configured",
                "latency": 0
            }

        model_cfg = llm_settings["model"]
        endpoint_cfg = llm_settings["endpoint"]

        try:
            llm = ChatOpenAI(
                model=model_override or model_cfg["model_name"],
                base_url=url_override or endpoint_cfg["url"],
                api_key=api_key_override or endpoint_cfg.get("api_key", ""),
                temperature=0,
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