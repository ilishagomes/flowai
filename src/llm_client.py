"""
llm_client.py

Thin wrapper around the Anthropic API used by the rest of FlowAI.

Design notes (worth re-reading before an interview):
- All AI calls are funneled through `ask_claude_for_json`, which enforces
  JSON-only output and validates it before anything downstream trusts it.
- If no API key is configured, or the API call fails for any reason
  (network, rate limit, malformed JSON), we fall back to a deterministic,
  rule-based analysis in `fallback.py`. This means the app never crashes
  or shows a blank screen just because the AI step failed - it degrades
  gracefully to a simpler but still useful result, and tells the user
  that's what happened.
- We never let the model's output go straight to the screen unvalidated.
  This is the "how do you handle bad AI outputs" answer for the interview:
  schema-check first, fallback second, human review always available.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

try:
    import anthropic
except ImportError:  # pragma: no cover - handled at runtime in the UI
    anthropic = None

DEFAULT_MODEL = "claude-sonnet-4-6"


@dataclass
class LLMResult:
    """Wraps an LLM call so callers always know whether it actually used AI."""
    data: dict
    used_ai: bool
    error: Optional[str] = None


def _get_client() -> Optional["anthropic.Anthropic"]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _extract_json(text: str) -> dict:
    """
    Models occasionally wrap JSON in prose or code fences despite instructions.
    Strip fences, then grab the first {...} block as a defensive measure.
    """
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def ask_claude_for_json(system_prompt: str, user_prompt: str,
                         model: str = DEFAULT_MODEL,
                         max_tokens: int = 2000) -> LLMResult:
    """
    Sends a prompt to Claude and returns parsed JSON.

    Returns LLMResult(used_ai=False, error=...) instead of raising, so the
    caller can decide to fall back rather than blow up the whole app.
    """
    client = _get_client()
    if client is None:
        return LLMResult(data={}, used_ai=False,
                          error="No ANTHROPIC_API_KEY configured - using offline analysis mode.")

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text_parts = [block.text for block in response.content if block.type == "text"]
        raw_text = "\n".join(text_parts)
        data = _extract_json(raw_text)
        if not isinstance(data, dict):
            raise ValueError("Model did not return a JSON object.")
        return LLMResult(data=data, used_ai=True)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any failure -> fallback
        return LLMResult(data={}, used_ai=False, error=f"AI call failed ({exc}); using offline analysis mode.")
