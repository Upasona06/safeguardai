#!/usr/bin/env python3
"""
Final quality benchmark for SafeGuard AI best-quality mode.

Checks:
1. Live load paths (gate model, multi-label model, context endpoint path)
2. Multilingual harmful-content benchmark
3. OCR extraction + OCR->classification benchmark
4. Strict READY / NOT_READY verdict
"""

import json
import sys
import time
import threading
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer

                                                                              
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw, ImageFont

from ai_services.toxicity import ToxicityClassifier
from ai_services.context_analysis import ContextAnalyzer
from ai_services.multilingual_processing import MultilingualProcessor
from backend.config.settings import settings
from backend.utils.ocr import extract_text_from_image


RESULT_PATH = Path("final_quality_report.json")


@dataclass
class Msg:
    role: str
    text: str


class _ContextMockHandler(BaseHTTPRequestHandler):
    hits = 0

    def log_message(self, format: str, *args: object) -> None:
                                      
        return

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return

        _ContextMockHandler.hits += 1
        payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "cyberbullying": 0.65,
                                "threat": 0.72,
                                "hate_speech": 0.05,
                                "sexual_harassment": 0.08,
                                "grooming": 0.22,
                            }
                        )
                    }
                }
            ]
        }

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _maybe_start_context_mock() -> Tuple[HTTPServer | None, threading.Thread | None, bool, str]:
    endpoint = str(settings.CONTEXT_LLM_ENDPOINT or "").strip()
    if not endpoint:
        return None, None, False, "CONTEXT_LLM_ENDPOINT is empty"

    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path or ""

    if host not in {"127.0.0.1", "localhost"}:
        return None, None, False, "Endpoint is not localhost; mock not started"

    if path != "/v1/chat/completions":
        return None, None, False, "Endpoint path is not /v1/chat/completions"

    try:
        server = HTTPServer((host, port), _ContextMockHandler)
    except OSError as e:
        return None, None, False, f"Could not bind mock server: {e}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, True, f"Mock server started at {host}:{port}"


