"""Customer request API endpoints."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Assignment,
    Customer,
    Consultant,
    ConsultantStatus,
    StaffingRequest,
    RequestStatus,
    TimelineEvent,
    User,
    UserRole,
)
from backend.schemas import (
    StaffingRequestCreate,
    StaffingRequestOut,
    RequestDetail,
    CustomerOut,
    FeasibilityAssessmentOut,
    CoordinationActionOut,
    TimelineEventOut,
    AssignmentOut,
    AssignmentDetailOut,
    MatchingConsultantOut,
)
from backend.services.ai_engine import ai_engine
from backend.services.feasibility import feasibility_service
from backend.services.coordinator import coordinator
from backend.routers.auth import require_user
from backend.routers.notifications import notify_handlers, notify_user

router = APIRouter(prefix="/api/requests", tags=["Staffing Requests"])


@router.post("", response_model=StaffingRequestOut, status_code=201)
def create_request(data: StaffingRequestCreate, db: Session = Depends(get_db)):
    """
    Submit a new staffing request.
    AI automatically analyzes and enriches the request.
    Notifies all handlers of the new request.
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    # AI analysis
    ai_result = ai_engine.analyze_request(
        title=data.title,
        description=data.description,
        skills=data.required_skills,
    )

    # Create request with AI enrichment
    request = StaffingRequest(
        customer_id=data.customer_id,
        title=data.title,
        description=data.description,
        required_skills=json.dumps(data.required_skills),
        number_of_consultants=data.number_of_consultants,
        start_date=data.start_date,
        end_date=data.end_date,
        budget_max_hourly=data.budget_max_hourly,
        location=data.location,
        remote_ok=data.remote_ok,
        priority=data.priority,
        status=RequestStatus.SUBMITTED,
        ai_summary=ai_result["summary"],
        ai_category=ai_result["category"],
        ai_complexity_score=ai_result["complexity_score"],
    )
    db.add(request)
    db.flush()  # Generate request.id before referencing it

    # Add timeline event
    event = TimelineEvent(
        request_id=request.id,
        event_type="request_submitted",
        title="Request submitted",
        description=f"AI Category: {ai_result['category']} | Complexity: {ai_result['complexity_score']:.0%}",
        actor=customer.name,
    )
    db.add(event)

    # Notify all handlers about the new request
    priority_label = ai_result.get("detected_priority", "medium")
    ntype = "urgent" if priority_label == "urgent" else "info"
    notify_handlers(
        db,
        title=f"Ny förfrågan: {data.title}",
        message=f"{customer.company} behöver {data.title}. AI-kategori: {ai_result['category']}. Prioritet: {priority_label}.",
        notification_type=ntype,
        link=request.id,
    )

    db.commit()
    db.refresh(request)

    # Auto-trigger feasibility & action plan
    try:
        feasibility_service.assess(db, request.id)
        coordinator.create_action_plan(db, request.id)
    except Exception:
        pass  # Non-blocking

    # Notify customer user(s) that it was received
    customer_users = db.query(User).filter(User.customer_id == data.customer_id).all()
    for cu in customer_users:
        notify_user(
            db, cu.id,
            title="Förfrågan mottagen",
            message=f"Din förfrågan '{data.title}' har tagits emot och AI-analyseras nu.",
            notification_type="success",
            link=request.id,
        )
    db.commit()

    db.refresh(request)
    return _serialize_request(request)


