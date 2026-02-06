"""Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field


# ── Auth ───────────────────────────────────────────────


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "customer"
    customer_id: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    customer_id: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    token: str
    user: UserOut


# ── Notification ───────────────────────────────────────


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    link: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Customer ───────────────────────────────────────────


class CustomerCreate(BaseModel):
    name: str
    company: str
    email: str
    phone: str | None = None
    industry: str | None = None
    contract_type: str = "standard"


class CustomerOut(CustomerCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Staffing Request ───────────────────────────────────


class StaffingRequestCreate(BaseModel):
    customer_id: str
    title: str
    description: str
    required_skills: list[str] = Field(default_factory=list)
    number_of_consultants: int = 1
    start_date: datetime | None = None
    end_date: datetime | None = None
    budget_max_hourly: float | None = None
    location: str | None = None
    remote_ok: bool = False
    priority: str = "medium"


class StaffingRequestOut(BaseModel):
    id: str
    customer_id: str
    title: str
    description: str
    required_skills: list[str] | str | None = None
    number_of_consultants: int
    start_date: datetime | None
    end_date: datetime | None
    budget_max_hourly: float | None
    location: str | None
    remote_ok: bool
    priority: str
    status: str
    ai_summary: str | None = None
    ai_category: str | None = None
    ai_complexity_score: float | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Feasibility Assessment ─────────────────────────────


class FeasibilityAssessmentOut(BaseModel):
    id: str
    request_id: str
    overall_rating: str
    confidence_score: float
    availability_score: float
    skills_match_score: float
    budget_fit_score: float
    timeline_score: float
    compliance_score: float
    matching_consultants: list | str | None = None
    risks: list | str | None = None
    recommendations: list | str | None = None
    alternatives: list | str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Coordination Action ────────────────────────────────


class CoordinationActionOut(BaseModel):
    id: str
    request_id: str
    action_type: str
    description: str
    status: str
    assigned_to: str | None
    result: str | None
    order: int
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


# ── Timeline Event ─────────────────────────────────────


class TimelineEventOut(BaseModel):
    id: str
    request_id: str
    event_type: str
    title: str
    description: str | None
    actor: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Consultant ─────────────────────────────────────────


class ConsultantOut(BaseModel):
    id: str
    name: str
    email: str
    title: str | None
    skills: list | str | None = None
    hourly_rate: float
    status: str
    availability_date: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Assignment ─────────────────────────────────────────


class AssignmentOut(BaseModel):
    id: str
    request_id: str
    consultant_id: str
    start_date: datetime
    end_date: datetime | None
    hourly_rate: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentDetailOut(BaseModel):
    """Assignment with consultant details embedded."""
    id: str
    request_id: str
    consultant_id: str
    consultant_name: str = ""
    consultant_title: str | None = None
    consultant_skills: list[str] = []
    start_date: datetime
    end_date: datetime | None
    hourly_rate: float
    status: str  # proposed, sent, confirmed, rejected, active, ended
    created_at: datetime


# ── Matching Consultant (enriched) ─────────────────────


class MatchingConsultantOut(BaseModel):
    id: str
    name: str
    title: str | None = None
    skills: list[str] = []
    hourly_rate: float
    status: str
    match_score: float = 0.0  # 0-100 how well they match
    matching_skills: list[str] = []  # which required skills they have
    missing_skills: list[str] = []  # which required skills they lack


# ── Dashboard / Analytics ──────────────────────────────


class DashboardStats(BaseModel):
    total_requests: int
    pending_requests: int
    active_requests: int
    completed_requests: int
    avg_response_time_hours: float
    feasibility_rate: float
    total_consultants: int
    available_consultants: int
    compliance_score: float


class RequestDetail(BaseModel):
    request: StaffingRequestOut
    customer: CustomerOut
    assessment: FeasibilityAssessmentOut | None = None
    matching_consultants: list[MatchingConsultantOut] = []
    actions: list[CoordinationActionOut] = []
    timeline: list[TimelineEventOut] = []
    assignments: list[AssignmentDetailOut] = []
