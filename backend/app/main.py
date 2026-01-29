"""
GitHub Guardrails - ULTIMATE Backend
Complete enterprise-grade security guardrails solution
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from loguru import logger

from app.api.ultimate_routes import router as ultimate_router


# Create FastAPI app
app = FastAPI(
    title="GitHub Guardrails - Ultimate Edition",
    description="Enterprise-grade security guardrails with 10-step analysis pipeline",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except:
    logger.warning("Static directory not found, dashboard may not work")

# Include API routes
app.include_router(ultimate_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - welcome message"""
    return {
        "message": "🛡️ GitHub Guardrails - Ultimate Edition",
        "version": "2.0.0",
        "features": {
            "static_analysis": True,
            "secrets_detection": True,
            "license_scanning": True,
            "duplication_detection": True,
            "coding_standards": True,
            "enterprise_rules": True,
            "ai_analysis": True,
            "ai_validation": True,
            "policy_enforcement": True,
            "audit_logging": True,
            "dashboard": True
        },
        "endpoints": {
            "health": "/health",
            "dashboard": "/dashboard",
            "api_docs": "/docs",
            "analyze": "/api/analyze/file",
            "policy": "/api/policy/{owner}/{repo}",
            "audit": "/api/audit/history",
            "statistics": "/api/audit/statistics"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini": "configured" if os.getenv('GEMINI_API_KEY') else "not configured",
        "scanners": {
            "static_analysis": "active",
            "secrets_detection": "active",
            "license_scanning": "active",
            "duplication_detection": "active",
            "coding_standards": "active",
            "enterprise_rules": "active",
            "ai_analysis": "active" if os.getenv('GEMINI_API_KEY') else "disabled",
            "audit_logging": "active"
        }
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    try:
        with open("app/static/dashboard.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("✅ Backend ready")
    logger.info("🚀 Backend starting...")
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        logger.info("Gemini: ✅")
    else:
        logger.warning("Gemini: ❌ (AI features disabled)")
    
    logger.info("📊 Dashboard: http://localhost:8000/dashboard")
    logger.info("📚 API Docs: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("👋 Backend shutting down")
