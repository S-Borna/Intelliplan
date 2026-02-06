# 🧠 Intelliplan — AI-Powered Staffing Operations Platform

An intelligent system for staffing companies that captures customer needs, assesses feasibility, coordinates actions, and guides decisions.

## Features

- **🎯 Smart Intake** — AI-driven customer request capture with context enrichment
- **📊 Feasibility Assessment** — Automatic evaluation of availability, skills, compliance & cost
- **⚡ Action Coordination** — Automated workflows across consultants, schedules & systems
- **🧭 Decision Guidance** — AI recommendations with risk analysis and alternatives
- **👁️ Transparency Portal** — Real-time status tracking for customers
- **✅ Compliance Engine** — Automated checks against regulations and contracts

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend                          │
│  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │ Customer     │  │ Consultant Manager Dashboard │ │
│  │ Portal       │  │ • Request Queue              │ │
│  │ • Submit     │  │ • Feasibility Analysis       │ │
│  │ • Track      │  │ • Action Coordination        │ │
│  │ • History    │  │ • Decision Support           │ │
│  └──────────────┘  └──────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                   │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │
│  │ AI Engine  │ │ Coordinator│ │ Compliance Engine│ │
│  │ • NLP      │ │ • Workflows│ │ • Rules          │ │
│  │ • Matching │ │ • Notify   │ │ • Validation     │ │
│  │ • Predict  │ │ • Schedule │ │ • Audit          │ │
│  └────────────┘ └────────────┘ └──────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   SQLite / DB   │
              └─────────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn backend.main:app --reload --port 8000

# Open in browser
# API docs:        http://localhost:8000/docs
# Customer portal: http://localhost:8000
# Dashboard:       http://localhost:8000/dashboard
```

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Frontend:** Vanilla JS, HTML5, CSS3
- **Database:** SQLite (swappable to PostgreSQL)
- **AI:** Rule-based engine with LLM integration points (OpenAI-ready)