@router.get("", response_model=list[StaffingRequestOut])
def list_requests(
    status: str | None = None,
    customer_id: str | None = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """List all staffing requests, optionally filtered by status or customer.
    If mine=true and user is a customer, only return their requests."""
    query = db.query(StaffingRequest).order_by(StaffingRequest.created_at.desc())

    if status:
        query = query.filter(StaffingRequest.status == status)
    if customer_id:
        query = query.filter(StaffingRequest.customer_id == customer_id)

    results = []
    for r in query.all():
        out = _serialize_request(r)
        # Enrich with company name
        if r.customer:
            out.company_name = r.customer.company
        # Enrich with feasibility score from assessment
        if r.assessment:
            out.feasibility_score = round(r.assessment.confidence_score * 100)
        results.append(out)
    return results


@router.get("/{request_id}", response_model=RequestDetail)
def get_request_detail(request_id: str, db: Session = Depends(get_db)):
    """Get full details of a request including assessment, actions, and timeline."""
    request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
    if not request:
        raise HTTPException(404, "Request not found")

    # Build matching consultant details from assessment
    matching_consultants_out = []
    assessment = request.assessment
    if assessment:
        matching_ids = []
        if assessment.matching_consultants:
            try:
                matching_ids = json.loads(assessment.matching_consultants) if isinstance(assessment.matching_consultants, str) else assessment.matching_consultants
            except (json.JSONDecodeError, TypeError):
                matching_ids = []

        # Parse required skills
        required_skills = []
        if request.required_skills:
            try:
                required_skills = json.loads(request.required_skills) if isinstance(request.required_skills, str) else request.required_skills
            except (json.JSONDecodeError, TypeError):
                required_skills = []

        # If no explicit skills, use AI-extracted skills from analysis
        if not required_skills and request.ai_category:
            from backend.services.ai_engine import ai_engine
            ai_result = ai_engine.analyze_request(
                title=request.title,
                description=request.description,
                skills=[],
            )
            required_skills = ai_result.get("extracted_skills", [])

        required_lower = [s.lower() for s in required_skills]

        # Fetch and enrich each matching consultant
        for cid in matching_ids:
            consultant = db.query(Consultant).filter(Consultant.id == cid).first()
            if not consultant:
                continue

            c_skills = []
            if consultant.skills:
                try:
                    c_skills = json.loads(consultant.skills) if isinstance(consultant.skills, str) else consultant.skills
                except (json.JSONDecodeError, TypeError):
                    c_skills = []

            c_skills_lower = [s.lower() for s in c_skills]
            matching_skills = [s for s in required_skills if s.lower() in c_skills_lower]
            missing_skills = [s for s in required_skills if s.lower() not in c_skills_lower]
            match_score = (len(matching_skills) / max(len(required_skills), 1)) * 100

            matching_consultants_out.append(MatchingConsultantOut(
                id=consultant.id,
                name=consultant.name,
                title=consultant.title,
                skills=c_skills,
                hourly_rate=consultant.hourly_rate,
                status=consultant.status.value if hasattr(consultant.status, 'value') else str(consultant.status),
                match_score=round(match_score, 1),
                matching_skills=matching_skills,
                missing_skills=missing_skills,
            ))

        # Sort by match score descending
        matching_consultants_out.sort(key=lambda c: c.match_score, reverse=True)

    return RequestDetail(
        request=_serialize_request(request),
        customer=CustomerOut.model_validate(request.customer),
        assessment=_serialize_assessment(assessment) if assessment else None,
        matching_consultants=matching_consultants_out,
        actions=[CoordinationActionOut.model_validate(a) for a in sorted(request.actions, key=lambda x: x.order)],
        timeline=[TimelineEventOut.model_validate(e) for e in sorted(request.timeline_events, key=lambda x: x.created_at, reverse=True)],
        assignments=_enrich_assignments(db, request.assignments),
    )


@router.post("/{request_id}/assess")
def trigger_assessment(request_id: str, db: Session = Depends(get_db)):
    """Manually trigger a feasibility assessment."""
    try:
        assessment = feasibility_service.assess(db, request_id)
        return _serialize_assessment(assessment)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{request_id}/coordinate")
def trigger_coordination(request_id: str, plan_type: str = "standard_staffing", db: Session = Depends(get_db)):
    """Create and execute an action plan for the request."""
    try:
        actions = coordinator.create_action_plan(db, request_id, plan_type)
        executed = coordinator.execute_all_actions(db, request_id)
        return {
            "plan_created": len(actions),
            "actions_executed": len(executed),
            "actions": [CoordinationActionOut.model_validate(a) for a in executed],
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{request_id}/assign/{consultant_id}")
def assign_consultant(request_id: str, consultant_id: str, db: Session = Depends(get_db)):
    """Assign a consultant to a request. Sets status to 'sent' and notifies all parties."""
    try:
        # Guard against duplicate assignments
        existing = db.query(Assignment).filter(
            Assignment.request_id == request_id,
            Assignment.consultant_id == consultant_id,
            Assignment.status.notin_(["rejected", "ended"]),
        ).first()
        if existing:
            raise HTTPException(400, "Konsulten är redan tilldelad denna förfrågan")

        assignment = coordinator.assign_consultant(db, request_id, consultant_id)
        # Update assignment status to 'sent' (förfrågan skickad till konsult)
        assignment.status = "sent"
        db.commit()
        db.refresh(assignment)

        # Get context for notifications
        request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
        consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()

        # Notify handlers: förfrågan skickad till konsult
        notify_handlers(
            db,
            title=f"Förfrågan skickad till {consultant.name}",
            message=f"{consultant.name} ({consultant.title}) har fått förfrågan för '{request.title}'. Inväntar konsultens svar.",
            notification_type="info",
            link=request_id,
        )

        # Notify customer: konsult föreslagen
        if request:
            customer_users = db.query(User).filter(User.customer_id == request.customer_id).all()
            for cu in customer_users:
                notify_user(
                    db, cu.id,
                    title=f"Konsult föreslagen: {consultant.name}",
                    message=f"{consultant.name} ({consultant.title}) har mottagit förfrågan för '{request.title}'. Vi inväntar konsultens godkännande.",
                    notification_type="info",
                    link=request_id,
                )

        # Add timeline event
        event = TimelineEvent(
            request_id=request_id,
            event_type="assignment_sent",
            title=f"Förfrågan skickad till {consultant.name}",
            description=f"Inväntar godkännande från {consultant.name} ({consultant.title})",
            actor="Handler",
        )
        db.add(event)
        db.commit()

        return AssignmentOut.model_validate(assignment)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.patch("/{request_id}/assignments/{assignment_id}/approve")
def approve_assignment(request_id: str, assignment_id: str, db: Session = Depends(get_db)):
    """Consultant approves the assignment."""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id, Assignment.request_id == request_id
    ).first()
    if not assignment:
        raise HTTPException(404, "Assignment not found")

    assignment.status = "confirmed"
    consultant = db.query(Consultant).filter(Consultant.id == assignment.consultant_id).first()
    request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()

    # Timeline event
    event = TimelineEvent(
        request_id=request_id,
        event_type="assignment_confirmed",
        title=f"{consultant.name} har godkänt uppdraget",
        description=f"{consultant.name} ({consultant.title}) — {consultant.hourly_rate} SEK/h",
        actor=consultant.name,
    )
    db.add(event)

    # Notify handlers
    notify_handlers(
        db,
        title=f"{consultant.name} godkände uppdraget",
        message=f"{consultant.name} har accepterat uppdraget '{request.title}'. Tilldelningen är bekräftad.",
        notification_type="success",
        link=request_id,
    )

    # Notify customer
    if request:
        customer_users = db.query(User).filter(User.customer_id == request.customer_id).all()
        for cu in customer_users:
            notify_user(
                db, cu.id,
                title=f"Konsult bekräftad: {consultant.name}",
                message=f"{consultant.name} har accepterat uppdraget '{request.title}'. Tilldelningen är klar!",
                notification_type="success",
                link=request_id,
            )

    # Check if all needed consultants are confirmed
    confirmed_count = sum(1 for a in request.assignments if a.status == "confirmed")
    if confirmed_count >= request.number_of_consultants:
        request.status = RequestStatus.COMPLETED
        complete_event = TimelineEvent(
            request_id=request_id,
            event_type="request_completed",
            title="Alla konsulter bekräftade — uppdraget är klart",
            description=f"{confirmed_count} konsult(er) tilldelade och bekräftade",
            actor="System",
        )
        db.add(complete_event)

    db.commit()
    return {"ok": True, "status": assignment.status}


@router.patch("/{request_id}/assignments/{assignment_id}/reject")
def reject_assignment(request_id: str, assignment_id: str, db: Session = Depends(get_db)):
    """Consultant rejects the assignment."""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id, Assignment.request_id == request_id
    ).first()
    if not assignment:
        raise HTTPException(404, "Assignment not found")

    assignment.status = "rejected"
    consultant = db.query(Consultant).filter(Consultant.id == assignment.consultant_id).first()
    request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()

    # Restore consultant availability
    if consultant:
        consultant.status = ConsultantStatus.AVAILABLE
        consultant.current_customer_id = None

    # Timeline event
    event = TimelineEvent(
        request_id=request_id,
        event_type="assignment_rejected",
        title=f"{consultant.name} avböjde uppdraget",
        description=f"{consultant.name} har tackat nej. Ny matchning kan behövas.",
        actor=consultant.name,
    )
    db.add(event)

    # Notify handlers
    notify_handlers(
        db,
        title=f"{consultant.name} avböjde uppdraget",
        message=f"{consultant.name} har tackat nej till '{request.title}'. Välj en annan konsult.",
        notification_type="warning",
        link=request_id,
    )

    # Notify customer
    if request:
        customer_users = db.query(User).filter(User.customer_id == request.customer_id).all()
        for cu in customer_users:
            notify_user(
                db, cu.id,
                title="Konsult avböjde — ny matchning pågår",
                message=f"Den föreslagna konsulten för '{request.title}' avböjde. Vi söker en ny matchning.",
                notification_type="warning",
                link=request_id,
            )

    db.commit()
    return {"ok": True, "status": assignment.status}


