"""Seed database with realistic sample data."""

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.models import (
    ComplianceRule,
    Consultant,
    ConsultantStatus,
    Customer,
    User,
    UserRole,
    hash_password,
)


def seed_database(db: Session):
    """Populate the database with sample data for demonstration."""

    # Check if already seeded
    if db.query(Customer).count() > 0:
        return

    # ── Customers ──────────────────────────────────────

    customers = [
        Customer(
            id="cust-001",
            name="Anna Lindström",
            company="Volvo Group",
            email="anna.lindstrom@volvo.com",
            phone="+46 70 123 4567",
            industry="Automotive",
            contract_type="premium",
        ),
        Customer(
            id="cust-002",
            name="Erik Johansson",
            company="Spotify",
            email="erik.j@spotify.com",
            phone="+46 70 234 5678",
            industry="Tech / Media",
            contract_type="standard",
        ),
        Customer(
            id="cust-003",
            name="Maria Karlsson",
            company="SEB",
            email="maria.karlsson@seb.se",
            phone="+46 70 345 6789",
            industry="Finance",
            contract_type="premium",
        ),
        Customer(
            id="cust-004",
            name="Lars Svensson",
            company="Ericsson",
            email="lars.svensson@ericsson.com",
            phone="+46 70 456 7890",
            industry="Telecom",
            contract_type="standard",
        ),
        Customer(
            id="cust-005",
            name="Sofia Bergman",
            company="H&M",
            email="sofia.bergman@hm.com",
            phone="+46 70 567 8901",
            industry="Retail",
            contract_type="standard",
        ),
    ]

    # ── Consultants ────────────────────────────────────

    consultants = [
        Consultant(
            id="cons-001",
            name="Johan Nilsson",
            email="johan.n@consultant.se",
            title="Senior Backend Developer",
            skills=json.dumps(["python", "java", "docker", "kubernetes", "aws", "sql"]),
            hourly_rate=950,
            status=ConsultantStatus.AVAILABLE,
        ),
        Consultant(
            id="cons-002",
            name="Emma Andersson",
            email="emma.a@consultant.se",
            title="Full Stack Developer",
            skills=json.dumps(["react", "typescript", "node.js", "python", "aws", "sql"]),
            hourly_rate=900,
            status=ConsultantStatus.AVAILABLE,
        ),
        Consultant(
            id="cons-003",
            name="Oscar Pettersson",
            email="oscar.p@consultant.se",
            title="DevOps Engineer",
            skills=json.dumps(["docker", "kubernetes", "terraform", "aws", "azure", "ci/cd", "python"]),
            hourly_rate=1000,
            status=ConsultantStatus.AVAILABLE,
        ),
        Consultant(
            id="cons-004",
            name="Linnea Eriksson",
            email="linnea.e@consultant.se",
            title="Data Engineer",
            skills=json.dumps(["python", "spark", "sql", "etl", "aws", "pandas", "power bi"]),
            hourly_rate=950,
            status=ConsultantStatus.ASSIGNED,
            current_customer_id="cust-002",
        ),
        Consultant(
            id="cons-005",
            name="Alexander Berg",
            email="alexander.b@consultant.se",
            title="Senior Frontend Developer",
            skills=json.dumps(["react", "typescript", "next.js", "vue", "css", "figma"]),
            hourly_rate=900,
            status=ConsultantStatus.AVAILABLE,
        ),
        Consultant(
            id="cons-006",
            name="Hanna Ström",
            email="hanna.s@consultant.se",
            title="ML Engineer",
            skills=json.dumps(["python", "machine learning", "pytorch", "tensorflow", "nlp", "docker"]),
            hourly_rate=1100,
            status=ConsultantStatus.AVAILABLE,
        ),
        Consultant(
            id="cons-007",
            name="Viktor Lund",
            email="viktor.l@consultant.se",
            title="Scrum Master / Agile Coach",
            skills=json.dumps(["scrum", "agile", "projektledning", "jira", "product owner"]),
            hourly_rate=850,
            status=ConsultantStatus.ENDING_SOON,
            availability_date=datetime.now(timezone.utc) + timedelta(days=14),
        ),
        Consultant(
            id="cons-008",
            name="Frida Sandberg",
            email="frida.s@consultant.se",
            title="iOS / Mobile Developer",
            skills=json.dumps(["swift", "ios", "react native", "kotlin", "android"]),
            hourly_rate=950,
            status=ConsultantStatus.AVAILABLE,
        ),
        Consultant(
            id="cons-009",
            name="Daniel Öberg",
            email="daniel.o@consultant.se",
            title="Cloud Architect",
            skills=json.dumps(["aws", "azure", "gcp", "terraform", "kubernetes", "docker"]),
            hourly_rate=1200,
            status=ConsultantStatus.ON_LEAVE,
            availability_date=datetime.now(timezone.utc) + timedelta(days=30),
        ),
        Consultant(
            id="cons-010",
            name="Maja Holmgren",
            email="maja.h@consultant.se",
            title="UX Designer",
            skills=json.dumps(["ux", "ui", "figma", "user research", "design system"]),
            hourly_rate=850,
            status=ConsultantStatus.AVAILABLE,
        ),
    ]

    # ── Compliance Rules ───────────────────────────────

    rules = [
        ComplianceRule(
            name="EU Working Time Directive",
            description="Maximum 48 working hours per week including overtime",
            rule_type="regulation",
            severity="blocking",
            condition=json.dumps({"max_weekly_hours": 48}),
        ),
        ComplianceRule(
            name="Minimum Notice Period",
            description="5 business days notice required for new assignments",
            rule_type="policy",
            severity="warning",
            condition=json.dumps({"min_notice_days": 5}),
        ),
        ComplianceRule(
            name="Rate Transparency",
            description="Customer must be informed of applicable rates before assignment starts",
            rule_type="contract",
            severity="blocking",
            condition=json.dumps({"require_rate_approval": True}),
        ),
        ComplianceRule(
            name="Non-Compete Check",
            description="Verify consultant has no conflicting non-compete clauses",
            rule_type="contract",
            severity="blocking",
            condition=json.dumps({"check_non_compete": True}),
        ),
    ]

    # ── Insert all ─────────────────────────────────────

    db.add_all(customers)
    db.add_all(consultants)
    db.add_all(rules)
    db.flush()

    # ── Users (demo accounts) ──────────────────────────

    users = [
        # Handlers / Admin
        User(
            id="user-admin",
            email="admin@intelliplan.se",
            password_hash=hash_password("admin123"),
            full_name="Admin Intelliplan",
            role=UserRole.ADMIN,
        ),
        User(
            id="user-handler-1",
            email="handler@intelliplan.se",
            password_hash=hash_password("handler123"),
            full_name="Sara Lindqvist",
            role=UserRole.HANDLER,
        ),
        User(
            id="user-handler-2",
            email="marcus@intelliplan.se",
            password_hash=hash_password("handler123"),
            full_name="Marcus Ek",
            role=UserRole.HANDLER,
        ),
        # Customer users
        User(
            id="user-cust-001",
            email="anna.lindstrom@volvo.com",
            password_hash=hash_password("kund123"),
            full_name="Anna Lindström",
            role=UserRole.CUSTOMER,
            customer_id="cust-001",
        ),
        User(
            id="user-cust-002",
            email="erik.j@spotify.com",
            password_hash=hash_password("kund123"),
            full_name="Erik Johansson",
            role=UserRole.CUSTOMER,
            customer_id="cust-002",
        ),
        User(
            id="user-cust-003",
            email="maria.karlsson@seb.se",
            password_hash=hash_password("kund123"),
            full_name="Maria Karlsson",
            role=UserRole.CUSTOMER,
            customer_id="cust-003",
        ),
    ]

    db.add_all(users)
    db.commit()

    print(f"✅ Seeded: {len(customers)} customers, {len(consultants)} consultants, {len(rules)} compliance rules")
