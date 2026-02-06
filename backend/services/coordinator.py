"""
Action Coordinator.

Orchestrates workflows: creates action plans, executes steps,
and manages the lifecycle of coordinated actions.
"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import (
    ActionStatus,
    CoordinationAction,
    RequestStatus,
    StaffingRequest,
    TimelineEvent,
    Assignment,
    Consultant,
    ConsultantStatus,
)


# Action templates for different scenarios
ACTION_TEMPLATES = {
    "standard_staffing": [
        {
            "action_type": "verify_requirements",
            "description": "Verify and confirm customer requirements with AI analysis",
        },
        {
            "action_type": "run_feasibility",
            "description": "Run automated feasibility assessment",
        },
        {
            "action_type": "match_consultants",
            "description": "Match and rank available consultants",
        },
        {
            "action_type": "compliance_check",
            "description": "Run compliance checks on proposed matches",
        },
        {
            "action_type": "prepare_proposal",
            "description": "Prepare staffing proposal for customer review",
        },
        {
            "action_type": "notify_customer",
            "description": "Send proposal and status update to customer",
        },
    ],
    "urgent_staffing": [
        {
            "action_type": "immediate_match",
            "description": "🚨 Immediate consultant matching — urgent request",
        },
        {
            "action_type": "fast_compliance",
            "description": "Fast-track compliance verification",
        },
        {
            "action_type": "notify_consultants",
            "description": "Notify matched consultants immediately",
        },
        {
            "action_type": "notify_customer",
            "description": "Send immediate status update to customer",
        },
    ],
    "extension": [
        {
            "action_type": "verify_current_assignment",
            "description": "Verify current assignment status and terms",
        },
        {
            "action_type": "consultant_availability",
            "description": "Confirm consultant availability for extension",
        },
        {
            "action_type": "update_contract",
            "description": "Prepare contract amendment for extension",
        },
        {
            "action_type": "notify_all_parties",
            "description": "Notify customer and consultant of extension",
        },
    ],
}


class Coordinator:
    """Coordinates actions and workflows for staffing requests."""

    def create_action_plan(self, db: Session, request_id: str, plan_type: str = "standard_staffing") -> list[CoordinationAction]:
        """
        Create an action plan for a request based on its type.

        Args:
            db: Database session
            request_id: The staffing request ID
            plan_type: Type of action plan (standard_staffing, urgent_staffing, extension)

        Returns:
            List of created CoordinationAction objects
        """
        request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")

        # Auto-detect plan type based on priority
        if request.priority and request.priority.value == "urgent":
            plan_type = "urgent_staffing"

        template = ACTION_TEMPLATES.get(plan_type, ACTION_TEMPLATES["standard_staffing"])
        actions = []

        for i, action_def in enumerate(template):
            action = CoordinationAction(
                request_id=request_id,
                action_type=action_def["action_type"],
                description=action_def["description"],
                status=ActionStatus.PENDING,
                order=i,
            )
            db.add(action)
            actions.append(action)

        # Timeline event
        event = TimelineEvent(
            request_id=request_id,
            event_type="action_plan_created",
            title=f"Action plan created ({plan_type})",
            description=f"{len(actions)} actions planned for execution",
            actor="Coordinator",
        )
        db.add(event)
        db.commit()

        for a in actions:
            db.refresh(a)

        return actions

    def execute_next_action(self, db: Session, request_id: str) -> CoordinationAction | None:
        """Execute the next pending action in the plan."""
        action = (
            db.query(CoordinationAction)
            .filter(
                CoordinationAction.request_id == request_id,
                CoordinationAction.status == ActionStatus.PENDING,
            )
            .order_by(CoordinationAction.order)
            .first()
        )

        if not action:
            return None

        action.status = ActionStatus.IN_PROGRESS

        # Simulate execution based on action type
        result = self._execute_action(db, action)
        action.result = result
        action.status = ActionStatus.COMPLETED
        action.completed_at = datetime.now(timezone.utc)

        # Timeline event
        event = TimelineEvent(
            request_id=request_id,
            event_type="action_completed",
            title=f"Action completed: {action.action_type}",
            description=result,
            actor="Coordinator",
        )
        db.add(event)

        # Check if all actions are done
        remaining = (
            db.query(CoordinationAction)
            .filter(
                CoordinationAction.request_id == request_id,
                CoordinationAction.status == ActionStatus.PENDING,
            )
            .count()
        )

        if remaining == 0:
            request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
            if request:
                request.status = RequestStatus.IN_PROGRESS
                complete_event = TimelineEvent(
                    request_id=request_id,
                    event_type="all_actions_completed",
                    title="All coordination actions completed",
                    description="Request is ready for final review and customer communication",
                    actor="Coordinator",
                )
                db.add(complete_event)

        db.commit()
        db.refresh(action)
        return action

    def execute_all_actions(self, db: Session, request_id: str) -> list[CoordinationAction]:
        """Execute all pending actions sequentially."""
        executed = []
        while True:
            action = self.execute_next_action(db, request_id)
            if not action:
                break
            executed.append(action)
        return executed

    def assign_consultant(
        self, db: Session, request_id: str, consultant_id: str
    ) -> Assignment:
        """Create an assignment for a consultant to a request."""
        request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
        consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()

        if not request or not consultant:
            raise ValueError("Request or consultant not found")

        assignment = Assignment(
            request_id=request_id,
            consultant_id=consultant_id,
            start_date=request.start_date or datetime.now(timezone.utc),
            end_date=request.end_date,
            hourly_rate=consultant.hourly_rate,
            status="proposed",
        )
        db.add(assignment)

        # Update consultant status
        consultant.status = ConsultantStatus.ASSIGNED
        consultant.current_customer_id = request.customer_id

        # Timeline event
        event = TimelineEvent(
            request_id=request_id,
            event_type="consultant_assigned",
            title=f"Consultant proposed: {consultant.name}",
            description=f"{consultant.title} — Rate: {consultant.hourly_rate}/h",
            actor="Coordinator",
        )
        db.add(event)

        db.commit()
        db.refresh(assignment)
        return assignment

    def _execute_action(self, db: Session, action: CoordinationAction) -> str:
        """Simulate action execution — returns result description."""
        action_results = {
            "verify_requirements": "Requirements verified — AI analysis confirms clarity and completeness",
            "run_feasibility": "Feasibility assessment triggered — results available in assessment panel",
            "match_consultants": "Consultant matching completed — candidates ranked by fit score",
            "compliance_check": "Compliance checks passed — no blocking issues found",
            "prepare_proposal": "Staffing proposal prepared with top 3 candidate profiles",
            "notify_customer": "Customer notification sent with current status and next steps",
            "notify_consultants": "Matched consultants notified of opportunity",
            "immediate_match": "Urgent matching completed — top available consultants identified",
            "fast_compliance": "Fast-track compliance check completed",
            "verify_current_assignment": "Current assignment verified — eligible for extension",
            "consultant_availability": "Consultant confirmed available for extended period",
            "update_contract": "Contract amendment prepared for review",
            "notify_all_parties": "All parties notified of changes",
        }
        return action_results.get(action.action_type, f"Action '{action.action_type}' completed successfully")


# Singleton
coordinator = Coordinator()
