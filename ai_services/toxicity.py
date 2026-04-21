"""
ToxicityClassifier — Hybrid harmful-content detection.

Production flow:
    - Stage 1 (optional): fast toxic gate model (mDeBERTa family)
    - Stage 2 (optional): multilingual multi-label model (XLM-R family)
    - Rule fusion: deterministic category rules for obfuscation, Hinglish, and OCR noise

If models are disabled or unavailable, classifier runs in rule-only mode without failing.
Output: dict of category -> float probability in [0, 1].
"""

import logging
import re
from functools import lru_cache
from typing import Dict, Tuple, List, Optional
import hashlib
from backend.config.settings import settings

# Lazy import torch only when model loading/inference is needed.
_TORCH_MODULE = None
_TORCH_IMPORT_ATTEMPTED = False


def _get_torch():
    global _TORCH_MODULE, _TORCH_IMPORT_ATTEMPTED
    if _TORCH_IMPORT_ATTEMPTED:
        return _TORCH_MODULE

    _TORCH_IMPORT_ATTEMPTED = True
    try:
        import torch as torch_module
        _TORCH_MODULE = torch_module
    except Exception as e:
        logger.warning("PyTorch import failed; falling back to rule-only mode (%s)", e)
        _TORCH_MODULE = None

    return _TORCH_MODULE

logger = logging.getLogger(__name__)

CATEGORIES = ("cyberbullying", "threat", "hate_speech", "sexual_harassment")

                                                                   
                                                                   
                                        
HF_LABEL_MAP = {
    "toxic": "cyberbullying",                                  
    "toxicity": "cyberbullying",
    "abusive": "cyberbullying",
    "harassment": "cyberbullying",
    "severe_toxic": "threat",
    "obscene": "sexual_harassment",
    "threat": "threat",
    "violence": "threat",
    "insult": "cyberbullying",
    "identity_hate": "hate_speech",
    "hate": "hate_speech",
    "sexually_explicit": "sexual_harassment",
}

NEUTRAL_LABEL_HINTS = (
    "non-toxic",
    "not_toxic",
    "neutral",
    "safe",
    "clean",
    "none",
    "normal",
)

FALLBACK_INDEX_TO_CATEGORY = {
    0: "cyberbullying",
    1: "threat",
    2: "hate_speech",
    3: "sexual_harassment",
}

                                                                    
KEYWORD_RULES: Dict[str, list] = {
    "threat": [
        r"\bkill\b", r"\bhurt\b", r"\bdekhna\b", r"\bdekh lena\b",
        r"\bwatch your back\b", r"\bregret\b", r"\bwon't forgive\b",
        r"\bmaar\b", r"\bjaan se\b", r"\bkhatam\b",
        r"\bdeath\b", r"\bdie\b", r"\beliminate\b",
        r"\bstab\b", r"\bshoot\b", r"\bslap\b", r"\bbeat you\b",
        r"\bno right to live\b", r"\bshould be dead\b", r"\bdeserves death\b",
        r"\bwipe out\b", r"\bexterminate\b",
    ],
    "cyberbullying": [
        r"\bloser\b", r"\bstupid\b", r"\bidiot\b", r"\bbewakoof\b",
        r"\bchutiya\b", r"\bsala\b", r"\bkamina\b", r"\bdesperate\b",
        r"\bfool\b", r"\bdumb\b", r"\bworthless\b", r"\bgay\b",
        r"\bmother[f-]ucker\b", r"\basshole\b", r"\bbitch\b",
        r"\bbastard\b", r"\bwhore\b", r"\bslut\b", r"\bfuck you\b",
        r"\bharami\b", r"\brandi\b", r"\bbehenchod\b", r"\bmadarchod\b",
    ],
    "hate_speech": [
        r"\bterrorist\b", r"\bcommunal\b", r"\bjihadi\b",
        r"\blanat\b", r"\bkaafir\b", r"\bpig\b",
        r"\bhate\b", r"\bMuslim\b", r"\bHindu\b", r"\bChristian\b", r"\bJew\b",
        r"\bscum\b", r"\bunholy\b", r"\binfidel\b",
    ],
    "sexual_harassment": [
        r"\bsexy\b", r"\bnude\b", r"\bsend pics\b", r"\bphoto bhejo\b",
        r"\bvideo call\b", r"\bkoi dekhega nahi\b",
        r"\bsuck\b", r"\bfucker\b", r"\bass\b", r"\bcock\b", r"\bpussy\b",
        r"\bfuck\b", r"\bblowjob\b", r"\bsex\b", r"\bporn\b",
        r"\bnudes\b", r"\bsend nudes\b", r"\bdick\b", r"\btits\b", r"\bboobs\b",
        r"\brape\b", r"\bsexual\b", r"\bgrope\b",
    ],
}

                                                                     
SEVERE_RULES: Dict[str, list] = {
    "threat": [
        r"\b(kill|murder|death|exterminate|watch your back)\b",
        r"\b(no right to live|deserves death|jaan se|khatam)\b",
    ],
    "cyberbullying": [
        r"\b(kill yourself|worthless|mother[f-]?ucker|asshole|bitch)\b",
    ],
    "hate_speech": [
        r"\b(terrorist|jihadi|infidel|scum|filth)\b",
    ],
    "sexual_harassment": [
        r"\b(rape|nude|porn|blowjob|send pics|photo bhejo|sexual)\b",
    ],
}