def _build_text_image_bytes(text: str) -> bytes:
    img = Image.new("RGB", (1100, 260), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except Exception:
        font = ImageFont.load_default()

    draw.multiline_text((40, 70), text, fill="black", font=font, spacing=10)

    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _run_multilingual_benchmark(clf: ToxicityClassifier, mp: MultilingualProcessor) -> Dict:
    harmful_cases = [
        {
            "text": "i will kill you tonight",
            "expected": "threat",
            "threshold": 0.60,
        },
        {
            "text": "मैं तुम्हें जान से मार दूंगा",
            "expected": "threat",
            "threshold": 0.55,
        },
        {
            "text": "send nudes or i leak your photos",
            "expected": "sexual_harassment",
            "threshold": 0.65,
        },
    ]

    benign_cases = [
        "have a great day",
        "let us discuss homework in class",
    ]

    harmful_results = []
    for case in harmful_cases:
        lang, normalized = mp.process(case["text"])
        scores = clf.classify(normalized)
        exp = case["expected"]
        val = float(scores.get(exp, 0.0))
        passed = val >= case["threshold"]
        harmful_results.append(
            {
                "text": case["text"],
                "language": lang,
                "expected": exp,
                "expected_score": val,
                "threshold": case["threshold"],
                "scores": scores,
                "passed": passed,
            }
        )

    benign_results = []
    for text in benign_cases:
        lang, normalized = mp.process(text)
        scores = clf.classify(normalized)
        top = max(scores.values()) if scores else 0.0
        passed = top <= 0.35
        benign_results.append(
            {
                "text": text,
                "language": lang,
                "top_score": top,
                "scores": scores,
                "passed": passed,
            }
        )

    harmful_pass = sum(1 for r in harmful_results if r["passed"])
    benign_pass = sum(1 for r in benign_results if r["passed"])

    return {
        "harmful_cases": harmful_results,
        "benign_cases": benign_results,
        "harmful_pass_rate": harmful_pass / max(1, len(harmful_results)),
        "benign_pass_rate": benign_pass / max(1, len(benign_results)),
    }


def _run_ocr_benchmark(clf: ToxicityClassifier) -> Dict:
    ocr_cases = [
        {
            "text": "i will kill you",
            "expected": "threat",
            "threshold": 0.55,
            "must_contain": "kill",
        },
        {
            "text": "have a wonderful day",
            "expected": "benign",
            "threshold": 0.35,
            "must_contain": "wonderful",
        },
    ]

    results = []
    extraction_pass = 0
    class_pass = 0

    for case in ocr_cases:
        image_bytes = _build_text_image_bytes(case["text"])
        extracted = extract_text_from_image(image_bytes)
        extracted_l = extracted.lower().strip()

        extracted_ok = case["must_contain"] in extracted_l
        if extracted_ok:
            extraction_pass += 1

        scores = clf.classify(extracted) if extracted else {
            "cyberbullying": 0.0,
            "threat": 0.0,
            "hate_speech": 0.0,
            "sexual_harassment": 0.0,
        }

        if case["expected"] == "benign":
            top = max(scores.values()) if scores else 0.0
            class_ok = top <= case["threshold"]
        else:
            class_ok = float(scores.get(case["expected"], 0.0)) >= case["threshold"]

        if class_ok:
            class_pass += 1

        results.append(
            {
                "source_text": case["text"],
                "extracted_text": extracted,
                "expected": case["expected"],
                "threshold": case["threshold"],
                "scores": scores,
                "extraction_pass": extracted_ok,
                "classification_pass": class_ok,
            }
        )

    total = max(1, len(ocr_cases))
    return {
        "cases": results,
        "extraction_pass_rate": extraction_pass / total,
        "classification_pass_rate": class_pass / total,
    }


def run() -> Dict:
    started_at = time.time()

    server = None
    thread = None
    mock_started = False
    mock_note = ""

    if settings.CONTEXT_LLM_ENABLED:
        server, thread, mock_started, mock_note = _maybe_start_context_mock()

    try:
        load_start = time.time()
        clf = ToxicityClassifier()
        mp = MultilingualProcessor()
        ctx = ContextAnalyzer()
        load_time_sec = time.time() - load_start

        stats = clf.cache_stats()
        gate_enabled = bool(stats.get("gate_enabled", False))
        multilabel_enabled = bool(stats.get("multilabel_enabled", False))

        context_probe_messages = [
            Msg("sender", "you are disgusting and i know where you live"),
            Msg("sender", "watch your back"),
        ]
        context_scores = ctx.analyze(context_probe_messages)
        context_live_hits = _ContextMockHandler.hits
        context_path_live = (not settings.CONTEXT_LLM_ENABLED) or (context_live_hits > 0)

        multilingual = _run_multilingual_benchmark(clf, mp)
        ocr = _run_ocr_benchmark(clf)

        criteria = {
            "gate_model_loaded": gate_enabled,
            "multilabel_model_loaded": multilabel_enabled,
            "context_enabled": bool(settings.CONTEXT_LLM_ENABLED),
            "context_path_live": context_path_live,
            "multilingual_harmful_pass": multilingual["harmful_pass_rate"] >= 0.80,
            "multilingual_benign_pass": multilingual["benign_pass_rate"] >= 0.66,
            "ocr_extraction_pass": ocr["extraction_pass_rate"] >= 0.67,
            "ocr_classification_pass": ocr["classification_pass_rate"] >= 0.67,
        }

        ready = all(criteria.values())

        report = {
            "timestamp": int(time.time()),
            "runtime_seconds": round(time.time() - started_at, 3),
            "load_time_seconds": round(load_time_sec, 3),
            "settings": {
                "HF_ENABLE_GATE_MODEL": settings.HF_ENABLE_GATE_MODEL,
                "HF_ENABLE_MULTILABEL_MODEL": settings.HF_ENABLE_MULTILABEL_MODEL,
                "CONTEXT_LLM_ENABLED": settings.CONTEXT_LLM_ENABLED,
                "TOXIC_GATE_MODEL_NAME": settings.TOXIC_GATE_MODEL_NAME,
                "TOXIC_MULTILABEL_MODEL_NAME": settings.TOXIC_MULTILABEL_MODEL_NAME,
                "CONTEXT_LLM_ENDPOINT": settings.CONTEXT_LLM_ENDPOINT,
                "HF_CACHE_DIR": settings.HF_CACHE_DIR,
            },
            "load_paths": {
                "cache_stats": stats,
                "context_probe_scores": context_scores,
                "context_mock_started": mock_started,
                "context_mock_note": mock_note,
                "context_mock_hits": context_live_hits,
            },
            "multilingual_benchmark": multilingual,
            "ocr_benchmark": ocr,
            "criteria": criteria,
            "verdict": "READY" if ready else "NOT_READY",
        }

        RESULT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    finally:
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass


if __name__ == "__main__":
    result = run()
    print("FINAL_VERDICT", result["verdict"])
    print("REPORT_FILE", str(RESULT_PATH.resolve()))
    print("GATE_LOADED", result["criteria"]["gate_model_loaded"])
    print("MULTILABEL_LOADED", result["criteria"]["multilabel_model_loaded"])
    print("CONTEXT_PATH_LIVE", result["criteria"]["context_path_live"])
    print("MULTILINGUAL_HARMFUL_PASS", result["multilingual_benchmark"]["harmful_pass_rate"])
    print("MULTILINGUAL_BENIGN_PASS", result["multilingual_benchmark"]["benign_pass_rate"])
    print("OCR_EXTRACTION_PASS", result["ocr_benchmark"]["extraction_pass_rate"])
    print("OCR_CLASSIFICATION_PASS", result["ocr_benchmark"]["classification_pass_rate"])
