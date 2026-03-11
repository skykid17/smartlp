"""Canonical response type for all LLM interactions.

Every service that calls an LLM (llm_service, rag_service, regex_engine)
should return an LLMResponse. Route handlers call .to_dict() at the JSON
serialization boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LLMResponse:
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    latency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON API responses.

        Metadata keys are flattened into the top-level dict so that
        existing callers (e.g. ``result["status_code"]``) keep working.
        """
        d = asdict(self)
        d.update(d.pop("metadata", {}))
        return d

    @staticmethod
    def fail(error: str, latency: float = 0.0, **meta: Any) -> LLMResponse:
        return LLMResponse(success=False, error=error, latency=latency, metadata=meta)

    @staticmethod
    def ok(content: str, latency: float = 0.0, **meta: Any) -> LLMResponse:
        return LLMResponse(success=True, content=content, latency=latency, metadata=meta)
