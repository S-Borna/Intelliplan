"""
Intelliplan — AI-Powered Staffing Operations Platform.

Main FastAPI application with static file serving.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, SessionLocal
from backend.routers import requests, customers, dashboard, auth, notifications
from backend.seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed data on startup."""
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Intelliplan",
    description="AI-Powered Staffing Operations Platform — captures customer needs, assesses feasibility, coordinates actions, and guides decisions.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Routers ────────────────────────────────────────

app.include_router(auth.router)
app.include_router(notifications.router)
app.include_router(requests.router)
app.include_router(customers.router)
app.include_router(dashboard.router)

# ── Static Files ───────────────────────────────────

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serve the main frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login")
async def serve_login():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/portal")
async def serve_portal():
    return FileResponse(FRONTEND_DIR / "index.html")
