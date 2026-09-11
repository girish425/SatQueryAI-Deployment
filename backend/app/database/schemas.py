from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnswerDetail(BaseModel):
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    explanation: str


class TechnicalDetails(BaseModel):
    dimensions: str = "Unknown"
    bands: int = 1
    crs: str = "Unknown"
    processing_time_sec: float = 0.0
    preprocessing_info: Optional[str] = None
    data_type: Optional[str] = None


class EvidenceDetail(BaseModel):
    original_image: Optional[str] = None
    overlay_image: Optional[str] = None
    difference_image: Optional[str] = None
    bounding_box: Optional[List[int]] = None
    metric_map: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    image_ids: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    query: str
    image_ids: List[str] = Field(default_factory=list)
    intent: str
    intent_confidence: float
    model_used: str
    reason: Optional[str] = None
    answer: AnswerDetail
    evidence: EvidenceDetail
    technical_details: TechnicalDetails
    status: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MessageRecord(BaseModel):
    id: Optional[str] = None
    session_id: str
    role: str  # "user" | "assistant"
    message: str
    image_ids: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    model_used: Optional[str] = None
    answer: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    evidence: Optional[Dict[str, Any]] = None
    technical_details: Optional[Dict[str, Any]] = None


class ConversationRecord(BaseModel):
    session_id: str
    title: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: List[MessageRecord] = Field(default_factory=list)


class RetrieveRequest(BaseModel):
    query: str
    bbox: Optional[List[float]] = None
    date_range: Optional[str] = None
    satellite: Optional[str] = None
    limit: int = 6


class SatelliteImageResult(BaseModel):
    id: str
    title: str
    satellite: str
    sensor: str
    date: str
    location: str
    cloud_coverage: Optional[float] = None
    resolution: Optional[str] = None
    thumbnail_url: str
    geotiff_url: str
    description: Optional[str] = None
