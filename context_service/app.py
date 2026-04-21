"""
Dedicated context moderation service for CONTEXT_LLM_ENDPOINT.

This service accepts OpenAI-style chat-completions payloads and returns
normalized category scores in [0, 1]. It can either:
1) Proxy to an upstream model endpoint, or
2) Use a deterministic local heuristic fallback.
"""

import json
import logging
import os
import re
from collections import Counter
from typing import Dict, List

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


CATEGORIES = (
    "cyberbullying",
    "threat",
    "hate_speech",
    "sexual_harassment",
    "grooming",
)

logger = logging.getLogger("context_service")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


class Message(BaseModel):
    role: str = "user"
    content: str | List[Dict[str, object]] | Dict[str, object] = ""


class ChatCompletionRequest(BaseModel):
    model: str = "Qwen/Qwen2.5-7B-Instruct"
    temperature: float = 0.0
    max_tokens: int = 220
    messages: List[Message] = Field(default_factory=list)


app = FastAPI(
    title="Safeguard Context LLM Service",
    version="1.0.0",
    description="Stable context scoring endpoint for conversation safety escalation.",
)


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _clamp(score: object) -> float:
    return round(min(max(_safe_float(score), 0.0), 1.0), 4)


def _extract_categories(obj: Dict[str, object]) -> Dict[str, float]:
    parsed: Dict[str, float] = {}
    for key in CATEGORIES:
        if key in obj:
            parsed[key] = _clamp(obj[key])
    return parsed


def _extract_json_block(text: str) -> str:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.IGNORECASE | re.DOTALL)
    if fenced:
        return fenced.group(1)

    generic = re.search(r"(\{.*\})", text, re.DOTALL)
    if generic:
        return generic.group(1)
    return ""


def _parse_upstream_payload(data: Dict[str, object]) -> Dict[str, float]:
    if isinstance(data.get("scores"), dict):
        return _extract_categories(data["scores"])

    top_level = _extract_categories(data)
    if top_level:
        return top_level

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message", {}) if isinstance(first, dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""

        if isinstance(content, list):
            content = "\n".join(
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict)
            )

        if isinstance(content, str) and content.strip():
            maybe_json = _extract_json_block(content)
            if maybe_json:
                try:
                    parsed = json.loads(maybe_json)
                    return _extract_categories(parsed)
                except Exception:
                    return {}

    return {}


def _content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        pieces: List[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text", "")
                if isinstance(text, str):
                    pieces.append(text)
        return "\n".join(pieces)

    if isinstance(content, dict):
        text = content.get("text", "")
        if isinstance(text, str):
            return text

    return ""


def _conversation_text(messages: List[Message]) -> str:
    turns: List[str] = []
    for message in messages:
        turns.append(f"{message.role}: {_content_to_text(message.content)}")
    return "\n".join(turns).strip()


def _keyword_score(text: str, terms: List[str], base: float = 0.22) -> float:
    count = 0
    for term in terms:
        count += len(re.findall(re.escape(term), text, re.IGNORECASE))
    return _clamp(min(1.0, count * base))


def _heuristic_scores(conversation: str) -> Dict[str, float]:
    text = conversation.lower()

    scores = {
        "cyberbullying": _keyword_score(
            text,
            [
                "loser",
                "idiot",
                "stupid",
                "worthless",
                "nobody likes you",
                "go away",
                "everyone hates you",
            ],
            base=0.18,
        ),
        "threat": _keyword_score(
            text,
            [
                "i will kill",
                "hurt you",
                "beat you",
                "attack",
                "destroy you",
                "shoot",
                "stab",
            ],
            base=0.28,
        ),
        "hate_speech": _keyword_score(
            text,
            [
                "go back to",
                "your kind",
                "dirty",
                "subhuman",
                "inferior race",
                "vermin",
            ],
            base=0.2,
        ),
        "sexual_harassment": _keyword_score(
            text,
            [
                "send nudes",
                "sex with me",
                "touch you",
                "hot pic",
                "sexy pic",
                "undress",
                "sleep with me",
            ],
            base=0.24,
        ),
        "grooming": _keyword_score(
            text,
            [
                "how old are you",
                "dont tell your parents",
                "secret between us",
                "meet me alone",
                "private chat",
                "are you alone",
            ],
            base=0.25,
        ),
    }

    mentions = re.findall(r"@\w+", conversation)
    if mentions:
        counts = Counter(mentions)
        most_common_count = counts.most_common(1)[0][1]
        repetition = min(most_common_count / max(len(conversation.splitlines()), 1), 1.0)
        if repetition >= 0.5:
            scores["cyberbullying"] = _clamp(max(scores["cyberbullying"], 0.5 + repetition * 0.3))

    return {key: _clamp(value) for key, value in scores.items()}


def _service_mode() -> str:
    return os.getenv("CONTEXT_SERVICE_MODE", "auto").strip().lower()


def _upstream_url() -> str:
    return os.getenv("UPSTREAM_CHAT_COMPLETIONS_URL", "").strip()


def _build_upstream_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}

    api_key = os.getenv("UPSTREAM_API_KEY", "").strip()
    if not api_key:
        return headers

    header_name = os.getenv("UPSTREAM_API_KEY_HEADER", "Authorization").strip() or "Authorization"
    prefix = os.getenv("UPSTREAM_API_KEY_PREFIX", "Bearer").strip()

    if prefix:
        headers[header_name] = f"{prefix} {api_key}"
    else:
        headers[header_name] = api_key

    return headers


def _upstream_timeout_s() -> float:
    timeout_ms = max(1000, int(os.getenv("UPSTREAM_TIMEOUT_MS", "6000")))
    return timeout_ms / 1000.0


def _call_upstream(payload: Dict[str, object]) -> Dict[str, float]:
    url = _upstream_url()
    if not url:
        return {}

    try:
        response = requests.post(
            url,
            json=payload,
            headers=_build_upstream_headers(),
            timeout=_upstream_timeout_s(),
        )
        response.raise_for_status()
        data = response.json()
        parsed = _parse_upstream_payload(data)
        if parsed:
            return parsed

        logger.warning("Upstream returned response without parseable category scores")
        return {}
    except Exception as exc:
        logger.warning("Upstream context call failed: %s", exc)
        return {}


@app.get("/health")
def health() -> Dict[str, object]:
    return {
        "status": "ok",
        "mode": _service_mode(),
        "upstream_configured": bool(_upstream_url()),
    }


@app.post("/")
@app.post("/v1/chat/completions")
def chat_completions(body: ChatCompletionRequest) -> Dict[str, object]:
    if not body.messages:
        return {"scores": {key: 0.0 for key in CATEGORIES}, "source": "empty"}

    payload = body.model_dump()
    mode = _service_mode()

    if mode in {"auto", "upstream"}:
        upstream_scores = _call_upstream(payload)
        if upstream_scores:
            return {"scores": upstream_scores, "source": "upstream"}

        if mode == "upstream":
            raise HTTPException(status_code=502, detail="Upstream context provider unavailable")

    conversation = _conversation_text(body.messages)
    local_scores = _heuristic_scores(conversation)
    return {"scores": local_scores, "source": "heuristic"}
