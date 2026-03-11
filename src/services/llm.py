"""LLM Service for SmartSOC Application

This module provides a centralized service for interacting with Large Language Models (LLMs)
for various tasks including regex generation, log type determination, and general queries.

All LLM client construction is funneled through ``get_client()`` so that the
rest of the codebase (including RAG) never imports ChatOpenAI directly.
"""

import time
from typing import Dict, Any, Tuple, Optional
from .base import BaseService
from .settings import settings_service
from .llm_response import LLMResponse
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


class LLMService(BaseService):
    """Service for interacting with Large Language Models."""

    def __init__(self):
        super().__init__('llm')
        self._client: Optional[ChatOpenAI] = None
        self._client_config_hash: Optional[str] = None

    # ------------------------------------------------------------------
    # Client factory (single source of ChatOpenAI instances)
    # ------------------------------------------------------------------

    def get_client(
        self,
        model_override: Optional[str] = None,
        url_override: Optional[str] = None,
        api_key_override: Optional[str] = None,
        json_mode: bool = False,
    ) -> Tuple[Optional[ChatOpenAI], Optional[LLMResponse]]:
        """Return a (possibly cached) ChatOpenAI client.

        Returns ``(client, None)`` on success or ``(None, LLMResponse)``
        on error.
        """
        llm_settings = settings_service.get_active_llm()

        if not llm_settings:
            return None, LLMResponse.fail(
                "No active LLM endpoint configured", status_code=500
            )

        model_cfg = llm_settings["model"]
        endpoint_cfg = llm_settings["endpoint"]

        model = model_override or model_cfg["model_name"]
        url = url_override or endpoint_cfg["url"]
        api_key = api_key_override or endpoint_cfg.get("api_key", "") or "dummy"

        config_key = f"{model}|{url}|{api_key}|{json_mode}"

        if self._client is not None and self._client_config_hash == config_key:
            return self._client, None

        try:
            llm_kwargs = {}
            if json_mode:
                llm_kwargs["model_kwargs"] = {
                    "response_format": {"type": "json_object"}
                }

            client = ChatOpenAI(
                model=model,
                base_url=url,
                api_key=api_key,
                temperature=0,
                timeout=30,
                **llm_kwargs,
            )

            # Only cache when using default settings (no overrides)
            if not any([model_override, url_override, api_key_override]):
                self._client = client
                self._client_config_hash = config_key

            return client, None

        except Exception as e:
            return None, LLMResponse.fail(
                f"Failed to initialize LLM client: {e}", status_code=500
            )

    def invalidate_cache(self) -> None:
        """Clear the cached client. Call when LLM settings change."""
        self._client = None
        self._client_config_hash = None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query_llm(
        self,
        user_prompt: str,
        system_prompt: str = None,
        model_override=None,
        url_override=None,
        api_key_override=None,
        json_mode: bool = False,
    ) -> dict:
        """Query the LLM and return a result dict.

        Returns a plain dict with keys: success, content, status_code,
        error, latency — preserving the exact contract that all existing
        callers depend on.
        """
        start_time = time.time()

        client, err = self.get_client(
            model_override=model_override,
            url_override=url_override,
            api_key_override=api_key_override,
            json_mode=json_mode,
        )

        if err:
            return err.to_dict()

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_prompt))

        try:
            response = client.invoke(messages)
            latency = round(time.time() - start_time, 4)

            return LLMResponse.ok(
                response.content.strip(),
                latency=latency,
                status_code=200,
            ).to_dict()

        except Exception as e:
            latency = round(time.time() - start_time, 4)
            status = getattr(e, "status_code", 500)

            self.logger.exception("LLM query failed")

            return LLMResponse.fail(
                str(e), latency=latency, status_code=status
            ).to_dict()

    # ------------------------------------------------------------------
    # Connection test (ad-hoc client, never cached)
    # ------------------------------------------------------------------

    def test_connection(
        self,
        endpoint_url: str,
        model_name: str,
        api_key: str,
        test_prompt: str,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Test LLM connection with provided configuration.

        Args:
            endpoint_url: The LLM endpoint URL
            model_name: The model name to test
            api_key: The API key (can be empty for some providers)
            test_prompt: The test prompt to send

        Returns:
            Tuple of (success, message, details)
        """
        try:
            client_key = (
                api_key
                if api_key is not None and str(api_key).strip()
                else "not-needed"
            )

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


# Create service instance
llm_service = LLMService()
