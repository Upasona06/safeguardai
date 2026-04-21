"""
GroomingDetector — detects child-targeting grooming patterns.

Uses a combination of:
  - Linguistic pattern matching (trust building, isolation, secret keeping)
  - Age-gap signal detection
  - Conversation escalation heuristics
  - Optional fine-tuned classifier

POCSO-aligned: maps to POCSO Act Section 11, 13, IT Act 67B.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

                                                                    
GROOMING_PATTERNS = {
                    
    "trust_building": [
        r"\bi understand you\b", r"\byou can trust me\b", r"\bonly i care\b",
        r"\byour parents don.t understand\b", r"\bour secret\b",
        r"\bspecial friend\b", r"\bno one else gets you\b",
    ],
                       
    "isolation": [
        r"\bdon.t tell (your )?(parents|mom|dad|teacher)\b",
        r"\bkeep this between us\b", r"\bjust between (you and )?me\b",
        r"\bdon.t tell anyone\b", r"\bright\? no one will know\b",
    ],
                                
    "maturity_flattery": [
        r"\bso mature for your age\b", r"\byou.re not like other kids\b",
        r"\bvery grown up\b", r"\byou seem older\b",
        r"\b(so|very|really) (smart|beautiful|pretty|handsome) for \d+\b",
    ],
                               
    "incentives": [
        r"\bi.ll buy you\b", r"\bsend you (money|gifts|recharge)\b",
        r"\bwant a (gift|present|surprise)\b",
        r"\bi can pay\b", r"\bpaisa dunga\b",
    ],
                            
    "desensitization": [
        r"\bsend (me )?(your )?(pic|photo|video|selfie)\b",
        r"\bshow me\b", r"\bvideo call karte hai\b",
        r"\bI.ll show you mine\b", r"\bnothing wrong\b",
    ],
                        
    "contact_escalation": [
        r"\bwhat.s your (address|school|location)\b",
        r"\bwhere do you live\b", r"\bmeet (me|in person)\b",
        r"\bcome (alone|without)\b", r"\bpick you up\b",
        r"\bkahan rehte ho\b",
    ],
}

                               
PATTERN_WEIGHTS = {
    "trust_building": 0.15,
    "isolation": 0.25,
    "maturity_flattery": 0.20,
    "incentives": 0.20,
    "desensitization": 0.30,
    "contact_escalation": 0.35,
}


class GroomingDetector:
    def score(self, text: str) -> float:
        """Score a single message for grooming signals. Returns [0, 1]."""
        return self._compute_score(text)

    def score_conversation(self, messages) -> float:
        """
        Score a full conversation for grooming patterns.
        Rewards consistent multi-turn grooming escalation.
        """
        combined = " ".join(m.text for m in messages)
        base_score = self._compute_score(combined)

                                                                         
        pattern_types_hit = set()
        for msg in messages:
            for ptype, patterns in GROOMING_PATTERNS.items():
                if any(re.search(p, msg.text, re.IGNORECASE) for p in patterns):
                    pattern_types_hit.add(ptype)

        escalation_bonus = len(pattern_types_hit) * 0.08
        return round(min(base_score + escalation_bonus, 1.0), 4)

    def _compute_score(self, text: str) -> float:
        total = 0.0
        for ptype, patterns in GROOMING_PATTERNS.items():
            hits = sum(
                1 for p in patterns
                if re.search(p, text, re.IGNORECASE)
            )
            if hits:
                weight = PATTERN_WEIGHTS[ptype]
                total += weight * min(hits, 3) / 3                          

        return round(min(total, 1.0), 4)
