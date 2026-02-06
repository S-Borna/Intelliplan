"""Seed database with realistic sample data for demo/review."""

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.models import (
    Assignment,
    ComplianceRule,
    Consultant,
    ConsultantStatus,
    CoordinationAction,
    ActionStatus,
    Customer,
    FeasibilityAssessment,
    FeasibilityRating,
    Notification,
    RequestStatus,
    RequestPriority,
    StaffingRequest,
    TimelineEvent,
    User,
    UserRole,
    hash_password,
)

now = datetime.now(timezone.utc)


def _ago(**kw):
    return now - timedelta(**kw)


def seed_database(db: Session):
    """Populate the database with comprehensive demo data."""

    if db.query(Customer).count() > 0:
        return

    # ═══════════════════════════════════════════════════
    # CUSTOMERS
    # ═══════════════════════════════════════════════════
    customers = [
        Customer(id="cust-001", name="Anna Lindström", company="Volvo Group", email="anna.lindstrom@volvo.com", phone="+46 70 123 4567", industry="Automotive & Manufacturing", contract_type="premium"),
        Customer(id="cust-002", name="Erik Johansson", company="Spotify", email="erik.j@spotify.com", phone="+46 70 234 5678", industry="Tech / Streaming", contract_type="standard"),
        Customer(id="cust-003", name="Maria Karlsson", company="SEB", email="maria.karlsson@seb.se", phone="+46 70 345 6789", industry="Finance & Banking", contract_type="premium"),
        Customer(id="cust-004", name="Lars Svensson", company="Ericsson", email="lars.svensson@ericsson.com", phone="+46 70 456 7890", industry="Telecom & 5G", contract_type="premium"),
        Customer(id="cust-005", name="Sofia Bergman", company="H&M Group", email="sofia.bergman@hm.com", phone="+46 70 567 8901", industry="Retail & E-commerce", contract_type="standard"),
    ]
    db.add_all(customers)
    db.flush()

    # ═══════════════════════════════════════════════════
    # CONSULTANTS
    # ═══════════════════════════════════════════════════
    consultants = [
        Consultant(id="cons-001", name="Johan Nilsson", email="johan.n@consultant.se", title="Senior Backend Developer", skills=json.dumps(["python", "java", "docker", "kubernetes", "aws", "sql", "fastapi", "microservices"]), hourly_rate=950, status=ConsultantStatus.ASSIGNED, current_customer_id="cust-001"),
        Consultant(id="cons-002", name="Emma Andersson", email="emma.a@consultant.se", title="Full Stack Developer", skills=json.dumps(["react", "typescript", "node.js", "python", "aws", "postgresql", "graphql"]), hourly_rate=900, status=ConsultantStatus.AVAILABLE),
        Consultant(id="cons-003", name="Oscar Pettersson", email="oscar.p@consultant.se", title="DevOps / Platform Engineer", skills=json.dumps(["docker", "kubernetes", "terraform", "aws", "azure", "ci/cd", "python", "gitops"]), hourly_rate=1000, status=ConsultantStatus.ASSIGNED, current_customer_id="cust-004"),
        Consultant(id="cons-004", name="Linnea Eriksson", email="linnea.e@consultant.se", title="Data Engineer / Analyst", skills=json.dumps(["python", "spark", "sql", "etl", "aws", "pandas", "power bi", "airflow"]), hourly_rate=950, status=ConsultantStatus.ASSIGNED, current_customer_id="cust-002"),
        Consultant(id="cons-005", name="Alexander Berg", email="alexander.b@consultant.se", title="Senior Frontend Developer", skills=json.dumps(["react", "typescript", "next.js", "vue", "css", "figma", "storybook"]), hourly_rate=900, status=ConsultantStatus.AVAILABLE),
        Consultant(id="cons-006", name="Hanna Ström", email="hanna.s@consultant.se", title="ML / AI Engineer", skills=json.dumps(["python", "machine learning", "pytorch", "tensorflow", "nlp", "docker", "mlops"]), hourly_rate=1100, status=ConsultantStatus.AVAILABLE),
        Consultant(id="cons-007", name="Viktor Lund", email="viktor.l@consultant.se", title="Scrum Master / Agile Coach", skills=json.dumps(["scrum", "agile", "projektledning", "jira", "kanban", "SAFe"]), hourly_rate=850, status=ConsultantStatus.ASSIGNED, current_customer_id="cust-003"),
        Consultant(id="cons-008", name="Frida Sandberg", email="frida.s@consultant.se", title="iOS / Mobile Developer", skills=json.dumps(["swift", "ios", "react native", "kotlin", "android", "firebase"]), hourly_rate=950, status=ConsultantStatus.AVAILABLE),
        Consultant(id="cons-009", name="Daniel Öberg", email="daniel.o@consultant.se", title="Cloud Solutions Architect", skills=json.dumps(["aws", "azure", "gcp", "terraform", "kubernetes", "docker", "networking"]), hourly_rate=1200, status=ConsultantStatus.ON_LEAVE, availability_date=now + timedelta(days=30)),
        Consultant(id="cons-010", name="Maja Holmgren", email="maja.h@consultant.se", title="UX/UI Designer", skills=json.dumps(["ux", "ui", "figma", "user research", "design system", "prototyping"]), hourly_rate=850, status=ConsultantStatus.AVAILABLE),
    ]
    db.add_all(consultants)
    db.flush()

    # ═══════════════════════════════════════════════════
    # COMPLIANCE RULES
    # ═══════════════════════════════════════════════════
    rules = [
        ComplianceRule(name="EU Working Time Directive", description="Maximum 48 working hours per week including overtime", rule_type="regulation", severity="blocking", condition=json.dumps({"max_weekly_hours": 48})),
        ComplianceRule(name="Minimum Notice Period", description="5 business days notice required for new assignments", rule_type="policy", severity="warning", condition=json.dumps({"min_notice_days": 5})),
        ComplianceRule(name="Rate Transparency", description="Customer must be informed of applicable rates before assignment starts", rule_type="contract", severity="blocking", condition=json.dumps({"require_rate_approval": True})),
        ComplianceRule(name="Non-Compete Check", description="Verify consultant has no conflicting non-compete clauses", rule_type="contract", severity="blocking", condition=json.dumps({"check_non_compete": True})),
        ComplianceRule(name="GDPR Data Processing", description="Ensure DPA is signed before consultant handles personal data", rule_type="regulation", severity="blocking", condition=json.dumps({"require_dpa": True})),
    ]
    db.add_all(rules)
    db.flush()

    # ═══════════════════════════════════════════════════
    # USERS
    # ═══════════════════════════════════════════════════
    users = [
        User(id="user-admin", email="admin@intelliplan.se", password_hash=hash_password("admin123"), full_name="Admin Intelliplan", role=UserRole.ADMIN),
        User(id="user-handler-1", email="handler@intelliplan.se", password_hash=hash_password("handler123"), full_name="Sara Lindqvist", role=UserRole.HANDLER),
        User(id="user-handler-2", email="marcus@intelliplan.se", password_hash=hash_password("handler123"), full_name="Marcus Ek", role=UserRole.HANDLER),
        User(id="user-cust-001", email="anna.lindstrom@volvo.com", password_hash=hash_password("kund123"), full_name="Anna Lindström", role=UserRole.CUSTOMER, customer_id="cust-001"),
        User(id="user-cust-002", email="erik.j@spotify.com", password_hash=hash_password("kund123"), full_name="Erik Johansson", role=UserRole.CUSTOMER, customer_id="cust-002"),
        User(id="user-cust-003", email="maria.karlsson@seb.se", password_hash=hash_password("kund123"), full_name="Maria Karlsson", role=UserRole.CUSTOMER, customer_id="cust-003"),
    ]
    db.add_all(users)
    db.flush()

    # ═══════════════════════════════════════════════════
    # STAFFING REQUESTS — 12 realistic scenarios
    # ═══════════════════════════════════════════════════
    requests_data = [
        # REQ-001: Volvo — COMPLETED (full lifecycle)
        dict(id="req-001", customer_id="cust-001",
             title="Senior Python-utvecklare — Autonomous Driving",
             description="Vi söker en erfaren Python-utvecklare för vårt Autonomous Driving-team i Göteborg. Kandidaten ska arbeta med perception pipeline, sensor fusion och realtidsbearbetning av LIDAR/kameradata. Krav på erfarenhet av Docker, Kubernetes samt CI/CD i AWS-miljö. Teamet arbetar agilt i 2-veckors sprintar.",
             required_skills=json.dumps(["python", "docker", "kubernetes", "aws", "sql", "fastapi"]),
             number_of_consultants=1, start_date=_ago(days=45), end_date=_ago(days=45) + timedelta(days=180),
             budget_max_hourly=1000, location="Göteborg", remote_ok=False, priority=RequestPriority.HIGH,
             status=RequestStatus.COMPLETED,
             ai_summary="Backend-utveckling med fokus på autonom körning. Hög komplexitet, kräver seniora kompetenser.",
             ai_category="Backend Development", ai_complexity_score=0.85, created_at=_ago(days=50)),

        # REQ-002: Spotify — IN_PROGRESS (konsult godkänd & aktiv)
        dict(id="req-002", customer_id="cust-002",
             title="Data Engineer — Recommendations Pipeline",
             description="Spotify söker en Data Engineer till vårt Recommendations-team. Du kommer bygga och optimera datapipelines i Spark/Airflow som driver vår musikrekommendationsmotor. Arbetet involverar hantering av petabyte-skala data, A/B-testning och nära samarbete med ML-teamet.",
             required_skills=json.dumps(["python", "spark", "sql", "etl", "aws", "pandas"]),
             number_of_consultants=1, start_date=_ago(days=20), end_date=_ago(days=20) + timedelta(days=120),
             budget_max_hourly=1000, location="Stockholm", remote_ok=True, priority=RequestPriority.MEDIUM,
             status=RequestStatus.IN_PROGRESS,
             ai_summary="Data engineering med fokus på rekommendationssystem. Kräver erfarenhet av storskalig databearbetning.",
             ai_category="Data Engineering", ai_complexity_score=0.78, created_at=_ago(days=30)),

        # REQ-003: SEB — ASSESSED (väntar tilldelning, urgent)
        dict(id="req-003", customer_id="cust-003",
             title="Cloud Architect — Digital Banking Platform",
             description="SEB driver en storskalig molnmigration av vår kärnbankplattform. Vi behöver en senior Cloud Architect som kan designa och implementera en multi-region AWS-arkitektur med fokus på säkerhet, compliance och 99.99% tillgänglighet. Kandidaten ska ha erfarenhet av finansiella system och PCI DSS.",
             required_skills=json.dumps(["aws", "azure", "terraform", "kubernetes", "docker", "networking"]),
             number_of_consultants=1, start_date=now + timedelta(days=10), end_date=now + timedelta(days=200),
             budget_max_hourly=1300, location="Stockholm", remote_ok=False, priority=RequestPriority.URGENT,
             status=RequestStatus.ASSESSED,
             ai_summary="Strategisk molnmigrering för bankplattform. Kräver seniora cloud- och säkerhetskompetenser. Hög budget motiverar topkandidater.",
             ai_category="Cloud Architecture", ai_complexity_score=0.92, created_at=_ago(days=5)),

        # REQ-004: Ericsson — IN_PROGRESS (konsult föreslagen, väntar accept)
        dict(id="req-004", customer_id="cust-004",
             title="DevOps Engineer — 5G Core Network",
             description="Ericsson söker en DevOps-ingenjör till vårt 5G Core-team. Arbetet omfattar CI/CD-pipelines, Kubernetes-kluster i edge-miljöer, och automatiserad testning. Du behöver gedigen erfarenhet av container-orkestration och Infrastructure as Code.",
             required_skills=json.dumps(["docker", "kubernetes", "terraform", "aws", "ci/cd", "python", "gitops"]),
             number_of_consultants=1, start_date=now + timedelta(days=5), end_date=now + timedelta(days=150),
             budget_max_hourly=1050, location="Linköping", remote_ok=True, priority=RequestPriority.HIGH,
             status=RequestStatus.IN_PROGRESS,
             ai_summary="DevOps för 5G Core. Kritisk infrastruktur med höga krav på tillförlitlighet och automation.",
             ai_category="DevOps / Infrastructure", ai_complexity_score=0.88, created_at=_ago(days=12)),

        # REQ-005: H&M — SUBMITTED (ny, ej analyserad)
        dict(id="req-005", customer_id="cust-005",
             title="React-utvecklare — E-commerce Replatform",
             description="H&M genomgår en stor re-platforming av vår e-handelssite. Vi behöver 2 erfarna React/TypeScript-utvecklare som kan arbeta med vår nya Next.js-baserade plattform. Fokus på prestanda, tillgänglighet (WCAG 2.1 AA) och mobilupplevelse.",
             required_skills=json.dumps(["react", "typescript", "next.js", "css", "figma"]),
             number_of_consultants=2, start_date=now + timedelta(days=15), end_date=now + timedelta(days=180),
             budget_max_hourly=950, location="Stockholm", remote_ok=True, priority=RequestPriority.MEDIUM,
             status=RequestStatus.SUBMITTED,
             ai_summary="Frontend-utveckling för e-handelsplattform. Kräver stark React/Next.js-kompetens med fokus på tillgänglighet.",
             ai_category="Frontend Development", ai_complexity_score=0.65, created_at=_ago(hours=6)),

        # REQ-006: Volvo — ASSESSED (ML-uppdrag)
        dict(id="req-006", customer_id="cust-001",
             title="ML Engineer — Predictive Maintenance",
             description="Volvo Cars söker en ML Engineer för att bygga predictive maintenance-modeller för vår nya elbilsplattform. Arbetet innebär att analysera sensordata från bilar i fält, träna modeller för komponentlivslängd och integrera inferens i vårt edge computing-system.",
             required_skills=json.dumps(["python", "machine learning", "pytorch", "docker", "mlops"]),
             number_of_consultants=1, start_date=now + timedelta(days=20), end_date=now + timedelta(days=240),
             budget_max_hourly=1150, location="Göteborg", remote_ok=False, priority=RequestPriority.HIGH,
             status=RequestStatus.ASSESSED,
             ai_summary="ML-utveckling för prediktivt underhåll. Kräver djup ML-kompetens och erfarenhet av produktionssystem.",
             ai_category="Machine Learning / AI", ai_complexity_score=0.90, created_at=_ago(days=3)),

        # REQ-007: SEB — IN_PROGRESS (Scrum Master pågående)
        dict(id="req-007", customer_id="cust-003",
             title="Scrum Master — Agile Transformation",
             description="SEB söker en erfaren Scrum Master / Agile Coach för att leda den agila transformationen av vår Private Banking-division. Du ska coacha 3 team, facilitera ceremonier och driva continuous improvement. Erfarenhet av SAFe i finanssektorn starkt meriterande.",
             required_skills=json.dumps(["scrum", "agile", "projektledning", "jira", "kanban", "SAFe"]),
             number_of_consultants=1, start_date=_ago(days=10), end_date=_ago(days=10) + timedelta(days=120),
             budget_max_hourly=900, location="Stockholm", remote_ok=False, priority=RequestPriority.MEDIUM,
             status=RequestStatus.IN_PROGRESS,
             ai_summary="Agil coachning för bankverksamhet. Kräver ledarerfarenhet och finansförståelse.",
             ai_category="Agile / Project Management", ai_complexity_score=0.55, created_at=_ago(days=18)),

        # REQ-008: Spotify — SUBMITTED (ny mobiluppdrag)
        dict(id="req-008", customer_id="cust-002",
             title="iOS-utvecklare — Spotify Car Thing 2.0",
             description="Spotify utvecklar nästa generation av Car Thing. Vi söker en iOS-utvecklare med erfarenhet av Swift, SwiftUI och Bluetooth LE-integration. Du ska arbeta med att bygga companion-appen som kommunicerar med vår in-car hardware.",
             required_skills=json.dumps(["swift", "ios", "react native", "kotlin"]),
             number_of_consultants=1, start_date=now + timedelta(days=25), end_date=now + timedelta(days=150),
             budget_max_hourly=1000, location="Stockholm", remote_ok=True, priority=RequestPriority.MEDIUM,
             status=RequestStatus.SUBMITTED,
             ai_summary="Mobil/IoT-utveckling. Kräver stark iOS-kompetens med hårdvaruintegration.",
             ai_category="Mobile Development", ai_complexity_score=0.72, created_at=_ago(hours=2)),

        # REQ-009: Ericsson — COMPLETED
        dict(id="req-009", customer_id="cust-004",
             title="Full Stack Developer — Internal Tools",
             description="Ericsson behöver en Full Stack-utvecklare för byggande av interna produktivitetsverktyg. React-frontend med Node.js/Python-backend. Verktygen ska stödja 5000+ ingenjörer och integreras med Jira, Confluence och GitLab.",
             required_skills=json.dumps(["react", "typescript", "node.js", "python", "aws", "sql"]),
             number_of_consultants=1, start_date=_ago(days=90), end_date=_ago(days=5),
             budget_max_hourly=900, location="Stockholm", remote_ok=True, priority=RequestPriority.LOW,
             status=RequestStatus.COMPLETED,
             ai_summary="Full stack-utveckling av interna verktyg. Standardkomplexitet.",
             ai_category="Full Stack Development", ai_complexity_score=0.50, created_at=_ago(days=100)),

        # REQ-010: H&M — ASSESSED (UX-design)
        dict(id="req-010", customer_id="cust-005",
             title="UX Designer — Design System & Mobile App",
             description="H&M bygger ett nytt koncerngemensamt design system (H&M, COS, & Other Stories, Weekday). Vi söker en senior UX/UI-designer med erfarenhet av att bygga och underhålla design systems i Figma.",
             required_skills=json.dumps(["ux", "ui", "figma", "user research", "design system", "prototyping"]),
             number_of_consultants=1, start_date=now + timedelta(days=8), end_date=now + timedelta(days=160),
             budget_max_hourly=900, location="Stockholm", remote_ok=True, priority=RequestPriority.MEDIUM,
             status=RequestStatus.ASSESSED,
             ai_summary="UX/UI-design för design system och mobilapp. Kräver bred designkompetens.",
             ai_category="UX / Design", ai_complexity_score=0.60, created_at=_ago(days=4)),

        # REQ-011: Volvo — SUBMITTED (urgent incident)
        dict(id="req-011", customer_id="cust-001",
             title="Incident Response — Produktionsstörning Volvo Connect",
             description="URGENT: Volvo Connect-plattformen upplever intermittenta prestandaproblem som påverkar 50 000+ lastbilskunder. Vi behöver en senior backend-/DevOps-person omedelbart för att felsöka, identifiera grundorsak och stabilisera miljön.",
             required_skills=json.dumps(["python", "docker", "kubernetes", "aws", "sql", "microservices"]),
             number_of_consultants=1, start_date=now, end_date=now + timedelta(days=30),
             budget_max_hourly=1300, location="Göteborg", remote_ok=False, priority=RequestPriority.URGENT,
             status=RequestStatus.SUBMITTED,
             ai_summary="Akut incident response. Kräver omedelbar tillgång och senior kompetens i cloud/backend.",
             ai_category="Incident Response / DevOps", ai_complexity_score=0.95, created_at=_ago(minutes=45)),

        # REQ-012: SEB — CANCELLED
        dict(id="req-012", customer_id="cust-003",
             title="Java-utvecklare — Legacy Migration",
             description="SEB planerade att migrera legacy Java 8-system. Projektet har pausats p.g.a. omprioriteringar internt.",
             required_skills=json.dumps(["java", "spring", "sql", "microservices"]),
             number_of_consultants=2, start_date=now + timedelta(days=30), end_date=now + timedelta(days=200),
             budget_max_hourly=900, location="Stockholm", remote_ok=False, priority=RequestPriority.LOW,
             status=RequestStatus.CANCELLED,
             ai_summary="Java-migrering — avbruten av kund.",
             ai_category="Backend Development", ai_complexity_score=0.60, created_at=_ago(days=25)),
    ]
    for rd in requests_data:
        db.add(StaffingRequest(**rd))
    db.flush()

    # ═══════════════════════════════════════════════════
    # FEASIBILITY ASSESSMENTS
    # ═══════════════════════════════════════════════════
    assessments = [
        FeasibilityAssessment(id="feas-001", request_id="req-001", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.92, availability_score=90, skills_match_score=95, budget_fit_score=85, timeline_score=88, compliance_score=92,
            matching_consultants=json.dumps(["cons-001", "cons-003"]),
            risks=json.dumps(["Konsulten är eftertraktad — risk för konkurrerande erbjudanden", "On-site krav begränsar kandidatpool"]),
            recommendations=json.dumps(["Agera snabbt med erbjudande till Johan Nilsson", "Förbered backup-kandidat"]),
            created_at=_ago(days=49)),
        FeasibilityAssessment(id="feas-002", request_id="req-002", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.88, availability_score=85, skills_match_score=92, budget_fit_score=90, timeline_score=80, compliance_score=95,
            matching_consultants=json.dumps(["cons-004", "cons-001"]),
            risks=json.dumps(["Spark-kompetens nischad — begränsat utbud", "Tidspress om Linnea ej tillgänglig"]),
            recommendations=json.dumps(["Linnea Eriksson är idealkandidat", "Verifiera Spotify-specifika säkerhetskrav"]),
            created_at=_ago(days=28)),
        FeasibilityAssessment(id="feas-003", request_id="req-003", overall_rating=FeasibilityRating.MEDIUM,
            confidence_score=0.75, availability_score=45, skills_match_score=88, budget_fit_score=95, timeline_score=60, compliance_score=78,
            matching_consultants=json.dumps(["cons-009", "cons-003"]),
            risks=json.dumps(["Daniel Öberg på tjänstledighet — tillgänglig om 30 dagar", "PCI DSS-krav kan kräva extra certifiering", "Urgent timeline svår att möta med nuvarande pool"]),
            recommendations=json.dumps(["Vänta på Daniel Öberg (bäst match) eller rekrytera externt", "Överväg delad leverans med partner", "Diskutera start-datum flexibilitet med kund"]),
            created_at=_ago(days=4)),
        FeasibilityAssessment(id="feas-004", request_id="req-004", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.91, availability_score=88, skills_match_score=96, budget_fit_score=92, timeline_score=85, compliance_score=90,
            matching_consultants=json.dumps(["cons-003", "cons-001"]),
            risks=json.dumps(["Oscar redan tilldelad Ericsson — intern omfördelning möjlig", "Linköping kräver ev. resekostnader"]),
            recommendations=json.dumps(["Oscar Pettersson perfekt match", "Johan Nilsson som backup"]),
            created_at=_ago(days=11)),
        FeasibilityAssessment(id="feas-006", request_id="req-006", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.87, availability_score=92, skills_match_score=90, budget_fit_score=88, timeline_score=90, compliance_score=85,
            matching_consultants=json.dumps(["cons-006", "cons-004"]),
            risks=json.dumps(["Hanna Ström mycket eftertraktad", "Eventuell MLOps-certifiering behövs"]),
            recommendations=json.dumps(["Hanna Ström idealkandidat — presentera omedelbart", "Förbered fallback med extern partner"]),
            created_at=_ago(days=2)),
        FeasibilityAssessment(id="feas-007", request_id="req-007", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.93, availability_score=78, skills_match_score=95, budget_fit_score=95, timeline_score=70, compliance_score=98,
            matching_consultants=json.dumps(["cons-007"]),
            risks=json.dumps(["Viktor avslutar nuvarande uppdrag om 14 dagar"]),
            recommendations=json.dumps(["Viktor Lund perfekt passning — tillsätt direkt vid frigörelse"]),
            created_at=_ago(days=17)),
        FeasibilityAssessment(id="feas-009", request_id="req-009", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.90, availability_score=85, skills_match_score=88, budget_fit_score=95, timeline_score=92, compliance_score=90,
            matching_consultants=json.dumps(["cons-002", "cons-005"]),
            risks=json.dumps(["Standarduppdrag — låg risk"]),
            recommendations=json.dumps(["Emma Andersson rekommenderas"]),
            created_at=_ago(days=98)),
        FeasibilityAssessment(id="feas-010", request_id="req-010", overall_rating=FeasibilityRating.HIGH,
            confidence_score=0.89, availability_score=95, skills_match_score=98, budget_fit_score=90, timeline_score=85, compliance_score=92,
            matching_consultants=json.dumps(["cons-010", "cons-005"]),
            risks=json.dumps(["Design system-arbete kräver långsiktigt engagemang"]),
            recommendations=json.dumps(["Maja Holmgren perfekt match — 98% kompetensmatch"]),
            created_at=_ago(days=3)),
    ]
    db.add_all(assessments)
    db.flush()

    # ═══════════════════════════════════════════════════
    # ASSIGNMENTS
    # ═══════════════════════════════════════════════════
    assignments = [
        # REQ-001: Volvo — Johan confirmed (completed request)
        Assignment(id="asgn-001", request_id="req-001", consultant_id="cons-001",
                   start_date=_ago(days=45), end_date=_ago(days=45) + timedelta(days=180),
                   hourly_rate=950, status="confirmed", created_at=_ago(days=48)),
        # REQ-002: Spotify — Linnea confirmed & active
        Assignment(id="asgn-002", request_id="req-002", consultant_id="cons-004",
                   start_date=_ago(days=20), end_date=_ago(days=20) + timedelta(days=120),
                   hourly_rate=950, status="confirmed", created_at=_ago(days=25)),
        # REQ-004: Ericsson — Oscar pending customer approval
        Assignment(id="asgn-003", request_id="req-004", consultant_id="cons-003",
                   start_date=now + timedelta(days=5), end_date=now + timedelta(days=150),
                   hourly_rate=1000, status="pending", created_at=_ago(days=3)),
        # REQ-007: SEB — Viktor confirmed & active
        Assignment(id="asgn-004", request_id="req-007", consultant_id="cons-007",
                   start_date=_ago(days=10), end_date=_ago(days=10) + timedelta(days=120),
                   hourly_rate=850, status="confirmed", created_at=_ago(days=15)),
        # REQ-009: Ericsson — Emma confirmed (completed)
        Assignment(id="asgn-005", request_id="req-009", consultant_id="cons-002",
                   start_date=_ago(days=90), end_date=_ago(days=5),
                   hourly_rate=900, status="confirmed", created_at=_ago(days=95)),
        # REQ-003: SEB Cloud — Daniel pending, Johan rejected
        Assignment(id="asgn-006", request_id="req-003", consultant_id="cons-009",
                   start_date=now + timedelta(days=30), end_date=now + timedelta(days=200),
                   hourly_rate=1200, status="pending", created_at=_ago(days=2)),
        Assignment(id="asgn-007", request_id="req-003", consultant_id="cons-001",
                   start_date=now + timedelta(days=10), end_date=now + timedelta(days=200),
                   hourly_rate=950, status="rejected", created_at=_ago(days=3)),
    ]
    db.add_all(assignments)
    db.flush()

    # ═══════════════════════════════════════════════════
    # COORDINATION ACTIONS
    # ═══════════════════════════════════════════════════
    actions = [
        # REQ-001 (completed)
        CoordinationAction(request_id="req-001", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=49)),
        CoordinationAction(request_id="req-001", action_type="skill_matching", description="AI-matchning av kompetenser", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=49)),
        CoordinationAction(request_id="req-001", action_type="compliance_check", description="Compliance-kontroll (arbetstid, non-compete)", status=ActionStatus.COMPLETED, assigned_to="Compliance Engine", order=3, created_at=_ago(days=49)),
        CoordinationAction(request_id="req-001", action_type="send_proposal", description="Skicka förslag till kund", status=ActionStatus.COMPLETED, assigned_to="Sara Lindqvist", order=4, result="Kund godkände Johan Nilsson", created_at=_ago(days=48)),
        CoordinationAction(request_id="req-001", action_type="contract_setup", description="Upprätta avtal och fakturaunderlag", status=ActionStatus.COMPLETED, assigned_to="Marcus Ek", order=5, created_at=_ago(days=46)),

        # REQ-003 (in progress)
        CoordinationAction(request_id="req-003", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=4)),
        CoordinationAction(request_id="req-003", action_type="skill_matching", description="AI-matchning av kompetenser", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=4)),
        CoordinationAction(request_id="req-003", action_type="compliance_check", description="PCI DSS-certifiering kontroll", status=ActionStatus.IN_PROGRESS, assigned_to="Compliance Engine", order=3, created_at=_ago(days=3)),
        CoordinationAction(request_id="req-003", action_type="send_proposal", description="Skicka förslag till kund", status=ActionStatus.PENDING, assigned_to="Sara Lindqvist", order=4, created_at=_ago(days=2)),

        # REQ-004
        CoordinationAction(request_id="req-004", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=11)),
        CoordinationAction(request_id="req-004", action_type="skill_matching", description="AI-matchning av kompetenser", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=11)),
        CoordinationAction(request_id="req-004", action_type="compliance_check", description="Compliance-kontroll", status=ActionStatus.COMPLETED, assigned_to="Compliance Engine", order=3, created_at=_ago(days=10)),
        CoordinationAction(request_id="req-004", action_type="send_proposal", description="Förslag skickat — väntar kundsvar", status=ActionStatus.IN_PROGRESS, assigned_to="Sara Lindqvist", order=4, created_at=_ago(days=3)),

        # REQ-006
        CoordinationAction(request_id="req-006", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=2)),
        CoordinationAction(request_id="req-006", action_type="skill_matching", description="AI-matchning mot ML-pool", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=2)),
        CoordinationAction(request_id="req-006", action_type="compliance_check", description="Compliance-kontroll", status=ActionStatus.PENDING, assigned_to="Compliance Engine", order=3, created_at=_ago(days=1)),

        # REQ-007
        CoordinationAction(request_id="req-007", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=17)),
        CoordinationAction(request_id="req-007", action_type="skill_matching", description="AI-matchning av kompetenser", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=17)),
        CoordinationAction(request_id="req-007", action_type="compliance_check", description="Compliance-kontroll", status=ActionStatus.COMPLETED, assigned_to="Compliance Engine", order=3, created_at=_ago(days=16)),
        CoordinationAction(request_id="req-007", action_type="send_proposal", description="Förslag godkänt av kund", status=ActionStatus.COMPLETED, assigned_to="Sara Lindqvist", order=4, result="Maria Karlsson godkände Viktor Lund", created_at=_ago(days=12)),

        # REQ-009 (completed)
        CoordinationAction(request_id="req-009", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=98)),
        CoordinationAction(request_id="req-009", action_type="skill_matching", description="AI-matchning av kompetenser", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=98)),
        CoordinationAction(request_id="req-009", action_type="compliance_check", description="Compliance-kontroll", status=ActionStatus.COMPLETED, assigned_to="Compliance Engine", order=3, created_at=_ago(days=97)),
        CoordinationAction(request_id="req-009", action_type="send_proposal", description="Förslag godkänt", status=ActionStatus.COMPLETED, assigned_to="Marcus Ek", order=4, result="Kund godkände Emma Andersson", created_at=_ago(days=95)),

        # REQ-010
        CoordinationAction(request_id="req-010", action_type="check_availability", description="Kontrollera konsulttillgänglighet", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=1, created_at=_ago(days=3)),
        CoordinationAction(request_id="req-010", action_type="skill_matching", description="AI-matchning mot design-pool", status=ActionStatus.COMPLETED, assigned_to="AI Engine", order=2, created_at=_ago(days=3)),
        CoordinationAction(request_id="req-010", action_type="compliance_check", description="Compliance-kontroll", status=ActionStatus.COMPLETED, assigned_to="Compliance Engine", order=3, created_at=_ago(days=2)),
    ]
    db.add_all(actions)
    db.flush()

    # ═══════════════════════════════════════════════════
    # TIMELINE EVENTS
    # ═══════════════════════════════════════════════════
    events = [
        # REQ-001 full lifecycle
        TimelineEvent(request_id="req-001", event_type="submitted", title="Förfrågan inskickad", description="Volvo Group skickade in förfrågan om senior Python-utvecklare", actor="Anna Lindström", created_at=_ago(days=50)),
        TimelineEvent(request_id="req-001", event_type="ai_analysis", title="AI-analys genomförd", description="Kategori: Backend Development | Komplexitet: 85% | 2 matchande konsulter", actor="AI Engine", created_at=_ago(days=50)),
        TimelineEvent(request_id="req-001", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG (92%) | Skills match: 95%", actor="AI Engine", created_at=_ago(days=49)),
        TimelineEvent(request_id="req-001", event_type="consultant_proposed", title="Konsult föreslagen", description="Johan Nilsson (Senior Backend Developer) föreslagen — 95% match", actor="Sara Lindqvist", created_at=_ago(days=48)),
        TimelineEvent(request_id="req-001", event_type="customer_approved", title="Kund godkände konsult", description="Anna Lindström godkände Johan Nilsson", actor="Anna Lindström", created_at=_ago(days=47)),
        TimelineEvent(request_id="req-001", event_type="assignment_started", title="Uppdrag startat", description="Johan Nilsson börjar hos Volvo Group", actor="System", created_at=_ago(days=45)),
        TimelineEvent(request_id="req-001", event_type="completed", title="Uppdrag slutfört", description="Uppdraget avslutat framgångsrikt. Kundnöjdhet: 9/10", actor="System", created_at=_ago(days=2)),

        # REQ-002
        TimelineEvent(request_id="req-002", event_type="submitted", title="Förfrågan inskickad", description="Spotify söker Data Engineer", actor="Erik Johansson", created_at=_ago(days=30)),
        TimelineEvent(request_id="req-002", event_type="ai_analysis", title="AI-analys genomförd", description="Kategori: Data Engineering | Komplexitet: 78%", actor="AI Engine", created_at=_ago(days=30)),
        TimelineEvent(request_id="req-002", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG (88%)", actor="AI Engine", created_at=_ago(days=28)),
        TimelineEvent(request_id="req-002", event_type="consultant_proposed", title="Konsult föreslagen", description="Linnea Eriksson föreslagen — 92% match", actor="Sara Lindqvist", created_at=_ago(days=25)),
        TimelineEvent(request_id="req-002", event_type="customer_approved", title="Kund godkände konsult", description="Erik Johansson godkände Linnea Eriksson", actor="Erik Johansson", created_at=_ago(days=22)),
        TimelineEvent(request_id="req-002", event_type="assignment_started", title="Uppdrag startat", description="Linnea Eriksson börjar hos Spotify", actor="System", created_at=_ago(days=20)),

        # REQ-003
        TimelineEvent(request_id="req-003", event_type="submitted", title="Förfrågan inskickad", description="SEB söker Cloud Architect — URGENT", actor="Maria Karlsson", created_at=_ago(days=5)),
        TimelineEvent(request_id="req-003", event_type="ai_analysis", title="AI-analys genomförd", description="Kategori: Cloud Architecture | Komplexitet: 92% | Hög prioritet flaggad", actor="AI Engine", created_at=_ago(days=5)),
        TimelineEvent(request_id="req-003", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: MEDIUM — tillgänglighet begränsad (45%). Daniel Öberg bäst match men på tjänstledighet.", actor="AI Engine", created_at=_ago(days=4)),
        TimelineEvent(request_id="req-003", event_type="consultant_rejected", title="Konsult nekad av kund", description="Johan Nilsson föreslagen men avböjd av SEB — saknar finansbransch-erfarenhet", actor="Maria Karlsson", created_at=_ago(days=3)),
        TimelineEvent(request_id="req-003", event_type="consultant_proposed", title="Ny konsult föreslagen", description="Daniel Öberg föreslagen — tillgänglig om 30 dagar. Väntar kundsvar.", actor="Sara Lindqvist", created_at=_ago(days=2)),

        # REQ-004
        TimelineEvent(request_id="req-004", event_type="submitted", title="Förfrågan inskickad", description="Ericsson söker DevOps Engineer för 5G Core", actor="Lars Svensson", created_at=_ago(days=12)),
        TimelineEvent(request_id="req-004", event_type="ai_analysis", title="AI-analys genomförd", description="Kategori: DevOps / Infrastructure | Komplexitet: 88%", actor="AI Engine", created_at=_ago(days=12)),
        TimelineEvent(request_id="req-004", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG (91%) | Oscar Pettersson rekommenderas", actor="AI Engine", created_at=_ago(days=11)),
        TimelineEvent(request_id="req-004", event_type="consultant_proposed", title="Konsult föreslagen", description="Oscar Pettersson föreslagen — 96% match. Väntar kundens godkännande.", actor="Sara Lindqvist", created_at=_ago(days=3)),

        # REQ-005 (just submitted)
        TimelineEvent(request_id="req-005", event_type="submitted", title="Förfrågan inskickad", description="H&M söker 2 React-utvecklare för e-commerce replatforming", actor="Sofia Bergman", created_at=_ago(hours=6)),

        # REQ-006
        TimelineEvent(request_id="req-006", event_type="submitted", title="Förfrågan inskickad", description="Volvo söker ML Engineer för prediktivt underhåll", actor="Anna Lindström", created_at=_ago(days=3)),
        TimelineEvent(request_id="req-006", event_type="ai_analysis", title="AI-analys genomförd", description="Kategori: Machine Learning / AI | Komplexitet: 90%", actor="AI Engine", created_at=_ago(days=3)),
        TimelineEvent(request_id="req-006", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG — Hanna Ström idealkandidat med 90% match", actor="AI Engine", created_at=_ago(days=2)),

        # REQ-007
        TimelineEvent(request_id="req-007", event_type="submitted", title="Förfrågan inskickad", description="SEB söker Scrum Master", actor="Maria Karlsson", created_at=_ago(days=18)),
        TimelineEvent(request_id="req-007", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG — Viktor Lund perfekt match", actor="AI Engine", created_at=_ago(days=17)),
        TimelineEvent(request_id="req-007", event_type="customer_approved", title="Kund godkände konsult", description="Maria Karlsson godkände Viktor Lund", actor="Maria Karlsson", created_at=_ago(days=12)),
        TimelineEvent(request_id="req-007", event_type="assignment_started", title="Uppdrag startat", description="Viktor Lund börjar som Scrum Master hos SEB", actor="System", created_at=_ago(days=10)),

        # REQ-008 (just submitted)
        TimelineEvent(request_id="req-008", event_type="submitted", title="Förfrågan inskickad", description="Spotify söker iOS-utvecklare för Car Thing 2.0", actor="Erik Johansson", created_at=_ago(hours=2)),

        # REQ-009 (completed)
        TimelineEvent(request_id="req-009", event_type="submitted", title="Förfrågan inskickad", description="Ericsson söker Full Stack Developer", actor="Lars Svensson", created_at=_ago(days=100)),
        TimelineEvent(request_id="req-009", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG (90%)", actor="AI Engine", created_at=_ago(days=98)),
        TimelineEvent(request_id="req-009", event_type="customer_approved", title="Kund godkände konsult", description="Lars Svensson godkände Emma Andersson", actor="Lars Svensson", created_at=_ago(days=92)),
        TimelineEvent(request_id="req-009", event_type="assignment_started", title="Uppdrag startat", description="Emma Andersson börjar hos Ericsson", actor="System", created_at=_ago(days=90)),
        TimelineEvent(request_id="req-009", event_type="completed", title="Uppdrag slutfört", description="Framgångsrikt levererat — 3 interna verktyg i produktion", actor="System", created_at=_ago(days=5)),

        # REQ-010
        TimelineEvent(request_id="req-010", event_type="submitted", title="Förfrågan inskickad", description="H&M söker UX Designer", actor="Sofia Bergman", created_at=_ago(days=4)),
        TimelineEvent(request_id="req-010", event_type="assessed", title="Genomförbarhetsanalys klar", description="Overall: HÖG — Maja Holmgren 98% match", actor="AI Engine", created_at=_ago(days=3)),

        # REQ-011 (urgent, just in)
        TimelineEvent(request_id="req-011", event_type="submitted", title="🚨 Akut förfrågan", description="Volvo Connect — produktionsstörning. 50 000+ kunder påverkade.", actor="Anna Lindström", created_at=_ago(minutes=45)),

        # REQ-012 (cancelled)
        TimelineEvent(request_id="req-012", event_type="submitted", title="Förfrågan inskickad", description="SEB söker Java-utvecklare", actor="Maria Karlsson", created_at=_ago(days=25)),
        TimelineEvent(request_id="req-012", event_type="cancelled", title="Förfrågan avbruten", description="Projektet pausat p.g.a. interna omprioriteringar hos SEB", actor="Maria Karlsson", created_at=_ago(days=15)),
    ]
    db.add_all(events)
    db.flush()

    # ═══════════════════════════════════════════════════
    # NOTIFICATIONS
    # ═══════════════════════════════════════════════════
    notifications = [
        # Handler Sara
        Notification(user_id="user-handler-1", title="🚨 Akut förfrågan", message="Volvo Group: Incident Response — Produktionsstörning Volvo Connect. 50 000+ kunder påverkade.", notification_type="urgent", is_read=False, link="req-011", created_at=_ago(minutes=45)),
        Notification(user_id="user-handler-1", title="Ny förfrågan", message="Spotify: iOS-utvecklare — Car Thing 2.0", notification_type="info", is_read=False, link="req-008", created_at=_ago(hours=2)),
        Notification(user_id="user-handler-1", title="Ny förfrågan", message="H&M Group: 2 React-utvecklare — E-commerce Replatform", notification_type="info", is_read=False, link="req-005", created_at=_ago(hours=6)),
        Notification(user_id="user-handler-1", title="Konsult nekad", message="SEB avböjde Johan Nilsson för Cloud Architect (saknar finanserfarenhet). Ny kandidat behövs.", notification_type="warning", is_read=True, link="req-003", created_at=_ago(days=3)),
        Notification(user_id="user-handler-1", title="Väntar på kundsvar", message="Ericsson: Oscar Pettersson föreslagen för DevOps 5G Core. Väntar godkännande.", notification_type="info", is_read=True, link="req-004", created_at=_ago(days=3)),
        Notification(user_id="user-handler-1", title="AI-analys klar", message="Volvo ML Engineer: Genomförbarhetsanalys klar — HÖG (87%). Hanna Ström rekommenderas.", notification_type="success", is_read=True, link="req-006", created_at=_ago(days=2)),
        Notification(user_id="user-handler-1", title="Uppdrag startat", message="Linnea Eriksson har börjat hos Spotify som Data Engineer.", notification_type="success", is_read=True, link="req-002", created_at=_ago(days=20)),
        Notification(user_id="user-handler-1", title="Uppdrag avslutat", message="Johan Nilsson — Volvo Autonomous Driving slutfört framgångsrikt.", notification_type="success", is_read=True, link="req-001", created_at=_ago(days=2)),

        # Admin
        Notification(user_id="user-admin", title="🚨 Akut förfrågan", message="Volvo Group: Produktionsstörning — kräver omedelbar handling.", notification_type="urgent", is_read=False, link="req-011", created_at=_ago(minutes=45)),
        Notification(user_id="user-admin", title="Ny förfrågan", message="Spotify söker iOS-utvecklare", notification_type="info", is_read=False, link="req-008", created_at=_ago(hours=2)),
        Notification(user_id="user-admin", title="Ny förfrågan", message="H&M söker 2 React-utvecklare", notification_type="info", is_read=False, link="req-005", created_at=_ago(hours=6)),

        # Volvo (cust-001)
        Notification(user_id="user-cust-001", title="Förfrågan mottagen", message="Din förfrågan 'ML Engineer — Predictive Maintenance' har tagits emot och AI-analyseras.", notification_type="success", is_read=False, link="req-006", created_at=_ago(days=3)),
        Notification(user_id="user-cust-001", title="🚨 Förfrågan mottagen", message="Din akuta förfrågan om incident response har tagits emot. Vi prioriterar detta.", notification_type="urgent", is_read=False, link="req-011", created_at=_ago(minutes=44)),
        Notification(user_id="user-cust-001", title="Uppdrag avslutat", message="Johan Nilssons uppdrag (Autonomous Driving) har avslutats framgångsrikt.", notification_type="success", is_read=True, link="req-001", created_at=_ago(days=2)),

        # Spotify (cust-002)
        Notification(user_id="user-cust-002", title="Konsult tilldelad", message="Linnea Eriksson har tilldelats 'Data Engineer — Recommendations Pipeline'.", notification_type="success", is_read=True, link="req-002", created_at=_ago(days=25)),

        # SEB (cust-003)
        Notification(user_id="user-cust-003", title="Konsult föreslagen", message="Daniel Öberg har föreslagits för 'Cloud Architect'. Väntar på ert godkännande.", notification_type="info", is_read=False, link="req-003", created_at=_ago(days=2)),
        Notification(user_id="user-cust-003", title="Konsult nekad", message="Ni avböjde Johan Nilsson. Vi söker alternativa kandidater.", notification_type="warning", is_read=True, link="req-003", created_at=_ago(days=3)),
    ]
    db.add_all(notifications)
    db.commit()

    print(f"✅ Seeded: {len(customers)} customers, {len(consultants)} consultants, "
          f"{len(requests_data)} requests, {len(assignments)} assignments, "
          f"{len(assessments)} assessments, {len(notifications)} notifications")
