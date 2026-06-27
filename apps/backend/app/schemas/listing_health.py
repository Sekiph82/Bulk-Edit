from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class HealthGrade(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_WORK = "needs_work"
    CRITICAL = "critical"


class HealthPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthIssueOut(BaseModel):
    category: str
    severity: IssueSeverity
    field: str
    message: str
    recommended_fix: str
    ai_can_help: bool = False


class ListingHealthRow(BaseModel):
    listing_id: str
    title: Optional[str] = None
    state: Optional[str] = None
    score: int
    grade: HealthGrade
    priority: HealthPriority
    issue_count: int
    top_issues: List[HealthIssueOut]
    photo_count: int
    tag_count: int
    has_video: bool
    price: Optional[float] = None
    currency: Optional[str] = None
    last_synced_at: Optional[datetime] = None


class ListingHealthDetail(ListingHealthRow):
    all_issues: List[HealthIssueOut]
    suggested_actions: List[str]


class ListingHealthSummary(BaseModel):
    average_score: float
    total_listings: int
    excellent_count: int
    good_count: int
    needs_work_count: int
    critical_count: int
    high_priority_count: int
    top_issue_categories: List[str]
    last_calculated_at: datetime


class ListingHealthPage(BaseModel):
    items: List[ListingHealthRow]
    total: int
    page: int
    page_size: int


class AISuggestionsOut(BaseModel):
    listing_id: str
    improved_title: Optional[str] = None
    suggested_tags: Optional[List[str]] = None
    improved_description: Optional[str] = None
    explanation: Optional[str] = None
    confidence: Optional[str] = None
    ai_available: bool
    message: Optional[str] = None
