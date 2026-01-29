"""
ULTIMATE API Routes - Complete Implementation
All endpoints for enterprise-grade guardrails
"""

import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.engines.ultimate_hybrid_engine import create_ultimate_engine
from app.core.policy_engine import get_policy_engine, PolicyConfig, EnforcementMode
from app.services.audit_service import get_audit_logger
import os

router = APIRouter()

# Initialize services
_engine = create_ultimate_engine(
    gemini_key=os.getenv('GEMINI_API_KEY', ''),
    rules_dir='/app/config'
)
_policy_engine = get_policy_engine()
_audit_logger = get_audit_logger()


# Request/Response Models

class AnalyzeRequest(BaseModel):
    code: str
    filename: str
    language: str
    copilot_detected: bool = False
    enabled_rule_packs: Optional[List[str]] = None
    repository: Optional[str] = None
    pr_number: Optional[int] = None
    user_id: Optional[str] = None


class BatchAnalyzeRequest(BaseModel):
    files: List[dict]
    copilot_detected: bool = False
    enabled_rule_packs: Optional[List[str]] = None


class ResolutionUpdate(BaseModel):
    scan_id: str
    resolution_state: str
    override_approved: bool = False
    override_approver: Optional[str] = None
    notes: Optional[str] = None


# Main Analysis Endpoints

