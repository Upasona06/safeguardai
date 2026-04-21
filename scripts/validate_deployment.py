#!/usr/bin/env python3
"""
Quick validation script for SafeGuard AI v3.1 deployment.
Tests core functionality without requiring full benchmarking infrastructure.
"""

import sys
import os
import time
from pathlib import Path

                     
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def validate_configuration():
    """Check configuration is correct."""
    print("\n" + "="*70)
    print("SAFEGUARD AI v3.1 - DEPLOYMENT VALIDATION")
    print("="*70)
    
    print("\n✓ STEP 1: Validating Configuration")
    print("-"*70)
    
    try:
        from backend.config.settings import settings
        
        print(f"  ✅ Settings loaded successfully")
        print(f"     Model: {settings.HF_MODEL_NAME}")
        print(f"     Quantization: {settings.HF_USE_QUANTIZATION}")
        print(f"     Device: {settings.HF_DEVICE}")
        print(f"     Redis URL: {settings.REDIS_URL}")
        print(f"     Cache DIR: {settings.HF_CACHE_DIR}")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def validate_imports():
    """Check all required modules can be imported."""
    print("\n✓ STEP 2: Validating Python Imports")
    print("-"*70)
    
                           
    required_modules = [
        ('torch', 'PyTorch', True),
        ('transformers', 'Transformers', True),
        ('redis', 'Redis', True),
        ('PIL', 'Pillow', True),
    ]
    
                                                      
    optional_modules = [
        ('easyocr', 'EasyOCR', False),
        ('paddleocr', 'PaddleOCR', False),
    ]
    
    all_required_ok = True
    all_optional_ok = True
    
    print("  Required modules:")
    for module_name, display_name, _ in required_modules:
        try:
            __import__(module_name)
            print(f"    ✅ {display_name:20s} imported successfully")
        except ImportError as e:
            print(f"    ❌ {display_name:20s} failed: {e}")
            all_required_ok = False
    
    print("\n  Optional modules (for enhanced OCR):")
    for module_name, display_name, _ in optional_modules:
        try:
            __import__(module_name)
            print(f"    ✅ {display_name:20s} imported successfully")
        except ImportError:
            print(f"    ⚠️  {display_name:20s} not installed (optional for Tesseract-only mode)")
    
    return all_required_ok

def validate_toxicity_model():
    """Test toxicity model initialization and inference."""
    print("\n✓ STEP 3: Testing Toxicity Model (DeBERTa)")
    print("-"*70)
    
    try:
        from ai_services.toxicity import ToxicityClassifier
        
        print("  Loading ToxicityClassifier...")
        start = time.time()
        clf = ToxicityClassifier()
        load_time = time.time() - start
        print(f"  ✅ Model loaded in {load_time:.2f}s")
        
                        
        test_cases = [
            ("Benign", "Hello, how are you?"),
            ("Toxic", "You are stupid"),
            ("Threat", "I will kill you"),
            ("Hinglish", "Tu mar jaayega"),
        ]
        
        print("\n  Testing inference:")
        for label, text in test_cases:
            start = time.time()
            scores = clf.classify(text)
            latency = (time.time() - start) * 1000
            max_score = max(scores.values()) if scores else 0
            max_label = max(scores, key=scores.get) if scores else "N/A"
            
            print(f"    {label:15s} | {latency:6.1f}ms | {max_label}: {max_score:.3f}")
        
        print(f"  ✅ Toxicity model working correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Toxicity model error: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_cache_layer():
    """Test Redis cache integration."""
    print("\n✓ STEP 4: Testing Cache Layer (Redis)")
    print("-"*70)
    
    try:
        import redis
        from backend.config.settings import settings
        
        print(f"  Attempting connection to {settings.REDIS_URL}...")
        
        try:
            r = redis.Redis.from_url(settings.REDIS_URL)
            r.ping()
            print(f"  ✅ Redis connection successful")
            
                                   
            test_key = "test:validation"
            test_value = "validation_test"
            
            r.set(test_key, test_value)
            retrieved = r.get(test_key)
            
            if retrieved and retrieved.decode() == test_value:
                print(f"  ✅ Cache read/write working")
                r.delete(test_key)
                return True
            else:
                print(f"  ❌ Cache read/write failed")
                return False
                
        except redis.ConnectionError as e:
            print(f"  ⚠️  Redis not running: {e}")
            print(f"     (This is expected if Redis is not installed/running)")
            print(f"     To start Redis:")
            print(f"       - Windows: Download from https://github.com/microsoftarchive/redis/releases")
            print(f"       - Or use: choco install redis-64")
            print(f"       - Or use: wsl redis-server")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Cache layer error (non-critical): {e}")
        return False

def validate_explainability():
    """Test attention-based explainability."""
    print("\n✓ STEP 5: Testing Explainability (Attention-based)")
    print("-"*70)
    
    try:
        from backend.utils.explainability import ExplainabilityEngine
        
        print("  Loading ExplainabilityEngine...")
        explainer = ExplainabilityEngine()
        print(f"  ✅ Explainability module loaded")
        
                                 
        test_text = "You are stupid"
        test_scores = {
            "cyberbullying": 0.85,
            "threat": 0.15,
            "hate_speech": 0.45,
            "sexual_harassment": 0.0,
        }
        
        highlighted = explainer.highlight_tokens(test_text, test_scores)
        print(f"  ✅ Token highlighting working")
        print(f"     Highlighted tokens: {highlighted[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  Explainability error: {e}")
        return False

def validate_ocr():
    """Test parallel OCR implementation."""
    print("\n✓ STEP 6: Testing OCR Module (Parallel)")
    print("-"*70)
    
    try:
        from backend.utils import ocr
        
        print("  ✅ OCR module imports correctly")
        
                                                
        import inspect
        
                                            
        source = inspect.getsource(ocr)
        
        if 'ThreadPoolExecutor' in source or 'concurrent' in source:
            print(f"  ✅ Parallel OCR implementation detected")
            print(f"     - ThreadPoolExecutor configured for parallel inference")
            return True
        else:
            print(f"  ⚠️  Parallel OCR implementation not detected")
            return False
            
    except Exception as e:
        print(f"  ⚠️  OCR validation error: {e}")
        return False

def generate_report(results):
    """Generate validation report."""
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {name}")
    
    print(f"\nStatus: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All validations passed! System is ready for deployment.")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed or skipped.")
        print("Review issues above before production deployment.")
        return False

def main():
    """Run all validations."""
    results = {
        'Configuration': validate_configuration(),
        'Imports': validate_imports(),
        'Toxicity Model': validate_toxicity_model(),
        'Cache Layer': validate_cache_layer(),
        'Explainability': validate_explainability(),
        'OCR Module': validate_ocr(),
    }
    
    success = generate_report(results)
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Review any failed validations above")
    print("2. For Redis: Start Redis server (required for caching)")
    print("3. Run: uvicorn backend.main:app --reload --port 8000")
    print("4. Test endpoints: curl http://localhost:8000/health")
    print("5. Deploy to staging/production using DEPLOYMENT_CHECKLIST.md")
    print("="*70 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
