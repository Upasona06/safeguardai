"""
MultilingualProcessor — Language detection and text normalization.

Handles:
  - Hindi (Devanagari)
  - Hinglish (Roman-script Hindi)
  - Bengali (বাংলা)
  - English
  - L33tspeak / obfuscation stripping

Uses langdetect for language identification.
"""

import logging
import re
import unicodedata
from typing import Tuple

logger = logging.getLogger(__name__)

                                                                    
L33T_MAP = {
    "0": "o", "1": "i", "3": "e", "4": "a",
    "5": "s", "6": "g", "7": "t", "8": "b", "@": "a",
    "$": "s", "!": "i", "|": "i",
}

                                                                    
HINGLISH_NORM = {
    r"\bbc\b": "motherfucker",
    r"\bmc\b": "motherfucker",
    r"\bbsdk\b": "bastard",
    r"\bmadarchod\b": "motherfucker",
    r"\bbehenchod\b": "motherfucker",
    r"\brandi\b": "whore",
    r"\blund\b": "dick",
    r"\bbhosdike\b": "bastard",
    r"\bbk\b": "bastard",
    r"\bchutiya\b": "idiot",
    r"\bbewakoof\b": "stupid",
    r"\bgandu\b": "asshole",
    r"\bkamina\b": "scoundrel",
    r"\bmaar dalenge\b": "will kill",
    r"\bjaan se marunga\b": "will kill",
    r"\bkhatam kar dunga\b": "will finish off",
    r"\bchod dene\b": "abandon",
}

                                                                                     
                                                                        
INDIC_NORM = {
                        
    r"मादरचोद|मदरचोद": "motherfucker",
    r"बहनचोद|बहनचोद": "motherfucker",
    r"चूतिया|चुतिया": "idiot",
    r"हरामी": "bastard",
    r"रंडी": "whore",
    r"भोसड़ीके|भोसडीके": "bastard",
    r"मार दूंगा|मार दूँगा|जान से मार": "will kill",
    r"बलात्कार": "rape",

             
    r"শুয়োরের বাচ্চা|শুয়োরের বাচ্চা": "bastard",
    r"বেশ্যা": "whore",
    r"চোদ": "fuck",
    r"ধর্ষণ": "rape",
    r"মেরে ফেলব|খুন করব": "will kill",
}

                                                                    
SUPPORTED_LANGS = {"en", "hi", "bn", "ur"}


class MultilingualProcessor:
    def __init__(self):
        self._langdetect_available = self._check_langdetect()

    def _check_langdetect(self) -> bool:
        try:
            import langdetect
            return True
        except ImportError:
            logger.warning("langdetect not installed — defaulting to 'en'")
            return False

    def process(self, text: str) -> Tuple[str, str]:
        """
        Returns (language_code, normalized_text).
        """
                            
        lang = self._detect_language(text)

                                        
        normalized = self._strip_leet(text)

                                      
        normalized = self._normalize_hinglish(normalized)

                                                              
        normalized = self._normalize_indic_terms(normalized)

                                                                    
        normalized = self._normalize_spacing_obfuscation(normalized)

                                  
        normalized = unicodedata.normalize("NFC", normalized)

                                                       
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return lang, normalized

    def _detect_language(self, text: str) -> str:
        if not self._langdetect_available:
            return self._heuristic_detect(text)
        try:
            from langdetect import detect
            lang = detect(text)
            return lang if lang in SUPPORTED_LANGS else "en"
        except Exception:
            return self._heuristic_detect(text)

    def _heuristic_detect(self, text: str) -> str:
        """Simple heuristic for language detection without langdetect."""
        devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        bengali = sum(1 for c in text if "\u0980" <= c <= "\u09FF")
        total = max(len(text), 1)

        if devanagari / total > 0.15:
            return "hi"
        if bengali / total > 0.15:
            return "bn"
        return "en"

    def _strip_leet(self, text: str) -> str:
        """Replace l33t characters with their alphabetic equivalents."""
        result = []
        for char in text:
            result.append(L33T_MAP.get(char, char))
        return "".join(result)

    def _normalize_hinglish(self, text: str) -> str:
        """Replace common Hinglish abuse terms with English equivalents for better model performance."""
        for pattern, replacement in HINGLISH_NORM.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _normalize_indic_terms(self, text: str) -> str:
        """Replace common Hindi/Bengali script abuse/toxic terms with English equivalents."""
        for pattern, replacement in INDIC_NORM.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _normalize_spacing_obfuscation(self, text: str) -> str:
        """Collapse spaced single-letter sequences (e.g. 'f u c k')."""
        return re.sub(
            r"\b(?:[a-zA-Z]\s+){2,}[a-zA-Z]\b",
            lambda m: m.group(0).replace(" ", ""),
            text,
        )
