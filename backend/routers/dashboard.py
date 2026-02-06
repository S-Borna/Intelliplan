"""Dashboard and analytics endpoints."""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Consultant,
    ConsultantStatus,
    StaffingRequest,
    RequestStatus,
)
from backend.schemas import ConsultantOut, DashboardStats

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overview statistics for the dashboard."""
    requests = db.query(StaffingRequest).all()
    consultants = db.query(Consultant).all()

    total = len(requests)
    pending = len([r for r in requests if r.status in (RequestStatus.SUBMITTED, RequestStatus.ANALYZING)])
    active = len([r for r in requests if r.status in (RequestStatus.ASSESSED, RequestStatus.IN_PROGRESS)])
    completed = len([r for r in requests if r.status == RequestStatus.COMPLETED])
    available = len([c for c in consultants if c.status == ConsultantStatus.AVAILABLE])

    # Calculate average feasibility score as proxy for compliance
    compliance_scores = []
    for r in requests:
        if r.assessment and r.assessment.compliance_score:
            compliance_scores.append(r.assessment.compliance_score)
    avg_compliance = sum(compliance_scores) / max(len(compliance_scores), 1)

    feasibility_count = len([r for r in requests if r.assessment and r.assessment.overall_rating in ("high", "medium")])
    feasibility_rate = feasibility_count / max(total, 1)

    return DashboardStats(
        total_requests=total,
        pending_requests=pending,
        active_requests=active,
        completed_requests=completed,
        avg_response_time_hours=2.4,  # Simulated
        feasibility_rate=round(feasibility_rate, 2),
        total_consultants=len(consultants),
        available_consultants=available,
        compliance_score=round(avg_compliance, 1),
    )


@router.get("/consultants", response_model=list[ConsultantOut])
def list_consultants(status: str | None = None, db: Session = Depends(get_db)):
    """List all consultants, optionally filtered by status."""
    query = db.query(Consultant).order_by(Consultant.name)
    if status:
        query = query.filter(Consultant.status == status)

    results = []
    for c in query.all():
        data = ConsultantOut.model_validate(c)
        if isinstance(c.skills, str):
            try:
                data.skills = json.loads(c.skills)
            except (json.JSONDecodeError, TypeError):
                data.skills = [c.skills]
        results.append(data)
    return results
