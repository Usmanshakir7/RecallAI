"""RecallAI AI provider adapter: offline sample mode and Meterless Nightshift."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger("recallai.ai")


def _sample_insights(transcript: str) -> dict[str, Any]:
    """Credential-free deterministic output for demos and tests."""
    lines = [line.strip() for line in transcript.splitlines() if line.strip()]
    action_items = []
    for line in lines:
        lower = line.lower()
        if any(marker in lower for marker in ("todo:", "action:", "follow up:", "will ", "needs to ")):
            owner = None
            if ":" in line:
                prefix, rest = line.split(":", 1)
                if len(prefix) <= 40 and prefix.lower() not in {"todo", "action", "decision"}:
                    owner = prefix.strip()
                    task = rest.strip()
                else:
                    task = line
            else:
                task = line
            action_items.append({"task": task, "owner": owner})
    decisions = [line for line in lines if line.lower().startswith(("decision:", "decided:"))]
    topics = []
    for line in lines:
        candidate = line.split(":", 1)[-1].strip()
        if candidate and candidate not in topics:
            topics.append(candidate[:120])
        if len(topics) == 5:
            break
    return {
        "status": "completed",
        "summary": "Sample-mode analysis of the supplied meeting transcript. Connect Nightshift to enable model-generated insights.",
        "topics": topics,
        "decisions": decisions,
        "action_items": action_items,
    }


def _runtime_token() -> str:
    token = os.getenv("METERLESS_API_KEY", "").strip()
    if token:
        return token
    token_path = os.getenv("METERLESS_TOKEN_FILE", "").strip()
    if token_path:
        try:
            return Path(token_path).expanduser().read_text(encoding="utf-8").strip()
        except OSError:
            logger.warning("Nightshift token file is unavailable.")
    return ""


def _nightshift_chat(transcript: str, role: str, prior: str | None = None) -> str:
    base_url = os.getenv("METERLESS_BASE_URL", "http://127.0.0.1:8088/v1").strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        endpoint = base_url
    else:
        endpoint = base_url.removesuffix("/v1") + "/v1/chat/completions"
    token = _runtime_token()
    if not token:
        raise RuntimeError("Nightshift token missing: set METERLESS_API_KEY or METERLESS_TOKEN_FILE.")
    model = os.getenv("METERLESS_MODEL", "meterless/auto").strip() or "meterless/auto"
    prompt = (
        "Extract meeting insights from the transcript. Return ONLY valid JSON with exactly these keys: "
        "status (string), summary (string), topics (array of strings), decisions (array of strings), "
        "action_items (array of objects with task and owner; owner may be null). "
        "Do not invent facts; preserve uncertainty.\n\nTRANSCRIPT:\n" + transcript
    )
    if prior:
        prompt = (
            "You are the critique/repair agent. Check the proposed JSON against the transcript for unsupported "
            "claims and schema errors. Return corrected JSON only with keys status, summary, topics, decisions, "
            "action_items. Transcript:\n" + transcript + "\n\nPROPOSED JSON:\n" + prior
        )
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "meterless-app": "recallai",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": False,
        },
        timeout=180,
    )
    logger.info("ai_trace provider=meterless_nightshift model=%s agent=%s status=%s", model, role, response.status_code)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_insights(transcript: str) -> dict[str, Any]:
    """Generate insights; defaults to safe offline mode unless explicitly disabled."""
    sample_mode = os.getenv("SAMPLE_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
    if sample_mode:
        logger.info("ai_trace provider=sample model=deterministic agent=extract status=completed")
        return _sample_insights(transcript)

    try:
        raw = _nightshift_chat(transcript, "extract")
        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Nightshift output was not valid JSON; invoking critique/repair agent.")
            raw = _nightshift_chat(transcript, "critique_repair", prior=str(raw))
            result = json.loads(raw)
        required = {"status", "summary", "topics", "decisions", "action_items"}
        if not required.issubset(result) or not isinstance(result["action_items"], list):
            raise ValueError("Nightshift response did not match the insights schema.")
        result["status"] = "completed"
        return result
    except Exception:
        logger.exception("ai_trace provider=meterless_nightshift model=%s agent=escalation status=failed", os.getenv("METERLESS_MODEL", "meterless/auto"))
        if os.getenv("SAMPLE_FALLBACK", "true").strip().lower() in {"1", "true", "yes", "on"}:
            logger.warning("Falling back to sample mode; output is not live AI.")
            return _sample_insights(transcript)
        raise