@router.post("/analyze/file")
async def analyze_file(request: AnalyzeRequest):
    """
    COMPLETE file analysis with ALL scanners
    - Static analysis (Bandit, ESLint)
    - Secrets detection (patterns + entropy)
    - License scanning (pattern-based)
    - Code duplication detection
    - Coding standards enforcement
    - Enterprise rules (YAML packs)
    - AI deep analysis (Gemini)
    - AI validation (reduces false positives)
    """
    start = time.time()
    
    try:
        # Get policy
        policy = _policy_engine.get_policy(
            repo_name=request.repository or "default",
            is_copilot_generated=request.copilot_detected
        )
        
        # Run complete analysis
        result = await _engine.analyze(
            code=request.code,
            filename=request.filename,
            language=request.language,
            copilot_detected=request.copilot_detected,
            enabled_rule_packs=request.enabled_rule_packs
        )
        
        violations = result['violations']
        duration = time.time() - start
        
        # Determine policy action
        policy_action = _policy_engine.determine_action(policy, violations)
        
        analysis_id = f"scan_{int(time.time())}"
        
        # Log to audit trail
        await _audit_logger.log_scan(
            scan_id=analysis_id,
            repository=request.repository or "unknown",
            file_path=request.filename,
            language=request.language,
            violations=violations,
            policy_action=policy_action,
            duration=duration,
            copilot_detected=request.copilot_detected,
            user_id=request.user_id,
            pr_number=request.pr_number
        )
        
        return {
            "violations": violations,
            "total_count": len(violations),
            "by_severity": result['by_severity'],
            "by_source": result['by_source'],
            "by_type": result['by_type'],
            "duration": duration,
            "analysis_id": analysis_id,
            "copilot_detected": request.copilot_detected,
            "policy_action": policy_action,
            "pipeline_steps": result['pipeline_steps']
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/analyze/batch")
async def analyze_batch(request: BatchAnalyzeRequest):
    """Analyze multiple files in parallel"""
    start = time.time()
    
    try:
        result = await _engine.batch_analyze(
            files=request.files,
            copilot_detected=request.copilot_detected,
            enabled_rule_packs=request.enabled_rule_packs
        )
        
        duration = time.time() - start
        result['duration'] = duration
        
        return result
        
    except Exception as e:
        raise HTTPException(500, str(e))


# Policy Management Endpoints

@router.get("/policy/{owner}/{repo}")
async def get_policy(owner: str, repo: str):
    """Get policy configuration for a repository"""
    try:
        repo_name = f"{owner}/{repo}"
        policy = _policy_engine.get_policy(repo_name)
        
        return {
            "repository": repo_name,
            "mode": policy.mode.value,
            "block_on_critical": policy.block_on_critical,
            "block_on_high": policy.block_on_high,
            "max_medium_violations": policy.max_medium_violations,
            "max_low_violations": policy.max_low_violations,
            "allow_override": policy.allow_override,
            "override_approvers": policy.override_approvers,
            "copilot_strict_mode": policy.copilot_strict_mode
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/policy/{owner}/{repo}")
async def set_policy(owner: str, repo: str, policy: PolicyConfig):
    """Set custom policy for a repository"""
    try:
        repo_name = f"{owner}/{repo}"
        _policy_engine.set_policy(repo_name, policy)
        
        return {"message": "Policy updated successfully", "repository": repo_name}
        
    except Exception as e:
        raise HTTPException(500, str(e))


# Scanner Status Endpoints

@router.get("/scanners/status")
async def get_scanners_status():
    """Get availability status of all scanners"""
    return {
        "static_analysis": {
            "python": True,
            "javascript": True
        },
        "secrets_detection": {
            "pattern_based": True,
            "entropy_detection": True,
            "detect_secrets": _engine.secrets.has_detect_secrets
        },
        "license_scanning": {
            "pattern_based": True,
            "scancode": _engine.licenses.has_scancode
        },
        "duplication_detection": {
            "enabled": True,
            "algorithms": ["similarity", "hash-based", "oss-matching"]
        },
        "coding_standards": {
            "enabled": True,
            "languages": ["python", "javascript", "typescript"]
        },
        "enterprise_rules": {
            "enabled": True,
            "rule_packs": _engine.rules.get_available_packs()
        },
        "ai_analysis": {
            "enabled": _engine.ai is not None,
            "provider": "Gemini" if _engine.ai else None
        }
    }


# Audit & Reporting Endpoints

@router.get("/audit/history")
async def get_audit_history(
    repository: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get audit log history"""
    try:
        history = await _audit_logger.get_scan_history(
            repository=repository,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "scans": history,
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/audit/statistics")
async def get_statistics(
    repository: Optional[str] = None,
    days: int = 30
):
    """Get aggregate statistics"""
    try:
        stats = await _audit_logger.get_statistics(repository=repository, days=days)
        trends = await _audit_logger.get_violation_trends(repository=repository, days=days)
        top_violations = await _audit_logger.get_top_violations(repository=repository, limit=10)
        
        return {
            "statistics": stats,
            "trends": trends,
            "top_violations": top_violations
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/audit/resolution")
async def update_resolution(update: ResolutionUpdate):
    """Update scan resolution state"""
    try:
        await _audit_logger.update_resolution(
            scan_id=update.scan_id,
            resolution_state=update.resolution_state,
            override_approved=update.override_approved,
            override_approver=update.override_approver,
            notes=update.notes
        )
        
        return {"message": "Resolution updated successfully"}
        
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/audit/export/csv")
async def export_audit_csv(
    repository: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export audit logs to CSV"""
    try:
        output_path = f"/tmp/audit_export_{int(time.time())}.csv"
        
        await _audit_logger.export_to_csv(
            output_path=output_path,
            repository=repository,
            start_date=start_date,
            end_date=end_date
        )
        
        return FileResponse(
            path=output_path,
            filename="audit_export.csv",
            media_type="text/csv"
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/audit/export/json")
async def export_audit_json(
    repository: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export audit logs to JSON"""
    try:
        output_path = f"/tmp/audit_export_{int(time.time())}.json"
        
        await _audit_logger.export_to_json(
            output_path=output_path,
            repository=repository,
            start_date=start_date,
            end_date=end_date
        )
        
        return FileResponse(
            path=output_path,
            filename="audit_export.json",
            media_type="application/json"
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))


# Dashboard Endpoint

@router.get("/dashboard/data")
async def get_dashboard_data(repository: Optional[str] = None):
    """Get dashboard data for visualization"""
    try:
        stats = await _audit_logger.get_statistics(repository=repository, days=30)
        trends = await _audit_logger.get_violation_trends(repository=repository, days=7)
        top_violations = await _audit_logger.get_top_violations(repository=repository, limit=10)
        
        # Calculate additional metrics
        total_scans = stats.get('total_scans', 0)
        total_violations = stats.get('total_violations', 0)
        avg_violations_per_scan = total_violations / total_scans if total_scans > 0 else 0
        
        return {
            "summary": {
                "total_scans": total_scans,
                "total_violations": total_violations,
                "avg_violations_per_scan": round(avg_violations_per_scan, 2),
                "critical_violations": stats.get('critical_violations', 0),
                "high_violations": stats.get('high_violations', 0),
                "medium_violations": stats.get('medium_violations', 0),
                "low_violations": stats.get('low_violations', 0),
                "avg_duration": round(stats.get('avg_duration', 0), 2),
                "blocked_scans": stats.get('blocked_scans', 0),
                "copilot_scans": stats.get('copilot_scans', 0)
            },
            "trends": trends,
            "top_violations": top_violations
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))
