# models/data_models.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TrendTopic(BaseModel):
    """Model representing a trending topic."""
    topic: str
    score: float
    sources: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class TrendAnalysisResult(BaseModel):
    """Results of trend analysis."""
    trends: List[TrendTopic] = Field(default_factory=list)
    industry_relevance: Dict[str, float] = Field(default_factory=dict)
    date_range: Dict[str, str] = Field(default_factory=dict)
    summary: str = ""