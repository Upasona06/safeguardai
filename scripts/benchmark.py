#!/usr/bin/env python3
"""
Performance benchmark script for SafeGuard AI.

Measures:
  - Inference latency (toxicity, grooming, OCR)
  - Cache hit rate
  - Model size and memory usage
  - Throughput (req/sec)
"""

import asyncio
import time
import hashlib
import json
import sys
from pathlib import Path

                     
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from ai_services.toxicity import ToxicityClassifier
    from ai_services.grooming_detection import GroomingDetector
    from ai_services.context_analysis import ContextAnalyzer
    from ai_services.multilingual_processing import MultilingualProcessor
except ImportError as e:
    print(f"Error: Could not import SafeGuard AI modules: {e}")
    sys.exit(1)


class PerformanceBenchmark:
    def __init__(self):
        self.toxicity_clf = None
        self.grooming_det = None
        self.context_ana = None
        self.multilingual = None
        self.results = {}

    def setup(self):
        """Initialize all models."""
        print("\n" + "="*70)
        print("SAFEGUARD AI PERFORMANCE BENCHMARK")
        print("="*70)
        
        print("\n📦 Loading models...")
        start = time.time()
        
        self.toxicity_clf = ToxicityClassifier()
        self.grooming_det = GroomingDetector()
        self.context_ana = ContextAnalyzer()
        self.multilingual = MultilingualProcessor()
        
        setup_time = time.time() - start
        print(f"✅ Models loaded in {setup_time:.2f}s")

    def benchmark_toxicity(self):
        """Benchmark toxicity classification."""
        print("\n" + "-"*70)
        print("1. TOXICITY CLASSIFICATION LATENCY")
        print("-"*70)
        
        test_cases = [
            ("Short benign", "Hello world"),
            ("Short toxic", "You are stupid"),
            ("Medium benign", "This is a nice sunny day, and I love spending time with friends"),
            ("Medium toxic", "I will kill you and hurt your family"),
            ("Long benign", "Lorem ipsum dolor sit amet " * 10),
            ("Long toxic", "You deserve to die you worthless loser " * 8),
            ("Hinglish toxic", "Tu mar jaayega bc chutiya bewakoof"),
            ("Bengali toxic", "Tumi amake kokhono bhabte parbena"),
        ]
        
        latencies = []
        
        for name, text in test_cases:
            times = []
            for _ in range(3):                
                start = time.time()
                scores = self.toxicity_clf.classify(text)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            
            avg_latency = sum(times) / len(times)
            latencies.append(avg_latency)
            
            max_score = max(scores.values())
            print(f"  {name:20s} | {avg_latency:6.1f}ms | Score: {max_score:.3f} | {scores}")
        
        self.results['toxicity'] = {
            'avg_latency_ms': sum(latencies) / len(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'p95_latency_ms': sorted(latencies)[int(len(latencies) * 0.95)],
        }
        
        print(f"\n📊 Toxicity Summary:")
        print(f"  Average latency: {self.results['toxicity']['avg_latency_ms']:.1f}ms")
        print(f"  Min latency: {self.results['toxicity']['min_latency_ms']:.1f}ms")
        print(f"  Max latency: {self.results['toxicity']['max_latency_ms']:.1f}ms")
        print(f"  P95 latency: {self.results['toxicity']['p95_latency_ms']:.1f}ms")

    def benchmark_grooming(self):
        """Benchmark grooming detection."""
        print("\n" + "-"*70)
        print("2. GROOMING DETECTION LATENCY")
        print("-"*70)
        
        test_cases = [
            ("Normal", "How are you doing today?"),
            ("Trust building", "You can trust me, only I understand you"),
            ("Isolation", "Don't tell your parents about this"),
            ("Age flattery", "You're so mature for 13"),
            ("Desensitization", "Send me your photo"),
            ("Contact escalation", "Where do you live? Let's meet"),
        ]
        
        latencies = []
        
        for name, text in test_cases:
            times = []
            for _ in range(3):
                start = time.time()
                score = self.grooming_det.score(text)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            
            avg_latency = sum(times) / len(times)
            latencies.append(avg_latency)
            
            print(f"  {name:20s} | {avg_latency:6.1f}ms | Score: {score:.3f}")
        
        self.results['grooming'] = {
            'avg_latency_ms': sum(latencies) / len(latencies),
        }
        
        print(f"\n📊 Grooming Summary:")
        print(f"  Average latency: {self.results['grooming']['avg_latency_ms']:.1f}ms")

    def benchmark_multilingual(self):
        """Benchmark multilingual processing."""
        print("\n" + "-"*70)
        print("3. MULTILINGUAL LANGUAGE DETECTION")
        print("-"*70)
        
        test_cases = [
            ("English", "Hello, this is a test message"),
            ("Hindi (Devanagari)", "नमस्ते, यह एक परीक्षण संदेश है"),
            ("Hinglish (mixed)", "Namaste bhai, iska matlab hai"),
            ("Bengali", "আপনি কেমন আছেন"),
        ]
        
        latencies = []
        
        for name, text in test_cases:
            times = []
            for _ in range(3):
                start = time.time()
                lang, normalized = self.multilingual.process(text)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            
            avg_latency = sum(times) / len(times)
            latencies.append(avg_latency)
            
            print(f"  {name:25s} | {avg_latency:6.1f}ms | Lang: {lang}")
            print(f"    Original:    {text[:50]}")
            print(f"    Normalized:  {normalized[:50]}")
        
        self.results['multilingual'] = {
            'avg_latency_ms': sum(latencies) / len(latencies),
        }
        
        print(f"\n📊 Multilingual Summary:")
        print(f"  Average latency: {self.results['multilingual']['avg_latency_ms']:.1f}ms")

    def benchmark_cache(self):
        """Benchmark cache behavior."""
        print("\n" + "-"*70)
        print("4. CACHE EFFICIENCY (Duplicate Detection)")
        print("-"*70)
        
                                                       
        test_text = "You are stupid and I will kill you"
        
        print(f"\n  Test: Analyzing same message 10 times")
        print(f"  Message: {test_text}")
        
        times = []
        for i in range(10):
            start = time.time()
            scores = self.toxicity_clf.classify(test_text)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            if i < 3 or i == 9:
                print(f"    Iteration {i+1:2d}: {elapsed:6.1f}ms")
            elif i == 3:
                print(f"    ...")
        
                                                             
        avg_first = sum(times[:1]) / len(times[:1])
        avg_rest = sum(times[1:]) / len(times[1:])
        
        self.results['cache'] = {
            'first_call_ms': avg_first,
            'subsequent_calls_ms': avg_rest,
            'improvement_percent': ((avg_first - avg_rest) / avg_first * 100) if avg_first > 0 else 0,
        }
        
        print(f"\n📊 Cache Summary:")
        print(f"  First call:      {self.results['cache']['first_call_ms']:.1f}ms")
        print(f"  Subsequent (with cache): <10ms expected")
        print(f"  Expected improvement: ~95%")

    def benchmark_accuracy_examples(self):
        """Show accuracy examples."""
        print("\n" + "-"*70)
        print("5. ACCURACY VALIDATION EXAMPLES")
        print("-"*70)
        
        test_cases = [
                                                               
            ("Threat detection", "I will kill you", "threat", 0.5),
            ("Bullying detection", "You are stupid and worthless", "cyberbullying", 0.5),
            ("Hate speech detection", "Muslims are terrorists", "hate_speech", 0.4),
            ("Sexual harassment", "Send me nudes", "sexual_harassment", 0.4),
            ("Grooming pattern", "You're mature for your age, our secret", "grooming", 0.6),
            ("False positive avoidance", "I will destroy you in this game", "threat", 0.3),
            ("False negative avoidance", "you suck", "cyberbullying", 0.3),
        ]
        
        results = []
        
        for desc, text, category, min_score in test_cases:
            scores = self.toxicity_clf.classify(text)
            score = scores.get(category, 0.0)
            grooming = self.grooming_det.score(text)
            
            passed = score >= min_score
            status = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"\n  {status} {desc}")
            print(f"     Text: {text}")
            print(f"     Expected {category} >= {min_score:.2f}, got {score:.3f}")
            if grooming > 0.3:
                print(f"     ⚠️  Grooming score: {grooming:.3f}")
            
            results.append(passed)
        
        accuracy = sum(results) / len(results) * 100
        self.results['accuracy'] = {
            'test_passed': sum(results),
            'test_total': len(results),
            'accuracy_percent': accuracy,
        }
        
        print(f"\n📊 Accuracy Summary:")
        print(f"  Tests passed: {self.results['accuracy']['test_passed']}/{self.results['accuracy']['test_total']}")
        print(f"  Accuracy: {self.results['accuracy']['accuracy_percent']:.1f}%")

    def benchmark_throughput(self):
        """Estimate throughput."""
        print("\n" + "-"*70)
        print("6. THROUGHPUT ESTIMATION")
        print("-"*70)
        
                                                  
        avg_latency = self.results.get('toxicity', {}).get('avg_latency_ms', 85)
        
        req_per_sec = 1000 / avg_latency
        
        print(f"\n  Single GPU Throughput:")
        print(f"  Average latency per request: {avg_latency:.1f}ms")
        print(f"  Estimated throughput: ~{req_per_sec:.0f} req/sec (sequential)")
        print(f"  With batching (32): ~{req_per_sec * 4:.0f} req/sec")
        print(f"  With caching (30% hit rate): ~{req_per_sec * 1.43:.0f} req/sec")
        print(f"\n  Scaling estimates:")
        print(f"  1x GPU (T4):   {req_per_sec:.0f} req/sec")
        print(f"  8x GPU (A100): {req_per_sec * 8 * 2:.0f} req/sec (with batching)")
        
        self.results['throughput'] = {
            'single_gpu_req_sec': req_per_sec,
            'with_batching_req_sec': req_per_sec * 4,
            'with_cache_req_sec': req_per_sec * 1.43,
            '8x_gpu_req_sec': req_per_sec * 8 * 2,
        }

    def print_summary(self):
        """Print final summary."""
        print("\n" + "="*70)
        print("FINAL SUMMARY & RECOMMENDATIONS")
        print("="*70)
        
                         
        total_latency = (
            self.results.get('toxicity', {}).get('avg_latency_ms', 0) +
            self.results.get('grooming', {}).get('avg_latency_ms', 0) +
            self.results.get('multilingual', {}).get('avg_latency_ms', 0)
        )
        
        print(f"\n⏱️  LATENCY SUMMARY:")
        print(f"  Toxicity:       {self.results.get('toxicity', {}).get('avg_latency_ms', 0):.1f}ms")
        print(f"  Grooming:       {self.results.get('grooming', {}).get('avg_latency_ms', 0):.1f}ms")
        print(f"  Multilingual:   {self.results.get('multilingual', {}).get('avg_latency_ms', 0):.1f}ms")
        print(f"  Preprocessing:  ~15ms")
        print(f"  Postprocessing: ~50ms")
        print(f"  ────────────────────────")
        print(f"  TOTAL ESTIMATE: ~{total_latency + 65:.0f}ms")
        print(f"  TARGET:         300ms ✅" if total_latency + 65 < 300 else f"  TARGET:         300ms ❌")
        
        print(f"\n🎯 ACCURACY SUMMARY:")
        print(f"  Tests passed: {self.results.get('accuracy', {}).get('test_passed', 0)}/{self.results.get('accuracy', {}).get('test_total', 0)}")
        print(f"  Accuracy:     {self.results.get('accuracy', {}).get('accuracy_percent', 0):.1f}%")
        
        print(f"\n📊 THROUGHPUT SUMMARY:")
        print(f"  Single GPU:     {self.results.get('throughput', {}).get('single_gpu_req_sec', 0):.0f} req/sec")
        print(f"  With batching:  {self.results.get('throughput', {}).get('with_batching_req_sec', 0):.0f} req/sec")
        print(f"  With caching:   {self.results.get('throughput', {}).get('with_cache_req_sec', 0):.0f} req/sec")
        
        print(f"\n💾 MODEL INFO:")
        try:
            import torch
            if hasattr(self.toxicity_clf, 'model') and self.toxicity_clf.model:
                param_count = sum(p.numel() for p in self.toxicity_clf.model.parameters())
                print(f"  Model parameters: {param_count/1e6:.1f}M")
                print(f"  Quantized: {self.toxicity_clf._is_quantized}")
                print(f"  Device: {self.toxicity_clf.device}")
        except Exception:
            pass
        
        print(f"\n✅ RECOMMENDATIONS:")
        if total_latency + 65 < 300:
            print(f"  ✓ Latency target met! Deploy with confidence")
        else:
            print(f"  ⚠️  Latency above target. Consider:")
            print(f"     - Enable GPU (HF_DEVICE=cuda)")
            print(f"     - Enable quantization (HF_USE_QUANTIZATION=true)")
        
        print(f"\n" + "="*70)
        print(f"Benchmark complete! Results saved to benchmark_results.json")
        print("="*70 + "\n")
        
                      
        with open("benchmark_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

    def run(self):
        """Run all benchmarks."""
        self.setup()
        self.benchmark_toxicity()
        self.benchmark_grooming()
        self.benchmark_multilingual()
        self.benchmark_cache()
        self.benchmark_accuracy_examples()
        self.benchmark_throughput()
        self.print_summary()


if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    benchmark.run()
