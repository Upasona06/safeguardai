"""
ImageSafetyAnalyzer - image-only harmful-content detection.

Pipeline:
  1) Optional NSFW classifier (Falconsai) for sexual content risk
  2) Optional CLIP zero-shot image classifier for threat/hate cues
  3) Lightweight pixel heuristics as fallback signal

All outputs are mapped to existing category keys used by RiskEngine.
"""

from __future__ import annotations

import io
import logging
from typing import Dict, List

import numpy as np
from PIL import Image, ImageOps

from backend.config.settings import settings

logger = logging.getLogger(__name__)


_nsfw_pipeline = None
_clip_pipeline = None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _get_nsfw_pipeline():
    global _nsfw_pipeline
    if _nsfw_pipeline is not None:
        return _nsfw_pipeline

    if not settings.IMAGE_ENABLE_SAFETY_MODEL:
        _nsfw_pipeline = False
        return None

    try:
        from transformers import pipeline

        _nsfw_pipeline = pipeline(
            "image-classification",
            model=settings.IMAGE_SAFETY_MODEL_NAME,
            device=-1,
            model_kwargs={"cache_dir": settings.HF_CACHE_DIR, "local_files_only": not settings.HF_ALLOW_DOWNLOAD},
        )
        logger.info("✅ Image safety model loaded: %s", settings.IMAGE_SAFETY_MODEL_NAME)
    except Exception as e:
        logger.warning("Image safety model unavailable (%s)", e)
        _nsfw_pipeline = False

    return _nsfw_pipeline if _nsfw_pipeline is not False else None


def _get_clip_pipeline():
    global _clip_pipeline
    if _clip_pipeline is not None:
        return _clip_pipeline

    if not settings.IMAGE_ENABLE_CLIP_ZEROSHOT:
        _clip_pipeline = False
        return None

    try:
        from transformers import pipeline

        _clip_pipeline = pipeline(
            "zero-shot-image-classification",
            model=settings.IMAGE_CLIP_MODEL_NAME,
            device=-1,
            model_kwargs={"cache_dir": settings.HF_CACHE_DIR, "local_files_only": not settings.HF_ALLOW_DOWNLOAD},
        )
        logger.info("✅ CLIP zero-shot model loaded: %s", settings.IMAGE_CLIP_MODEL_NAME)
    except Exception as e:
        logger.warning("CLIP zero-shot model unavailable (%s)", e)
        _clip_pipeline = False

    return _clip_pipeline if _clip_pipeline is not False else None


def _extract_nsfw_score(outputs: List[Dict]) -> float:
    for item in outputs or []:
        label = str(item.get("label", "")).strip().lower()
        score = float(item.get("score", 0.0))
        if "nsfw" in label or "porn" in label or "explicit" in label:
            return _clamp01(score)
    return 0.0


def _safe_get_label_score(outputs: List[Dict], needle: str) -> float:
    needle_lower = needle.lower()
    for item in outputs or []:
        label = str(item.get("label", "")).strip().lower()
        if needle_lower in label:
            return _clamp01(float(item.get("score", 0.0)))
    return 0.0


def _heuristic_scores(image: Image.Image) -> Dict[str, float]:
    # Lightweight fallback only; tuned conservatively to avoid over-triggering.
    rgb = np.array(image.convert("RGB"), dtype=np.uint8)

    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)

    skin_mask = (
        (r > 95)
        & (g > 40)
        & (b > 20)
        & ((np.max(rgb, axis=2) - np.min(rgb, axis=2)) > 15)
        & (np.abs(r - g) > 15)
        & (r > g)
        & (r > b)
    )
    skin_ratio = float(np.mean(skin_mask))

    red_dominant_mask = (r > 140) & (r > (g * 1.35)) & (r > (b * 1.35))
    red_ratio = float(np.mean(red_dominant_mask))

    sexual_score = _clamp01(max(0.0, (skin_ratio - 0.28) * 1.8))
    threat_score = _clamp01(max(0.0, (red_ratio - 0.20) * 1.6))

    return {
        "cyberbullying": 0.0,
        "threat": threat_score,
        "hate_speech": 0.0,
        "sexual_harassment": sexual_score,
        "grooming": 0.0,
    }


class ImageSafetyAnalyzer:
    def analyze(self, image_bytes: bytes) -> Dict:
        scores = {
            "cyberbullying": 0.0,
            "threat": 0.0,
            "hate_speech": 0.0,
            "sexual_harassment": 0.0,
            "grooming": 0.0,
        }
        evidence: List[str] = []

        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")

        nsfw_pipe = _get_nsfw_pipeline()
        if nsfw_pipe is not None:
            try:
                nsfw_outputs = nsfw_pipe(image)
                nsfw_score = _extract_nsfw_score(nsfw_outputs)
                scores["sexual_harassment"] = max(scores["sexual_harassment"], nsfw_score)
                if nsfw_score >= 0.20:
                    evidence.append(f"nsfw_model={nsfw_score:.2f}")
            except Exception as e:
                logger.warning("NSFW inference failed: %s", e)

        clip_pipe = _get_clip_pipeline()
        if clip_pipe is not None:
            try:
                outputs = clip_pipe(
                    image,
                    candidate_labels=[
                        "violent scene",
                        "weapon",
                        "hate symbol",
                        "extremist symbol",
                        "safe everyday image",
                        "sexual explicit content",
                    ],
                )
                violent_score = max(
                    _safe_get_label_score(outputs, "violent"),
                    _safe_get_label_score(outputs, "weapon"),
                )
                hate_score = max(
                    _safe_get_label_score(outputs, "hate symbol"),
                    _safe_get_label_score(outputs, "extremist"),
                )
                sexual_score = _safe_get_label_score(outputs, "sexual explicit")

                scores["threat"] = max(scores["threat"], violent_score)
                scores["hate_speech"] = max(scores["hate_speech"], hate_score)
                scores["sexual_harassment"] = max(scores["sexual_harassment"], sexual_score)

                if violent_score >= 0.20:
                    evidence.append(f"clip_violent={violent_score:.2f}")
                if hate_score >= 0.20:
                    evidence.append(f"clip_hate={hate_score:.2f}")
                if sexual_score >= 0.20:
                    evidence.append(f"clip_sexual={sexual_score:.2f}")
            except Exception as e:
                logger.warning("CLIP zero-shot inference failed: %s", e)

        heuristic = _heuristic_scores(image)
        for key, value in heuristic.items():
            scores[key] = max(scores[key], value)

        if heuristic["sexual_harassment"] >= 0.20:
            evidence.append(f"heuristic_skin={heuristic['sexual_harassment']:.2f}")
        if heuristic["threat"] >= 0.20:
            evidence.append(f"heuristic_red={heuristic['threat']:.2f}")

        return {
            "scores": {k: _clamp01(v) for k, v in scores.items()},
            "evidence": evidence,
        }
