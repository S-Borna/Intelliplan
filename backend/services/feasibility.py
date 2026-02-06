"""
Feasibility Assessment Service.

Evaluates whether a staffing request can be fulfilled based on
availability, skills, budget, timeline, and compliance.
"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import (
    Consultant,
    ConsultantStatus,
    FeasibilityAssessment,
    FeasibilityRating,
    StaffingRequest,
    RequestStatus,
    TimelineEvent,
)
from backend.services.ai_engine import ai_engine
from backend.services.compliance import compliance_engine


class FeasibilityService:
    """Assess the feasibility of fulfilling a staffing request."""

    def assess(self, db: Session, request_id: str) -> FeasibilityAssessment:
        """Run a full feasibility assessment on a staffing request."""
        request = db.query(StaffingRequest).filter(StaffingRequest.id == request_id).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")

        # Update status
        request.status = RequestStatus.ANALYZING

        # Parse required skills
        required_skills = []
        if request.required_skills:
            try:
                required_skills = json.loads(request.required_skills)
            except (json.JSONDecodeError, TypeError):
                required_skills = [s.strip() for s in str(request.required_skills).split(",")]

        # If no explicit skills, extract from description using AI
        if not required_skills:
            from backend.services.ai_engine import ai_engine as _ai
            ai_result = _ai.analyze_request(
                title=request.title,
                description=request.description,
                skills=[],
            )
            required_skills = [s for s in ai_result.get("extracted_skills", []) if "experience" not in s.lower()]

        # Get all consultants
        all_consultants = db.query(Consultant).all()

        # Run sub-assessments
        availability_result = self._assess_availability(all_consultants, request)
        skills_result = self._assess_skills_match(all_consultants, required_skills)
        budget_result = self._assess_budget(all_consultants, request.budget_max_hourly)
        timeline_result = self._assess_timeline(request)
        compliance_result = compliance_engine.check_request(request, all_consultants)

        # Find matching consultants (intersection of good matches)
        matching_ids = self._find_matching_consultants(
            all_consultants, required_skills, request
        )

        # Calculate overall rating
        scores = {
            "availability_score": availability_result["score"],
            "skills_match_score": skills_result["score"],
            "budget_fit_score": budget_result["score"],
            "timeline_score": timeline_result["score"],
            "compliance_score": compliance_result["score"],
        }
        overall_rating, confidence = self._calculate_overall(scores, len(matching_ids), request.number_of_consultants)

        # Collect risks
        risks = (
            availability_result.get("risks", [])
            + skills_result.get("risks", [])
            + budget_result.get("risks", [])
            + compliance_result.get("risks", [])
        )

        # Generate AI recommendations
        recommendations = ai_engine.generate_recommendations({
            "overall_rating": overall_rating,
            **scores,
        })

        # Generate alternatives if not fully feasible
        alternatives = self._suggest_alternatives(scores, required_skills, request)

        # Create assessment
        assessment = FeasibilityAssessment(
            request_id=request_id,
            overall_rating=overall_rating,
            confidence_score=confidence,
            availability_score=scores["availability_score"],
            skills_match_score=scores["skills_match_score"],
            budget_fit_score=scores["budget_fit_score"],
            timeline_score=scores["timeline_score"],
            compliance_score=scores["compliance_score"],
            matching_consultants=json.dumps(matching_ids),
            risks=json.dumps(risks),
            recommendations=json.dumps(recommendations),
            alternatives=json.dumps(alternatives),
        )

        # Delete old assessment if exists
        old = db.query(FeasibilityAssessment).filter(
            FeasibilityAssessment.request_id == request_id
        ).first()
        if old:
            db.delete(old)

        db.add(assessment)

        # Update request status
        request.status = RequestStatus.ASSESSED

        # Add timeline event
        event = TimelineEvent(
            request_id=request_id,
            event_type="assessment_completed",
            title="Feasibility assessment completed",
            description=f"Overall rating: {overall_rating} (confidence: {confidence:.0%})",
            actor="AI Engine",
        )
        db.add(event)
        db.commit()
        db.refresh(assessment)

        return assessment

    def _assess_availability(self, consultants: list[Consultant], request: StaffingRequest) -> dict:
        """Check how many consultants are available."""
        available = [c for c in consultants if c.status == ConsultantStatus.AVAILABLE]
        ending_soon = [c for c in consultants if c.status == ConsultantStatus.ENDING_SOON]

        total_available = len(available) + len(ending_soon)
        needed = request.number_of_consultants or 1
        ratio = min(total_available / max(needed, 1), 1.0)
        score = ratio * 100

        risks = []
        if total_available < needed:
            risks.append(f"Only {total_available} consultants available, {needed} needed")
        if total_available == 0:
            risks.append("No consultants currently available")

        return {"score": round(score), "risks": risks}

    def _assess_skills_match(self, consultants: list[Consultant], required_skills: list[str]) -> dict:
        """Evaluate skills match across available consultants."""
        if not required_skills:
            return {"score": 80, "risks": ["No specific skills requested — broad matching"]}

        best_match = 0
        for consultant in consultants:
            c_skills = []
            if consultant.skills:
                try:
                    c_skills = json.loads(consultant.skills)
                except (json.JSONDecodeError, TypeError):
                    c_skills = [s.strip().lower() for s in str(consultant.skills).split(",")]

            c_skills_lower = [s.lower() for s in c_skills]
            match = sum(1 for s in required_skills if s.lower() in c_skills_lower)
            match_ratio = match / len(required_skills)
            best_match = max(best_match, match_ratio)

        score = best_match * 100
        risks = []
        if score < 50:
            risks.append(f"Best skills match is only {score:.0f}% — may need external recruitment")

        return {"score": round(score), "risks": risks}

    def _assess_budget(self, consultants: list[Consultant], max_hourly: float | None) -> dict:
        """Evaluate budget fit."""
        if not max_hourly:
            return {"score": 70, "risks": ["No budget specified — assuming flexible"]}

        affordable = [c for c in consultants if c.hourly_rate <= max_hourly]
        ratio = len(affordable) / max(len(consultants), 1)
        score = ratio * 100

        risks = []
        if ratio < 0.3:
            avg_rate = sum(c.hourly_rate for c in consultants) / max(len(consultants), 1)
            risks.append(f"Budget ({max_hourly}/h) below average rate ({avg_rate:.0f}/h)")

        return {"score": round(score), "risks": risks}

    def _assess_timeline(self, request: StaffingRequest) -> dict:
        """Evaluate timeline feasibility."""
        if not request.start_date:
            return {"score": 70, "risks": ["No start date specified"]}

        now = datetime.now(timezone.utc)
        start = request.start_date if request.start_date.tzinfo else request.start_date.replace(tzinfo=timezone.utc)
        days_until_start = (start - now).days

        risks = []
        if days_until_start < 0:
            score = 20
            risks.append("Start date is in the past")
        elif days_until_start < 7:
            score = 40
            risks.append("Very tight timeline — less than 1 week")
        elif days_until_start < 14:
            score = 60
            risks.append("Tight timeline — less than 2 weeks")
        elif days_until_start < 30:
            score = 80
        else:
            score = 95

        return {"score": score, "risks": risks}

    def _find_matching_consultants(
        self, consultants: list[Consultant], required_skills: list[str], request: StaffingRequest
    ) -> list[str]:
        """Find consultant IDs that match the request."""
        matches = []

        for c in consultants:
            if c.status not in (ConsultantStatus.AVAILABLE, ConsultantStatus.ENDING_SOON):
                continue

            # Skills check
            c_skills = []
            if c.skills:
                try:
                    c_skills = [s.lower() for s in json.loads(c.skills)]
                except (json.JSONDecodeError, TypeError):
                    c_skills = [s.strip().lower() for s in str(c.skills).split(",")]

            if required_skills:
                match_ratio = sum(1 for s in required_skills if s.lower() in c_skills) / len(required_skills)
                if match_ratio < 0.3:
                    continue

            # Budget check
            if request.budget_max_hourly and c.hourly_rate > request.budget_max_hourly:
                continue

            matches.append(c.id)

        return matches

    def _calculate_overall(self, scores: dict, matching_count: int, needed: int) -> tuple[str, float]:
        """Calculate overall feasibility rating and confidence."""
        avg = sum(scores.values()) / len(scores)

        # Confidence based on data quality
        confidence = min(0.5 + (matching_count / max(needed, 1)) * 0.3 + 0.2, 1.0)

        if avg >= 75 and matching_count >= needed:
            rating = FeasibilityRating.HIGH
        elif avg >= 50:
            rating = FeasibilityRating.MEDIUM
        elif avg >= 30:
            rating = FeasibilityRating.LOW
        else:
            rating = FeasibilityRating.NOT_FEASIBLE

        return rating.value, round(confidence, 2)

    def _suggest_alternatives(self, scores: dict, skills: list[str], request: StaffingRequest) -> list[str]:
        """Suggest alternatives when feasibility is limited."""
        alternatives = []

        if scores["availability_score"] < 50:
            alternatives.append("Consider a later start date to access more consultants")
            alternatives.append("Split the request into phases with staggered starts")

        if scores["skills_match_score"] < 50:
            alternatives.append("Broaden skill requirements to include adjacent technologies")
            alternatives.append("Consider a mix of senior and junior consultants with mentoring")

        if scores["budget_fit_score"] < 50:
            alternatives.append("Negotiate a blended rate with mixed seniority levels")
            alternatives.append("Consider remote consultants for lower rates")

        if scores["timeline_score"] < 50:
            alternatives.append("Start with partial team and scale up")

        return alternatives


# Singleton
feasibility_service = FeasibilityService()