@router.patch("/{request_id}/status")
def update_status(request_id: str, status: str, db: Session = Depends(get_db)):
    """Update request status."""
    request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
    if not request:
        raise HTTPException(404, "Request not found")

    request.status = status

    event = TimelineEvent(
        request_id=request_id,
        event_type="status_changed",
        title=f"Status changed to {status}",
        description=f"Request status updated to: {status}",
        actor="System",
    )
    db.add(event)
    db.commit()
    db.refresh(request)
    return _serialize_request(request)


def _enrich_assignments(db: Session, assignments) -> list[AssignmentDetailOut]:
    """Enrich assignments with consultant details."""
    result = []
    for a in assignments:
        consultant = db.query(Consultant).filter(Consultant.id == a.consultant_id).first()
        skills = []
        if consultant and consultant.skills:
            if isinstance(consultant.skills, str):
                try:
                    skills = json.loads(consultant.skills)
                except (json.JSONDecodeError, TypeError):
                    skills = [consultant.skills]
            elif isinstance(consultant.skills, list):
                skills = consultant.skills
        result.append(AssignmentDetailOut(
            id=a.id,
            request_id=a.request_id,
            consultant_id=a.consultant_id,
            consultant_name=consultant.name if consultant else "Unknown",
            consultant_title=consultant.title if consultant else None,
            consultant_skills=skills,
            start_date=a.start_date,
            end_date=a.end_date,
            hourly_rate=a.hourly_rate,
            status=a.status,
            created_at=a.created_at,
        ))
    return result


def _serialize_request(r: StaffingRequest) -> StaffingRequestOut:
    """Serialize a request with JSON fields parsed."""
    data = StaffingRequestOut.model_validate(r)
    if isinstance(r.required_skills, str):
        try:
            data.required_skills = json.loads(r.required_skills)
        except (json.JSONDecodeError, TypeError):
            data.required_skills = [r.required_skills]
    return data


def _serialize_assessment(a) -> FeasibilityAssessmentOut:
    """Serialize assessment with JSON fields parsed."""
    data = FeasibilityAssessmentOut.model_validate(a)
    for field in ["matching_consultants", "risks", "recommendations", "alternatives"]:
        val = getattr(a, field)
        if isinstance(val, str):
            try:
                setattr(data, field, json.loads(val))
            except (json.JSONDecodeError, TypeError):
                pass
    return data
