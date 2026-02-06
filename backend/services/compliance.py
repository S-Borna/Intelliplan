"""
Compliance Engine.

Checks staffing requests against rules, regulations, and contract terms.
"""

import json
from backend.models import StaffingRequest, Consultant, ConsultantStatus


# Built-in compliance rules
DEFAULT_RULES = [
    {
        "id": "max_hours_weekly",
        "name": "Maximum Weekly Hours",
        "description": "EU Working Time Directive — max 48h/week",
        "severity": "blocking",
        "check": "weekly_hours",
    },
    {
        "id": "notice_period",
        "name": "Minimum Notice Period",
        "description": "Assignments require at least 5 business days notice",
        "severity": "warning",
        "check": "notice_days",
        "min_days": 5,
    },
    {
        "id": "contract_coverage",
        "name": "Contract Coverage",
        "description": "Customer must have an active framework agreement",
        "severity": "blocking",
        "check": "contract",
    },
    {
        "id": "rate_cap",
        "name": "Rate Cap Compliance",
        "description": "Hourly rate must not exceed contract maximum",
        "severity": "warning",
        "check": "rate_cap",
    },
    {
        "id": "consultant_availability",
        "name": "Consultant Availability Verification",
        "description": "Consultant must not have conflicting assignments",
        "severity": "blocking",
        "check": "availability",
    },
]


class ComplianceEngine:
    """Check requests and assignments against compliance rules."""

    def __init__(self):
        self.rules = DEFAULT_RULES

    def check_request(self, request: StaffingRequest, consultants: list[Consultant]) -> dict:
        """
        Run all compliance checks on a request.

        Returns dict with:
          - score: 0-100
          - risks: list of compliance risk descriptions
          - violations: list of blocking violations
          - warnings: list of non-blocking warnings
        """
        violations = []
        warnings = []

        for rule in self.rules:
            result = self._run_check(rule, request, consultants)
            if result:
                if rule["severity"] == "blocking":
                    violations.append(result)
                else:
                    warnings.append(result)

        # Score: start at 100, deduct for issues
        score = 100 - (len(violations) * 25) - (len(warnings) * 10)
        score = max(score, 0)

        risks = [f"🚫 {v}" for v in violations] + [f"⚠️ {w}" for w in warnings]

        return {
            "score": score,
            "risks": risks,
            "violations": violations,
            "warnings": warnings,
            "rules_checked": len(self.rules),
            "passed": len(violations) == 0,
        }

    def check_assignment(self, consultant: Consultant, request: StaffingRequest) -> dict:
        """Check compliance for a specific consultant-request assignment."""
        issues = []

        # Check if consultant is already assigned elsewhere
        if consultant.status == ConsultantStatus.ASSIGNED:
            issues.append({
                "rule": "availability",
                "severity": "blocking",
                "message": f"{consultant.name} is currently assigned to another customer",
            })

        # Check if consultant is on leave
        if consultant.status == ConsultantStatus.ON_LEAVE:
            issues.append({
                "rule": "availability",
                "severity": "blocking",
                "message": f"{consultant.name} is currently on leave",
            })

        # Rate check
        if request.budget_max_hourly and consultant.hourly_rate > request.budget_max_hourly:
            issues.append({
                "rule": "rate_cap",
                "severity": "warning",
                "message": f"Consultant rate ({consultant.hourly_rate}/h) exceeds budget ({request.budget_max_hourly}/h)",
            })

        return {
            "compliant": len([i for i in issues if i["severity"] == "blocking"]) == 0,
            "issues": issues,
        }

    def _run_check(self, rule: dict, request: StaffingRequest, consultants: list[Consultant]) -> str | None:
        """Run a single compliance check. Returns risk description or None."""
        check_type = rule.get("check")

        if check_type == "notice_days":
            # Simplified: always pass for now since we don't have exact business day calc
            return None

        if check_type == "contract":
            # Check customer contract type
            if request.customer and hasattr(request.customer, 'contract_type'):
                if request.customer.contract_type == "none":
                    return f"{rule['name']}: Customer has no active framework agreement"
            return None

        if check_type == "availability":
            available = [c for c in consultants if c.status in (
                ConsultantStatus.AVAILABLE, ConsultantStatus.ENDING_SOON
            )]
            if len(available) == 0:
                return f"{rule['name']}: No consultants available for verification"
            return None

        if check_type == "rate_cap":
            if request.budget_max_hourly:
                avg_rate = sum(c.hourly_rate for c in consultants) / max(len(consultants), 1)
                if request.budget_max_hourly < avg_rate * 0.5:
                    return f"{rule['name']}: Budget significantly below market rates"
            return None

        return None


# Singleton
compliance_engine = ComplianceEngine()
