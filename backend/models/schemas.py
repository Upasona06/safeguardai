"""
Pydantic data models for request validation and response serialisation.
All API contracts are defined here.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import uuid


                                                                   
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
MessageRole = Literal["sender", "receiver"]


                                                                   
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)


class ConversationMessage(BaseModel):
    role: MessageRole
    text: str
    timestamp: Optional[str] = None


class ContextAnalysisRequest(BaseModel):
    messages: List[ConversationMessage] = Field(..., min_length=2, max_length=100)


class GenerateFIRRequest(BaseModel):
    analysis_id: str


class FinalizeFIRRequest(BaseModel):
    fir_id: str
    analysis_id: str
    complainant_name: str
    complainant_contact: str
    complainant_address: Optional[str] = ""
    accused_name: Optional[str] = ""                                   
    accused_details: Optional[str] = ""                                             
    incident_date: str
    incident_time: Optional[str] = ""               
    incident_location: Optional[str] = ""                               
    additional_info: Optional[str] = ""
    legal_sections: List[str] = []
    evidence_urls: List[str] = []


                                                                   
class ToxicToken(BaseModel):
    token: str
    score: float
    category: str


class LegalMapping(BaseModel):
    law: str
    section: str
    description: str
    severity: str


class CategoryScores(BaseModel):
    cyberbullying: float = 0.0
    threat: float = 0.0
    hate_speech: float = 0.0
    sexual_harassment: float = 0.0
    grooming: float = 0.0


                                                                   
class AnalysisResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    risk_level: RiskLevel
    overall_score: float
    labels: CategoryScores
    toxic_tokens: List[ToxicToken]
    original_text: str
    highlighted_text: str
    legal_mappings: List[LegalMapping]
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language_detected: str = "en"
    image_url: Optional[str] = None
    fir_id: Optional[str] = None


class FIRCreateResponse(BaseModel):
    fir_id: str
    status: str = "created"
    message: str


class FIRHistoryItem(BaseModel):
    fir_id: str
    status: str
    complainant_name: str
    accused_name: Optional[str] = None
    incident_date: str
    incident_location: Optional[str] = None
    created_at: datetime
    finalized_at: Optional[datetime] = None
    pdf_url: Optional[str] = None


class FIRHistoryResponse(BaseModel):
    firs: List[FIRHistoryItem]
    total: int


class FIRFinalizeResponse(BaseModel):
    fir_id: str
    pdf_url: str
    status: str = "finalized"


class AnalyticsResponse(BaseModel):
    total_reports: int
    critical_cases: int
    fir_generated: int
    avg_response_time: float
    daily_counts: List[Dict]
    category_breakdown: Dict[str, int]
