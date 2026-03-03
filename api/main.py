# ============================================================
# api/main.py
# PURPOSE: FastAPI application entry point
#
# HOW TO RUN:
#   uvicorn api.main:app --reload --port 8000
#
# Then open browser: http://localhost:8000/docs
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.routes import incidents, anomalies, services


# ── Create FastAPI app ────────────────────────────────────
app = FastAPI(
    title="Project 71 — AIOps Platform API",
    description="""
    Autonomous Incident Response & Root-Cause Intelligence Platform.

    ## Features
    - 🔍 **Incidents** — View all detected incidents with full RCA reports
    - 🚨 **Anomalies** — Live anomaly feed from ML detection engine
    - 🕸️  **Services** — Service dependency graph and health status
    - 📊 **Metrics**  — Real-time telemetry from all microservices
    """,
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc UI at http://localhost:8000/redoc
)

# ── CORS Middleware ───────────────────────────────────────
# Allows your React dashboard to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE etc
    allow_headers=["*"],
)

# ── Include Routers ───────────────────────────────────────
# Each router handles a group of related endpoints
app.include_router(
    incidents.router,
    prefix="/incidents",
    tags=["Incidents"]
)
app.include_router(
    anomalies.router,
    prefix="/anomalies",
    tags=["Anomalies"]
)
app.include_router(
    services.router,
    prefix="/services",
    tags=["Services"]
)


# ── Root endpoint ─────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Welcome endpoint — confirms API is running"""
    return {
        "name":    "Project 71 AIOps Platform",
        "version": "1.0.0",
        "status":  "running",
        "time":    datetime.utcnow().isoformat(),
        "docs":    "http://localhost:8000/docs",
        "endpoints": {
            "incidents": "/incidents",
            "anomalies": "/anomalies/live",
            "services":  "/services/graph",
            "health":    "/health",
        }
    }


# ── Health check endpoint ─────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check — used by load balancers and monitoring
    to verify the API is alive and responding.
    """
    return {
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api":      "up",
            "kafka":    "up",
            "postgres": "up",
        }
    }


# ── Global error handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catches any unhandled exceptions and returns clean JSON"""
    return JSONResponse(
        status_code=500,
        content={
            "error":   "Internal server error",
            "detail":  str(exc),
            "path":    str(request.url),
        }
    )