SELF_HARM_BULLYING_PATTERN = r"\b(kill yourself|kys|go die)\b"
PHOTO_BLACKMAIL_PATTERN = (
    r"\b(photo bhejo|send (me )?(your )?(pic|pics|photo|nudes)|nude pics)\b"
    r".*\b(warna|or else|dekh lena|i will leak|viral kar dunga|expose)\b"
)

                                                                          
OBFUSCATED_TOKEN_MAP: Dict[str, str] = {
    r"\bf[\W_]*u[\W_]*c[\W_]*k(?:[\W_]*e[\W_]*r)?\b": "fucker",
    r"\bb[\W_]*i[\W_]*t[\W_]*c[\W_]*h\b": "bitch",
    r"\bm[\W_]*a[\W_]*d[\W_]*a[\W_]*r[\W_]*c[\W_]*h[\W_]*o[\W_]*d\b": "madarchod",
    r"\bb[\W_]*e[\W_]*h[\W_]*e[\W_]*n[\W_]*c[\W_]*h[\W_]*o[\W_]*d\b": "behenchod",
    r"\br[\W_]*a[\W_]*n[\W_]*d[\W_]*i\b": "randi",
}


class ToxicityClassifier:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.multilabel_model = None
        self.multilabel_tokenizer = None
        self.device = None
        self._is_quantized = False
        self._model_enabled = False
        self._multilabel_enabled = False
        self._set_device()
        self._load_model()
        self._load_multilabel_model()

    def _set_device(self) -> None:
        torch_module = _get_torch()
        if torch_module is None:
            self.device = None
            return

        self.device = torch_module.device(
            "cuda" if settings.HF_DEVICE == "cuda" and torch_module.cuda.is_available() else "cpu"
        )

    def _load_model(self):
        """Load stage-1 toxic gate model (mDeBERTa family by default)."""
        torch_module = _get_torch()
        gate_enabled = settings.HF_ENABLE_GATE_MODEL or settings.HF_ENABLE_MODEL
        model_name = (
            settings.TOXIC_GATE_MODEL_NAME
            if settings.HF_ENABLE_GATE_MODEL
            else settings.HF_MODEL_NAME
        )

        if not gate_enabled:
            logger.info("Stage-1 toxicity gate disabled; using rules-only gating")
            self.model = None
            self.tokenizer = None
            self._model_enabled = False
            return

        if torch_module is None:
            logger.warning("PyTorch unavailable; running toxicity classifier in rule-only mode")
            self.model = None
            self.tokenizer = None
            self._model_enabled = False
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            logger.info("Loading stage-1 gate model: %s", model_name)
            local_only = not settings.HF_ALLOW_DOWNLOAD

                            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=settings.HF_CACHE_DIR,
                truncation_side="right",
                local_files_only=local_only,
            )

                        
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=settings.HF_CACHE_DIR,
                output_attentions=True,                             
                local_files_only=local_only,
            ).to(self.device).eval()

                                                          
            if settings.HF_USE_QUANTIZATION and self.device and self.device.type == "cpu":
                try:
                    self.model = torch_module.quantization.quantize_dynamic(
                        self.model,
                        {torch_module.nn.Linear},
                        dtype=torch_module.qint8,
                    )
                    self._is_quantized = True
                    logger.info("✅ Model quantized (INT8) — 2-3x faster inference")
                except Exception as e:
                    logger.warning("Quantization failed (%s), using full precision", e)

            self._model_enabled = True
            logger.info(
                "✅ Stage-1 toxicity gate loaded on %s (quantized=%s)",
                self.device,
                self._is_quantized,
            )
        except Exception as e:
            logger.exception("Gate model unavailable (%s) — using rule-only mode", e)
            self.model = None
            self.tokenizer = None
            self._model_enabled = False

    def _load_multilabel_model(self):
        """Load stage-2 multi-label classifier (XLM-R family by default)."""
        torch_module = _get_torch()
        if not settings.HF_ENABLE_MULTILABEL_MODEL:
            logger.info("Stage-2 multi-label model disabled; using rule-calibrated labels")
            self.multilabel_model = None
            self.multilabel_tokenizer = None
            self._multilabel_enabled = False
            return

        if torch_module is None:
            logger.warning("PyTorch unavailable; disabling multi-label model")
            self.multilabel_model = None
            self.multilabel_tokenizer = None
            self._multilabel_enabled = False
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            model_name = settings.TOXIC_MULTILABEL_MODEL_NAME
            logger.info("Loading stage-2 multi-label model: %s", model_name)
            local_only = not settings.HF_ALLOW_DOWNLOAD

            self.multilabel_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=settings.HF_CACHE_DIR,
                truncation_side="right",
                local_files_only=local_only,
            )

            self.multilabel_model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=settings.HF_CACHE_DIR,
                output_attentions=False,
                local_files_only=local_only,
            ).to(self.device).eval()

            if settings.HF_USE_QUANTIZATION and self.device and self.device.type == "cpu":
                try:
                    self.multilabel_model = torch_module.quantization.quantize_dynamic(
                        self.multilabel_model,
                        {torch_module.nn.Linear},
                        dtype=torch_module.qint8,
                    )
                    logger.info("✅ Stage-2 model quantized (INT8)")
                except Exception as e:
                    logger.warning("Stage-2 quantization failed (%s), using full precision", e)

            self._multilabel_enabled = True
            logger.info("✅ Stage-2 multi-label model loaded on %s", self.device)
        except Exception as e:
            logger.exception("Multi-label model unavailable (%s) — using rule-calibrated labels", e)
            self.multilabel_model = None
            self.multilabel_tokenizer = None
            self._multilabel_enabled = False

    def classify(self, text: str) -> Dict[str, float]:
        """Classify text with hybrid ML + rules approach. Returns {category: score}."""
        normalized_text = self._normalize_input_text(text)

        scores: Dict[str, float] = {category: 0.0 for category in CATEGORIES}

                                                                             
        category_hits: Dict[str, int] = {}
        for category, patterns in KEYWORD_RULES.items():
            hits = sum(
                1 for p in patterns
                if re.search(p, normalized_text, re.IGNORECASE)
            )
            if hits > 0:
                category_hits[category] = hits

                                           
        gate_score = 0.0
        if self._model_enabled and self.model and self.tokenizer:
            try:
                gate_score, attention_weights = self._infer_with_attention(normalized_text)

                                                                                            
                self._get_token_attribution(normalized_text, attention_weights)
            except Exception as e:
                logger.warning("Transformer inference error: %s", e)
                                                                                              
                self._model_enabled = False
                self.model = None
                self.tokenizer = None

                                                              
        model_multilabel_scores: Dict[str, float] = {}
        should_run_multilabel = bool(category_hits) or gate_score >= settings.TOXIC_GATE_THRESHOLD
        if should_run_multilabel and self._multilabel_enabled and self.multilabel_model and self.multilabel_tokenizer:
            try:
                model_multilabel_scores = self._infer_multilabel_scores(normalized_text)
            except Exception as e:
                logger.warning("Multi-label inference error: %s", e)
                self._multilabel_enabled = False
                self.multilabel_model = None
                self.multilabel_tokenizer = None

                                                                  
        for category, score in model_multilabel_scores.items():
            if category in scores:
                scores[category] = round(max(scores[category], score), 4)

                                
        if category_hits:
            for category, hits in category_hits.items():
                rule_score = self._compute_rule_score(category, hits, normalized_text)
                fused_score = max(rule_score, scores.get(category, 0.0))

                if gate_score > 0.0:
                    fused_score = max(fused_score, min(1.0, rule_score * 0.75 + gate_score * 0.35))

                if scores.get(category, 0.0) > 0.0:
                    fused_score = max(
                        fused_score,
                        min(1.0, rule_score * 0.55 + scores[category] * 0.55),
                    )

                scores[category] = round(min(fused_score, 1.0), 4)
        else:
                                                                                 
                                                                        
            if gate_score >= 0.85 and max(scores.values()) < 0.35:
                scores["cyberbullying"] = round(max(scores["cyberbullying"], min(gate_score * 0.75, 0.75)), 4)
            elif gate_score >= 0.75 and max(scores.values()) < 0.25:
                scores["cyberbullying"] = round(max(scores["cyberbullying"], min(gate_score * 0.50, 0.45)), 4)

                                                  
                                                                               
                                                     
        if re.search(SELF_HARM_BULLYING_PATTERN, normalized_text, re.IGNORECASE):
            scores["cyberbullying"] = round(max(scores["cyberbullying"], 0.88), 4)
            scores["threat"] = round(min(scores["threat"], 0.30), 4)

                                                                                        
        if re.search(PHOTO_BLACKMAIL_PATTERN, normalized_text, re.IGNORECASE):
            scores["sexual_harassment"] = round(max(scores["sexual_harassment"], 0.86), 4)
            if scores["threat"] > 0.0:
                scores["threat"] = round(max(scores["threat"], 0.45), 4)

                               
        for category in CATEGORIES:
            scores[category] = round(min(max(scores.get(category, 0.0), 0.0), 1.0), 4)

        return scores

    def _normalize_input_text(self, text: str) -> str:
        normalized = text.lower().strip()

                                                  
        normalized = re.sub(r"[_\-./]+", " ", normalized)

                                                                         
        normalized = re.sub(r"(.)\1{2,}", r"\1\1", normalized)

                                                                               
        normalized = re.sub(
            r"\b(?:[a-z]\s+){2,}[a-z]\b",
            lambda m: m.group(0).replace(" ", ""),
            normalized,
        )

        for pattern, replacement in OBFUSCATED_TOKEN_MAP.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _compute_rule_score(self, category: str, hits: int, text: str) -> float:
        """Convert regex hit counts to calibrated category confidence."""
                                                                 
        score = min(0.35 + hits * 0.18, 0.78)

        severe_patterns = SEVERE_RULES.get(category, [])
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in severe_patterns):
            score = max(score, 0.82)

        return min(score, 1.0)

    def _infer_multilabel_scores(self, text: str) -> Dict[str, float]:
        """Run stage-2 multi-label model and map labels into platform categories."""
        torch_module = _get_torch()
        if torch_module is None:
            raise RuntimeError("PyTorch is unavailable")

        if not self.multilabel_model or not self.multilabel_tokenizer:
            return {}

        inputs = self.multilabel_tokenizer(
            text[: settings.HF_MAX_SEQUENCE_LENGTH],
            return_tensors="pt",
            truncation=True,
            max_length=settings.HF_MAX_SEQUENCE_LENGTH,
            padding=True,
        ).to(self.device)

        with torch_module.no_grad():
            outputs = self.multilabel_model(**inputs)

        logits = outputs.logits
        if logits.shape[-1] <= 0:
            return {}

                                                                              
                                                                       
        probs = torch_module.sigmoid(logits)[0]

        raw_id2label = getattr(self.multilabel_model.config, "id2label", {}) or {}
        id2label: Dict[int, str] = {}
        for idx, label in raw_id2label.items():
            try:
                id2label[int(idx)] = str(label)
            except Exception:
                continue

        resolved: Dict[str, float] = {}
        for idx in range(len(probs)):
            label_name = id2label.get(idx, f"LABEL_{idx}")
            category = self._map_model_label_to_category(
                label_name=label_name,
                index=idx,
                total_labels=len(probs),
            )
            if not category:
                continue

            score = float(probs[idx].cpu())
            resolved[category] = max(resolved.get(category, 0.0), score)

        return {k: round(v, 4) for k, v in resolved.items()}

    def _map_model_label_to_category(
        self,
        label_name: str,
        index: int,
        total_labels: int,
    ) -> Optional[str]:
        """Map model output labels into the platform category schema."""
        normalized = str(label_name).strip().lower().replace("-", "_").replace(" ", "_")

        if normalized in HF_LABEL_MAP:
            return HF_LABEL_MAP[normalized]

        for alias, category in HF_LABEL_MAP.items():
            if alias in normalized:
                return category

                                                                                  
                                                                                
        if normalized.startswith("label_") and total_labels == len(CATEGORIES) and index in FALLBACK_INDEX_TO_CATEGORY:
            return FALLBACK_INDEX_TO_CATEGORY[index]

                                                                                  
        if total_labels == len(CATEGORIES) and index in FALLBACK_INDEX_TO_CATEGORY:
            return FALLBACK_INDEX_TO_CATEGORY[index]

        return None

    def _extract_toxic_probability(self, logits: "torch.Tensor", id2label: Dict[int, str]) -> float:
        """Extract a robust toxic probability from binary or multi-class gate heads."""
        torch_module = _get_torch()
        if torch_module is None:
            return 0.0

        if logits.shape[-1] == 1:
            return float(torch_module.sigmoid(logits)[0, 0].cpu())

        probs = torch_module.softmax(logits, dim=-1)[0]
        toxic_max = 0.0

        for idx, score in enumerate(probs):
            label = str(id2label.get(idx, "")).strip().lower().replace(" ", "_")
            if label and any(hint in label for hint in NEUTRAL_LABEL_HINTS):
                continue
            toxic_max = max(toxic_max, float(score.cpu()))

        if toxic_max > 0.0:
            return toxic_max

        if len(probs) > 1:
            return float(probs[1].cpu())

        return float(probs.max().cpu())
    
    def _infer_with_attention(self, text: str) -> Tuple[float, object]:
        """Run inference and return: (toxic_score, attention_weights)."""
        torch_module = _get_torch()
        if torch_module is None:
            raise RuntimeError("PyTorch is unavailable")

        if not self.model or not self.tokenizer:
            raise RuntimeError("Gate model is not loaded")

                  
        inputs = self.tokenizer(
            text[: settings.HF_MAX_SEQUENCE_LENGTH],
            return_tensors="pt",
            truncation=True,
            max_length=settings.HF_MAX_SEQUENCE_LENGTH,
            padding=True,
        ).to(self.device)
        
                      
        with torch_module.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits

        raw_id2label = getattr(self.model.config, "id2label", {}) or {}
        id2label: Dict[int, str] = {}
        for idx, label in raw_id2label.items():
            try:
                id2label[int(idx)] = str(label)
            except Exception:
                continue

        toxic_prob = self._extract_toxic_probability(logits, id2label)
        
                                                                
        attention = outputs.attentions[-1] if outputs.attentions else None
        
        return toxic_prob, attention
    
    def _get_token_attribution(self, text: str, attention: object) -> Dict[str, float]:
        """Extract token importance scores from attention weights."""
        try:
            if attention is None or not self.tokenizer:
                return {}

                                            
            aggregated = attention[0].mean(dim=0)                      
            
                                                
            cls_attention = aggregated[0, :]             
            
                                           
            tokens = self.tokenizer.tokenize(text[:512])
            
                                      
            token_importance = {}
            for i, token in enumerate(tokens[:len(cls_attention)]):
                importance = float(cls_attention[i].cpu())
                token_importance[token] = importance
            
            return token_importance
        except Exception as e:
            logger.warning("Token attribution extraction failed: %s", e)
            return {}

    @lru_cache(maxsize=1000)
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text classification."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def cache_stats(self) -> Dict:
        """Return cache statistics for monitoring."""
        return {
            "cache_info": self._get_cache_key.cache_info(),
            "quantized": self._is_quantized,
            "device": str(self.device),
            "gate_enabled": self._model_enabled,
            "multilabel_enabled": self._multilabel_enabled,
        }
