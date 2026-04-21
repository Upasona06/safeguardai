"""
XLM-RoBERTa-Based Toxicity & Harm Detection
Replaces DeBERTa for better multilingual + Hinglish support
"""

import logging
import torch
import numpy as np
from typing import Dict, List, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import re
from functools import lru_cache

logger = logging.getLogger(__name__)


class XLMRoBERTaAnalyzer:
    """
    Multilingual toxicity detection using XLM-RoBERTa
    Supports: English, Hindi, Bengali, Hinglish + code-switching
    """
    
                               
    HINGLISH_SLANG = {
        'bewakoof': 'fool',
        'chutiya': 'idiot',
        'gandu': 'asshole',
        'sala': 'damn',
        'saali': 'damn',
        'mara': 'killed',
        'khatam kar': 'will kill',
        'jaan se mara': 'killed from life',
        'mujhe': 'me',
        'tujhe': 'you',
        'tera': 'your',
        'mera': 'my',
        'chhod': 'leave',
        'maat kar': 'don\'t do',
        'padha': 'beat',
        'marunga': 'will beat',
        'gali dena': 'abuse',
        'jhooth': 'lie',
        'pagal': 'crazy',
        'nalayak': 'useless',
        'haraami': 'bastard',
        'gaandu': 'asshole',
    }
    
    def __init__(
        self, 
        model_name: str = "xlm-roberta-large",
        use_quantization: bool = True,
        device: str = "cuda",
        cache_dir: str = "/models/huggingface"
    ):
        """
        Initialize XLM-RoBERTa analyzer
        
        Args:
            model_name: HuggingFace model ID
            use_quantization: Use INT8 quantization for speed/memory
            device: cuda or cpu
            cache_dir: HuggingFace cache directory
        """
        self.model_name = model_name
        self.use_quantization = use_quantization
        self.device = device
        self.cache_dir = cache_dir
        
        logger.info(f"Loading {model_name}...")
        
                                  
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=2,
            output_attentions=True,
            cache_dir=cache_dir
        )
        
                                       
        if use_quantization:
            self.model = torch.quantization.quantize_dynamic(
                self.model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            logger.info("✅ Model quantized to INT8 (4x faster, 75% smaller)")
        
        self.model.to(device)
        self.model.eval()
    
    def detect_language(self, text: str) -> Dict[str, str]:
        """
        Detect language: en, hi, bn, or hinglish
        """
        try:
            from langdetect import detect_langs
        except ImportError:
            logger.warning("langdetect not installed. Defaulting to English.")
            return {'detected': 'en', 'confidence': 0.5, 'is_codemixed': False}
        
        try:
            langs = detect_langs(text)
            primary = langs[0].lang
            confidence = langs[0].prob
        except:
            primary = 'en'
            confidence = 0.5
        
                                                     
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]+', text))
        
                                 
        if devanagari_chars > 0 and latin_chars > 0:
            detected = 'hinglish'
            is_codemixed = True
        elif devanagari_chars > latin_chars:
            detected = 'hi'
            is_codemixed = False
        else:
            detected = primary if primary in ['en', 'hi', 'bn'] else 'en'
            is_codemixed = False
        
        return {
            'detected': detected,
            'confidence': float(confidence),
            'is_codemixed': is_codemixed,
            'devanagari_chars': devanagari_chars,
            'latin_chars': latin_chars
        }
    
    def normalize_hinglish(self, text: str) -> str:
        """
        Normalize Hinglish text for better model understanding
        """
        normalized = text.lower()
        
                                                
        for hinglish, english in self.HINGLISH_SLANG.items():
                                    
            normalized = re.sub(
                r'\b' + hinglish + r'\b',
                english,
                normalized,
                flags=re.IGNORECASE
            )
        
                                
        normalized = re.sub(r'ega\b', 'will', normalized)                     
        normalized = re.sub(r'ungi?\b', 'will', normalized)                    
        
        return normalized
    
    def preprocess_text(self, text: str, language: str) -> str:
        """
        Preprocess text based on detected language
        """
                            
        if language == 'hinglish':
            text = self.normalize_hinglish(text)
        
                                 
        text = ' '.join(text.split())
        
                                      
        text = text[:512]
        
        return text
    
    @torch.no_grad()
    def predict_toxicity_binary(self, text: str) -> Dict:
        """
        Binary toxicity classification (toxic/non-toxic)
        """
                         
        lang_info = self.detect_language(text)
        language = lang_info['detected']
        
                    
        processed_text = self.preprocess_text(text, language)
        
                  
        tokens = self.tokenizer(
            processed_text,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        ).to(self.device)
        
                      
        outputs = self.model(**tokens)
        
                        
        logits = outputs.logits[0]
        scores = torch.softmax(logits, dim=-1)
        toxic_score = scores[1].item()                   
        
                                               
        attentions = outputs.attentions[-1][0, -1, :]                         
        
        return {
            'toxic_score': toxic_score,
            'label': 'toxic' if toxic_score > 0.5 else 'safe',
            'confidence': max(scores.tolist()),
            'language': language,
            'is_codemixed': lang_info['is_codemixed'],
            'attentions': attentions.cpu().numpy()
        }
    
    @torch.no_grad()
    def predict_multilabel(self, text: str) -> Dict:
        """
        Multi-label classification with XLM-RoBERTa
        Categories: cyberbullying, threat, hate_speech, sexual_harassment, grooming
        
        In production, use separate fine-tuned heads per category
        For now: approximate scores based on pattern matching + base model
        """
        binary_result = self.predict_toxicity_binary(text)
        base_score = binary_result['toxic_score']
        language = binary_result['language']
        
                                              
        text_lower = text.lower()
        processed = self.preprocess_text(text, language)
        
                           
        categories = {
            'cyberbullying': {
                'patterns': ['stupid', 'idiot', 'fool', 'dumb', 'loser', 'hate', 'chutiya', 'gandu'],
                'score': 0.0
            },
            'threat': {
                'patterns': ['kill', 'murder', 'beat', 'punch', 'hurt', 'khatam', 'marunga'],
                'score': 0.0
            },
            'hate_speech': {
                'patterns': ['muslim', 'hindu', 'christian', 'jewish', 'gay', 'lesbian', 'transgender'],
                'score': 0.0
            },
            'sexual_harassment': {
                'patterns': ['sex', 'dick', 'pussy', 'boobs', 'porn', 'rape', 'sexual'],
                'score': 0.0
            },
            'grooming': {
                'patterns': ['meet', 'private', 'alone', 'secret', 'tell no one', 'age'],
                'score': 0.0
            }
        }
        
                                   
        for category, info in categories.items():
            pattern_matches = sum(1 for p in info['patterns'] if p in text_lower)
            
            if pattern_matches > 0:
                                                                
                categories[category]['score'] = min(
                    0.95,
                    base_score * 0.5 + (pattern_matches / len(info['patterns'])) * 0.5
                )
            else:
                categories[category]['score'] = base_score * 0.3                  
        
        return {
            'overall_score': base_score,
            'categories': {k: v['score'] for k, v in categories.items()},
            'language': language,
            'is_codemixed': binary_result['is_codemixed'],
            'confidence': binary_result['confidence']
        }
    
    def explain_prediction(self, text: str, target_score: float = None) -> Dict:
        """
        Generate token-level explanation of prediction
        """
        result = self.predict_toxicity_binary(text)
        
                                
        tokens = self.tokenizer(
            text,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        token_ids = tokens['input_ids'][0]
        token_strs = self.tokenizer.convert_ids_to_tokens(token_ids)
        
                               
        attention_scores = result['attentions']
        
                             
        att_min, att_max = attention_scores.min(), attention_scores.max()
        normalized_att = (attention_scores - att_min) / (att_max - att_min + 1e-8)
        
                       
        token_explanations = []
        for token, att_score in zip(token_strs, normalized_att):
            if token not in ['[CLS]', '[SEP]', '[PAD]', '▁']:
                token_explanations.append({
                    'token': token.replace('▁', ' '),
                    'attention': float(att_score),
                    'importance': (
                        'HIGH' if att_score > 0.7 else 
                        'MEDIUM' if att_score > 0.3 else 
                        'LOW'
                    )
                })
        
                            
        token_explanations.sort(key=lambda x: x['attention'], reverse=True)
        
        return {
            'toxic_score': result['toxic_score'],
            'label': result['label'],
            'language': result['language'],
            'top_tokens': token_explanations[:10],                           
            'full_tokens': token_explanations
        }


                                             
class MultiTaskXLMRoBERTa:
    """
    Multi-task learning with shared XLM-RoBERTa + category-specific heads
    For production deployment
    """
    
    def __init__(
        self,
        base_model: str = "xlm-roberta-large",
        checkpoint_path: Optional[str] = None
    ):
        self.base_model_name = base_model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
                              
        if checkpoint_path:
            self.model = torch.load(checkpoint_path)
        else:
            self.model = self._build_model()
        
        self.model.to(self.device)
        self.model.eval()
    
    def _build_model(self):
        """Build multi-task model architecture"""
        
                                                                       
                                  
        from transformers import AutoModelForSequenceClassification
        
        return AutoModelForSequenceClassification.from_pretrained(
            self.base_model_name,
            num_labels=2
        )
    
    @torch.no_grad()
    def predict(self, text: str):
        """Predict all categories"""
                                                                         
        pass


                     
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/text")
async def analyze_text(content: dict):
    """
    Analyze text for harmful content
    
    Request:
    {
        "content": "I will kill you",
        "language": "auto",
        "include_explanation": true
    }
    """
    
    text = content.get('content', '')
    if not text or len(text.strip()) == 0:
        return {'error': 'Empty content'}, 400
    
                                                             
    analyzer = XLMRoBERTaAnalyzer(
        model_name="xlm-roberta-large",
        use_quantization=True
    )
    
             
    multilabel = analyzer.predict_multilabel(text)
    
    response = {
        'analysis_id': f"ANAL-{np.random.randint(1000, 9999)}",
        'overall_score': multilabel['overall_score'],
        'risk_level': 'CRITICAL' if multilabel['overall_score'] > 0.8 else 'HIGH' if multilabel['overall_score'] > 0.6 else 'MEDIUM' if multilabel['overall_score'] > 0.3 else 'LOW',
        'category_scores': multilabel['categories'],
        'language': multilabel['language'],
        'is_codemixed': multilabel['is_codemixed'],
        'confidence': multilabel['confidence']
    }
    
                                  
    if content.get('include_explanation'):
        explanation = analyzer.explain_prediction(text)
        response['explanation'] = explanation
    
    return response


@router.post("/explain")
async def explain_analysis(content: dict):
    """Get detailed explanation for text analysis"""
    
    text = content.get('content', '')
    analyzer = XLMRoBERTaAnalyzer()
    
    return analyzer.explain_prediction(text)
