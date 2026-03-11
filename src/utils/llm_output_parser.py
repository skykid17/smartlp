"""Centralized parsers for LLM output.

Replaces the scattered ``clean_response() -> json.loads() -> extract``
pattern with two focused functions:

- ``parse_json_response`` — for LLM calls that should return JSON
- ``parse_regex_response`` — for LLM calls that should return a regex string

Both build on the low-level ``clean_response()`` from ``utils.formatters``.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from utils.formatters import clean_response

logger = logging.getLogger(__name__)


def parse_json_response(
    raw: str,
    required_fields: Optional[List[str]] = None,
    defaults: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse LLM output as a JSON dict.

    Steps:
        1. ``clean_response()`` to strip markdown fences / backticks
        2. ``json.loads()``
        3. If the result is a list, take the first element
        4. Apply *defaults* for missing fields
        5. Warn (not fail) if *required_fields* are absent

    Raises:
        ValueError: when the raw string cannot be parsed as JSON or the
            top-level type is unexpected.
    """
    defaults = defaults or {}
    cleaned = clean_response(raw)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e} | Raw: {raw[:200]}") from e

    # Normalize to dict
    if isinstance(parsed, list):
        if not parsed:
            raise ValueError("LLM returned empty JSON array")
        parsed = parsed[0] if isinstance(parsed[0], dict) else {"value": parsed[0]}
    elif not isinstance(parsed, dict):
        raise ValueError(f"Unexpected JSON type: {type(parsed).__name__}")

    # Apply defaults for missing keys
    for key, default_val in defaults.items():
        parsed.setdefault(key, default_val)

    # Warn about missing required fields (but don't fail — LLMs are unreliable)
    if required_fields:
        missing = [f for f in required_fields if f not in parsed]
        if missing:
            logger.warning("LLM JSON missing fields %s: %s", missing, parsed)

    return parsed


def parse_regex_response(raw: str) -> str:
    """Parse LLM output as a regex string.

    Handles JSON-wrapped strings/objects (e.g. ``{"regex": "..."}``),
    markdown fences, and safely un-escapes doubled backslashes.

    This intentionally does NOT blindly ``json.loads`` the cleaned output
    because regex patterns containing ``{n}`` quantifiers look like JSON
    braces but should not be parsed that way.
    """
    cleaned = clean_response(raw)

    # Only attempt JSON decode if it actually looks like a JSON object/array
    parsed = None
    stripped = cleaned.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            pass

    if isinstance(parsed, dict):
        cleaned = parsed.get("regex") or parsed.get("pattern") or cleaned
    elif isinstance(parsed, list) and parsed:
        first = parsed[0]
        cleaned = first if isinstance(first, str) else cleaned
    elif isinstance(parsed, str):
        cleaned = parsed

    if isinstance(cleaned, str):
        cleaned = cleaned.strip()
        cleaned = cleaned.replace("\\\\", "\\")

    return cleaned
