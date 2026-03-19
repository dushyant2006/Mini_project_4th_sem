# ============================================================
# api/main.py
# PURPOSE: FastAPI app with full security configuration
#          JWT Auth, RBAC, Rate Limiting, CORS, Security Headers
# ============================================================

import os
import sys
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import incidents, anomalies, services
from api.routes.auth import router as auth_router

# ── Rate Limiter ───────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="Project 71 — AIOps Platform API",
    description="""
## Autonomous Incident Response & Root-Cause Intelligence Platform

### Authentication
This API uses **JWT Bearer token** authentication.

1. Call `POST /auth/login` with username and password
2. Copy the `access_token` from the response
3. Click **Authorize** above and enter: `Bearer <your_token>`

### Default Accounts
| Username | Password | Role | Access |
|---|---|---|---|
| admin | admin123 | Admin | Full access |
| operator | operator123 | Operator | Read + Write |
| viewer | viewer123 | Viewer | Read only |

### Rate Limits
- Auth endpoints: **10 requests/minute**
- Read endpoints: **100 requests/minute**
- Write endpoints: **20 requests/minute**
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiter State ─────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# ── Security Headers Middleware ────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response   = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]      = "geolocation=(), microphone=()"
    response.headers["Cache-Control"]           = "no-store"
    response.headers["X-Process-Time"]          = (
        str(round((time.time() - start_time) * 1000, 2)) + "ms"
    )
    return response

# ── Global Exception Handlers ──────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = [
        {
            "field":   " → ".join(str(loc) for loc in e["loc"]),
            "message": e["msg"],
            "type":    e["type"],
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error":   "Validation Error",
            "details": errors,
            "tip":     "Check /docs for correct request format"
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "path":  str(request.url.path),
            "tip":   "See all endpoints at /docs"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error":   "Internal Server Error",
            "message": "An unexpected error occurred.",
            "tip":     "Check server logs for details"
        }
    )

# ── Routers ────────────────────────────────────────────────
app.include_router(auth_router,      prefix="/auth",      tags=["Authentication"])
app.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
app.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
app.include_router(services.router,  prefix="/services",  tags=["Services"])

# ── Root ───────────────────────────────────────────────────
@app.get("/", tags=["Health"])
@limiter.limit("60/minute")
async def root(request: Request):
    return {
        "platform": "Project 71 — AIOps Platform",
        "version":  "2.0.0",
        "auth":     "POST /auth/login to get JWT token",
        "docs":     "/docs",
    }

# ── Health ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
@limiter.limit("60/minute")
async def health(request: Request):
    return {
        "status":  "healthy",
        "version": "2.0.0",
        "security": {
            "authentication":  "JWT Bearer",
            "authorization":   "RBAC (admin/operator/viewer)",
            "rate_limiting":   "enabled",
            "cors":            "configured",
            "security_headers": "enabled",
        }
    }

# ── ML Metrics ─────────────────────────────────────────────
@app.get("/metrics/models", tags=["Metrics"])
@limiter.limit("30/minute")
async def model_metrics(request: Request):
    """Returns ML model performance metrics — precision, recall, F1-score."""
    try:
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        from detection.model_metrics import metrics_tracker
        return metrics_tracker.get_summary()
    except Exception as e:
        return {
            "message": "Metrics initializing — run detection engine first",
            "error":   str(e)
        }
