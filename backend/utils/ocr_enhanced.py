"""
Enhanced OCR Pipeline with Preprocessing & Multi-Engine Fallback
Fixes: "No text detected in image" issue
"""

import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional
import easyocr
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class RobustOCREngine:
    """Multi-engine OCR with intelligent fallback and preprocessing"""
    
    def __init__(self, languages: list = None):
        self.languages = languages or ['en', 'hi', 'bn']
        self.easyocr_reader = None
        self.tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            logger.warning("Tesseract not available. Install: apt-get install tesseract-ocr")
            return False
    
    def preprocess_image(self, image_input) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        - Contrast enhancement
        - Denoising
        - Deskewing
        - Thresholding
        """
                    
        if isinstance(image_input, str):
            img = cv2.imread(image_input)
        else:
            img = image_input
        
        if img is None:
            raise ValueError("Could not load image")
        
                              
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        logger.debug("Step 1: Grayscale conversion OK")
        
                                              
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        logger.debug("Step 2: Contrast enhancement OK")
        
                                                                  
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)
        logger.debug("Step 3: Denoising OK")
        
                                                                            
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel, iterations=1)
        logger.debug("Step 4: Morphological operations OK")
        
                                              
        deskewed = self._deskew_image(morph)
        logger.debug("Step 5: Deskewing OK")
        
                                                  
        _, binary = cv2.threshold(deskewed, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        logger.debug("Step 6: Thresholding OK")
        
        return binary
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image using contour detection"""
        try:
            coords = np.column_stack(np.where(image > 0))
            if len(coords) < 4:
                return image
            
            angle = cv2.minAreaRect(cv2.convexHull(coords))[-1]
            if angle < -45:
                angle = angle + 90
            
            h, w = image.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            deskewed = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)
            
            logger.debug(f"Deskewed by {angle:.1f} degrees")
            return deskewed
        except Exception as e:
            logger.warning(f"Deskewing failed: {e}. Using original image.")
            return image
    
    def extract_text_easyocr(self, image_input) -> Dict:
        """Extract text using EasyOCR"""
        try:
            if self.easyocr_reader is None:
                logger.info("Loading EasyOCR reader...")
                self.easyocr_reader = easyocr.Reader(self.languages, gpu=True)
            
                                               
            if isinstance(image_input, str):
                result = self.easyocr_reader.readtext(image_input)
            else:
                                               
                temp_path = "/tmp/ocr_temp.png"
                cv2.imwrite(temp_path, image_input)
                result = self.easyocr_reader.readtext(temp_path)
            
            text = '\n'.join([item[1] for item in result])
            confidence = np.mean([item[2] for item in result]) if result else 0
            
            logger.info(f"EasyOCR: {len(result)} lines, confidence {confidence:.2f}")
            
            return {
                'text': text,
                'confidence': float(confidence),
                'lines_detected': len(result),
                'success': True
            }
        except Exception as e:
            logger.warning(f"EasyOCR failed: {e}")
            return {'text': '', 'confidence': 0, 'success': False, 'error': str(e)}
    
    def extract_text_paddle(self, image_input) -> Dict:
        """Extract text using PaddleOCR (better for handwriting)"""
        try:
            from paddleocr import PaddleOCR
            
            paddle = PaddleOCR(use_angle_cls=True, lang='en')
            
            if isinstance(image_input, str):
                result = paddle.ocr(image_input, cls=True)
            else:
                temp_path = "/tmp/ocr_temp.png"
                cv2.imwrite(temp_path, image_input)
                result = paddle.ocr(temp_path, cls=True)
            
            if not result or not result[0]:
                return {'text': '', 'confidence': 0, 'success': False}
            
            text = '\n'.join([item[1][0] for item in result[0]])
            confidence = np.mean([item[1][1] for item in result[0]])
            
            logger.info(f"PaddleOCR: {len(result[0])} lines, confidence {confidence:.2f}")
            
            return {
                'text': text,
                'confidence': float(confidence),
                'lines_detected': len(result[0]),
                'success': True
            }
        except Exception as e:
            logger.warning(f"PaddleOCR failed: {e}")
            return {'text': '', 'confidence': 0, 'success': False, 'error': str(e)}
    
    def extract_text_tesseract(self, image: np.ndarray) -> Dict:
        """Extract text using Tesseract (fallback)"""
        if not self.tesseract_available:
            return {'text': '', 'confidence': 0, 'success': False, 'error': 'Tesseract not available'}
        
        try:
            pil_img = Image.fromarray(image)
            text = pytesseract.image_to_string(pil_img)
            
            logger.info(f"Tesseract: extracted {len(text)} characters")
            
            return {
                'text': text,
                'confidence': 0.7,                                       
                'success': bool(text.strip())
            }
        except Exception as e:
            logger.warning(f"Tesseract failed: {e}")
            return {'text': '', 'confidence': 0, 'success': False, 'error': str(e)}
    
    def extract_text_robust(self, image_path: str) -> Dict:
        """
        Robust OCR with preprocessing and multi-engine fallback
        """
        logger.info(f"Starting robust OCR for: {image_path}")
        
                            
        try:
            preprocessed = self.preprocess_image(image_path)
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return {
                'text': '',
                'confidence': 0,
                'engine_used': None,
                'status': 'failed',
                'error': str(e)
            }
        
        results = {}
        
                                 
        logger.info("Attempting OCR with EasyOCR...")
        results['easyocr'] = self.extract_text_easyocr(image_path)
        
        logger.info("Attempting OCR with PaddleOCR...")
        results['paddle'] = self.extract_text_paddle(image_path)
        
        logger.info("Attempting OCR with Tesseract...")
        results['tesseract'] = self.extract_text_tesseract(preprocessed)
        
                                                                          
        best_engine = None
        best_confidence = -1
        
        for engine, result in results.items():
            if result['success'] and len(result.get('text', '').strip()) > 0:
                confidence = result.get('confidence', 0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_engine = engine
        
                                    
        if best_engine:
            final_result = results[best_engine]
            final_result['engine_used'] = best_engine
            final_result['status'] = 'success'
            logger.info(f"✅ OCR successful with {best_engine} (confidence: {best_confidence:.2f})")
        else:
                                                    
            all_text = '\n'.join([
                r.get('text', '') for r in results.values() 
                if r.get('success') and r.get('text', '').strip()
            ])
            final_result = {
                'text': all_text,
                'confidence': max([r.get('confidence', 0) for r in results.values()]),
                'engine_used': 'ensemble',
                'status': 'fallback' if all_text.strip() else 'failed',
                'all_results': results
            }
            logger.warning(f"⚠️ OCR using ensemble fallback")
        
        return final_result


                     
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

async def analyze_image_with_robust_ocr(file: UploadFile = File(...)):
    """FastAPI endpoint for image analysis with robust OCR"""
    
                        
    contents = await file.read()
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, 'wb') as f:
        f.write(contents)
    
             
    ocr = RobustOCREngine(languages=['en', 'hi', 'bn'])
    ocr_result = ocr.extract_text_robust(temp_path)
    
                                                
    if ocr_result['status'] == 'success' and ocr_result.get('text'):
        from backend.services.analysis_service import AnalysisService
        
        analysis_service = AnalysisService()
        toxicity_result = await analysis_service.analyze_text(ocr_result['text'])
        
        return JSONResponse({
            'ocr': ocr_result,
            'toxicity_analysis': toxicity_result
        })
    else:
        return JSONResponse({
            'ocr': ocr_result,
            'error': 'No text could be extracted from image'
        }, status_code=400)
