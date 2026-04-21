"""
RiskEngine — converts category probability scores to a risk level.

Scoring logic:
  - Compute a weighted composite score
  - Grooming & threat carry higher weight
  - Map composite to LOW / MEDIUM / HIGH / CRITICAL
"""

from typing import Dict, Tuple

                                                                    
CATEGORY_WEIGHTS = {
    "grooming": 1.5,
    "threat": 1.3,
    "sexual_harassment": 1.2,
    "hate_speech": 1.0,
    "cyberbullying": 0.9,
}

                                                                    
THRESHOLDS = [
    (0.75, "CRITICAL"),
    (0.50, "HIGH"),
    (0.25, "MEDIUM"),
    (0.0,  "LOW"),
]


class RiskEngine:
    def compute(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """
        Returns (risk_level, overall_score) where overall_score ∈ [0, 1].
        """
        if not scores:
            return "LOW", 0.0

        max_score = max(scores.values(), default=0.0)

                                                                              
                                                    
        active_scores = {cat: score for cat, score in scores.items() if score >= 0.05}

        if not active_scores:
            overall = round(max_score, 4)
        else:
            weighted_sum = 0.0
            weight_total = 0.0
            for cat, score in active_scores.items():
                w = CATEGORY_WEIGHTS.get(cat, 1.0)
                weighted_sum += score * w
                weight_total += w

            weighted_active = weighted_sum / max(weight_total, 1.0)
            overall = round(max(weighted_active, max_score * 0.9), 4)

                                                        
        if scores.get("grooming", 0.0) >= 0.70 or scores.get("threat", 0.0) >= 0.75:
            return "CRITICAL", max(overall, 0.75)

        if (
            scores.get("threat", 0.0) >= 0.60
            or scores.get("sexual_harassment", 0.0) >= 0.65
            or scores.get("hate_speech", 0.0) >= 0.70
        ):
            return "HIGH", max(overall, 0.60)

        for threshold, level in THRESHOLDS:
            if overall >= threshold:
                return level, overall

        return "LOW", overall
