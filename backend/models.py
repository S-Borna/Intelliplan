"""SQLAlchemy ORM models for Intelliplan."""

from datetime import datetime, timezone
import enum
import hashlib
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    """Simple SHA-256 password hashing (demo-grade)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ── Enums ──────────────────────────────────────────────


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    HANDLER = "handler"
    ADMIN = "admin"


class RequestStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    ASSESSED = "assessed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FeasibilityRating(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_FEASIBLE = "not_feasible"


class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ConsultantStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_LEAVE = "on_leave"
    ENDING_SOON = "ending_soon"


# ── Models ─────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    last_login = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="users")
    notifications = relationship("Notification", back_populates="user")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")  # info, success, warning, urgent
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)  # optional deep-link to request
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="notifications")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    phone = Column(String(50))
    industry = Column(String(100))
    contract_type = Column(String(50), default="standard")
    created_at = Column(DateTime, default=_utcnow)

    requests = relationship("StaffingRequest", back_populates="customer")
    users = relationship("User", back_populates="customer")


class Consultant(Base):
    __tablename__ = "consultants"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    title = Column(String(200))
    skills = Column(Text)  # JSON-encoded list
    hourly_rate = Column(Float, default=0)
    status = Column(Enum(ConsultantStatus), default=ConsultantStatus.AVAILABLE)
    availability_date = Column(DateTime, nullable=True)
    current_customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    assignments = relationship("Assignment", back_populates="consultant")


class StaffingRequest(Base):
    __tablename__ = "staffing_requests"

    id = Column(String, primary_key=True, default=_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(Text)  # JSON-encoded list
    number_of_consultants = Column(Integer, default=1)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    budget_max_hourly = Column(Float, nullable=True)
    location = Column(String(200))
    remote_ok = Column(Boolean, default=False)
    priority = Column(Enum(RequestPriority), default=RequestPriority.MEDIUM)
    status = Column(Enum(RequestStatus), default=RequestStatus.SUBMITTED)

    # AI-enriched fields
    ai_summary = Column(Text, nullable=True)
    ai_category = Column(String(100), nullable=True)
    ai_complexity_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer = relationship("Customer", back_populates="requests")
    assessment = relationship("FeasibilityAssessment", back_populates="request", uselist=False)
    actions = relationship("CoordinationAction", back_populates="request")
    timeline_events = relationship("TimelineEvent", back_populates="request")
    assignments = relationship("Assignment", back_populates="request")


class FeasibilityAssessment(Base):
    __tablename__ = "feasibility_assessments"

    id = Column(String, primary_key=True, default=_uuid)
    request_id = Column(String, ForeignKey("staffing_requests.id"), nullable=False, unique=True)

    overall_rating = Column(Enum(FeasibilityRating), nullable=False)
    confidence_score = Column(Float, default=0.0)  # 0-1

    # Sub-scores (0-100)
    availability_score = Column(Float, default=0)
    skills_match_score = Column(Float, default=0)
    budget_fit_score = Column(Float, default=0)
    timeline_score = Column(Float, default=0)
    compliance_score = Column(Float, default=0)

    matching_consultants = Column(Text)  # JSON list of consultant IDs
    risks = Column(Text)  # JSON list of risk strings
    recommendations = Column(Text)  # JSON list
    alternatives = Column(Text)  # JSON list of alternative suggestions

    created_at = Column(DateTime, default=_utcnow)

    request = relationship("StaffingRequest", back_populates="assessment")


class CoordinationAction(Base):
    __tablename__ = "coordination_actions"

    id = Column(String, primary_key=True, default=_uuid)
    request_id = Column(String, ForeignKey("staffing_requests.id"), nullable=False)
    action_type = Column(String(100), nullable=False)  # e.g., "notify_consultant", "check_compliance"
    description = Column(Text, nullable=False)
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    assigned_to = Column(String(200), nullable=True)
    result = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)

    request = relationship("StaffingRequest", back_populates="actions")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=_uuid)
    request_id = Column(String, ForeignKey("staffing_requests.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    actor = Column(String(200))  # Who/what caused this event
    created_at = Column(DateTime, default=_utcnow)

    request = relationship("StaffingRequest", back_populates="timeline_events")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True, default=_uuid)
    request_id = Column(String, ForeignKey("staffing_requests.id"), nullable=False)
    consultant_id = Column(String, ForeignKey("consultants.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    hourly_rate = Column(Float, nullable=False)
    status = Column(String(50), default="proposed")  # proposed, confirmed, active, ended
    created_at = Column(DateTime, default=_utcnow)

    request = relationship("StaffingRequest", back_populates="assignments")
    consultant = relationship("Consultant", back_populates="assignments")


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    rule_type = Column(String(100))  # "contract", "regulation", "policy"
    condition = Column(Text)  # JSON-encoded rule logic
    severity = Column(String(50), default="warning")  # "info", "warning", "blocking"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
