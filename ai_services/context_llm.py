"""
Optional context LLM escalation for conversation-level safety analysis.

The analyzer is disabled by default and only activated when:
  - CONTEXT_LLM_ENABLED=true
  - CONTEXT_LLM_ENDPOINT is set

Expected output categories are normalized to [0, 1].
"""

import json
import logging
import re
from typing import Dict, Iterable
from urllib import request as urllib_request

from backend.config.settings import settings


logger = logging.getLogger(__name__)

CATEGORIES = ("cyberbullying", "threat", "hate_speech", "sexual_harassment", "grooming")


class ContextLLMAnalyzer:
    def __init__(self) -> None:
        self.enabled = bool(
            settings.CONTEXT_LLM_ENABLED and str(settings.CONTEXT_LLM_ENDPOINT).strip()
        )

    def analyze(self, messages: Iterable) -> Dict[str, float]:
        """Return category scores from context LLM; returns empty dict on any failure."""
        if not self.enabled:
            return {}

        try:
            payload = self._build_payload(messages)
            timeout_s = max(1000, int(settings.CONTEXT_LLM_TIMEOUT_MS)) / 1000.0
            req = urllib_request.Request(
                settings.CONTEXT_LLM_ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=timeout_s) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)

            parsed = self._parse_response(data)
            return self._clamp_scores(parsed)
        except Exception as e:
            logger.warning("Context LLM escalation unavailable: %s", e)
            return {}

    def _build_payload(self, messages: Iterable) -> Dict:
        turns = []
        for message in messages:
            role = getattr(message, "role", "user")
            text = getattr(message, "text", "")
            turns.append(f"{role}: {text}")

        conversation = "\n".join(turns).strip()

        system_prompt = (
            "You are a safety classifier for multi-turn conversations. "
            "Return JSON only, with numeric scores between 0 and 1 for keys: "
            "cyberbullying, threat, hate_speech, sexual_harassment, grooming."
        )

        return {
            "model": settings.CONTEXT_LLM_MODEL,
            "temperature": 0,
            "max_tokens": 220,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation},
            ],
        }

    def _parse_response(self, data: Dict) -> Dict[str, float]:
                                          
        if isinstance(data.get("scores"), dict):
            return self._extract_categories(data["scores"])

                                                     
        top_level_scores = self._extract_categories(data)
        if top_level_scores:
            return top_level_scores

                                                           
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, list):
                                                   
                content = "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))

            if isinstance(content, str) and content.strip():
                maybe_json = self._extract_json_block(content)
                if maybe_json:
                    try:
                        parsed = json.loads(maybe_json)
                        return self._extract_categories(parsed)
                    except Exception:
                        return {}

        return {}

    def _extract_categories(self, obj: Dict) -> Dict[str, float]:
        extracted: Dict[str, float] = {}
        for key in CATEGORIES:
            if key in obj:
                extracted[key] = self._to_float(obj[key])
        return extracted

    def _extract_json_block(self, text: str) -> str:
                                                
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.IGNORECASE | re.DOTALL)
        if fenced:
            return fenced.group(1)

                                                  
        generic = re.search(r"(\{.*\})", text, re.DOTALL)
        if generic:
            return generic.group(1)
        return ""

    def _to_float(self, value) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    def _clamp_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        clamped: Dict[str, float] = {}
        for key, value in scores.items():
            clamped[key] = round(min(max(self._to_float(value), 0.0), 1.0), 4)
        return clamped
