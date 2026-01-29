"""
Complete API Routes - 100% Implementation
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import time

from app.engines.complete_hybrid_engine import create_complete_engine
from app.core.config import settings
from app.core.policy_engine import get_policy_engine, PolicyConfig, EnforcementMode

logger = logging.getLogger(__name__)
router = APIRouter()

# Services
_engine = None
_policy_engine = get_policy_engine()

def get_engine():
    global _engine
    if not _engine:
        _engine = create_complete_engine(
            gemini_key=settings.GEMINI_API_KEY,
            rules_dir="config"
        )
    return _engine

# Models
class AnalyzeRequest(BaseModel):
    code: str
    filename: str
    language: str
    repository: Optional[str] = None
    pr_number: Optional[int] = None
    copilot_detected: bool = False
    enabled_rule_packs: Optional[List[str]] = None

class AnalyzeResponse(BaseModel):
    violations: List[Dict]
    total_count: int
    by_severity: Dict[str, int]
    by_source: Dict[str, int]
    duration: float
    analysis_id: str
    copilot_detected: bool
    policy_action: Optional[Dict] = None

class PolicyConfigRequest(BaseModel):
    mode: EnforcementMode
    allow_override: bool = False
    override_approvers: List[str] = []
    block_on_critical: bool = True
    block_on_high: bool = False
    copilot_strict_mode: bool = True

# Endpoints
@router.post("/analyze/file", response_model=AnalyzeResponse)
async def analyze_file(
    request: AnalyzeRequest,
    engine = Depends(get_engine)
):
    """
    COMPLETE file analysis with all scanners
    - Static analysis (Bandit, ESLint patterns)
    - Secrets detection (detect-secrets, entropy)
    - License scanning (ScanCode)
    - Enterprise rules (YAML packs)
    - AI deep analysis (Gemini)
    - AI validation (reduces false positives)
    """
    start = time.time()
    
    try:
        logger.info(f"📁 Complete analysis: {request.filename}")
        
        # Get policy
        policy = _policy_engine.get_policy(
            repo_name=request.repository or "default",
            is_copilot_generated=request.copilot_detected
        )
        
        # Run complete analysis
        result = await engine.analyze(
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
        
        logger.info(f"✅ Complete analysis: {len(violations)} issues in {duration:.2f}s")
        logger.info(f"   Policy: {policy_action['github_status']['state']}")
        
        return {
            "violations": violations,
            "total_count": len(violations),
            "by_severity": result['by_severity'],
            "by_source": result['by_source'],
            "duration": duration,
            "analysis_id": analysis_id,
            "copilot_detected": request.copilot_detected,
            "policy_action": policy_action
        }
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@router.post("/analyze/batch")
async def analyze_batch(
    files: List[AnalyzeRequest],
    engine = Depends(get_engine)
):
    """Analyze multiple files in parallel"""
    try:
        # Prepare files
        file_data = [
            {
                'code': f.code,
                'filename': f.filename,
                'language': f.language
            }
            for f in files
        ]
        
        # Batch analyze
        results = await engine.batch_analyze(
            file_data,
            copilot_detected=files[0].copilot_detected if files else False
        )
        
        logger.info(f"✅ Batch analysis: {len(results)} files")
        
        return {
            "results": results,
            "total_files": len(files),
            "successful": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {e}")
        raise HTTPException(500, str(e))

@router.get("/policy/{owner}/{repo}")
async def get_policy(owner: str, repo: str):
    """Get policy for repository"""
    repo_name = f"{owner}/{repo}"
    policy = _policy_engine.get_policy(repo_name)
    
    return {
        "repository": repo_name,
        "mode": policy.mode.value,
        "allow_override": policy.allow_override,
        "override_approvers": policy.override_approvers,
        "thresholds": {
            "block_on_critical": policy.block_on_critical,
            "block_on_high": policy.block_on_high,
            "max_medium": policy.max_medium_violations,
            "max_low": policy.max_low_violations
        }
    }

@router.post("/policy/{owner}/{repo}")
async def set_policy(
    owner: str,
    repo: str,
    policy_config: PolicyConfigRequest
):
    """Set custom policy for repository"""
    repo_name = f"{owner}/{repo}"
    
    policy = PolicyConfig(
        mode=policy_config.mode,
        allow_override=policy_config.allow_override,
        override_approvers=policy_config.override_approvers,
        block_on_critical=policy_config.block_on_critical,
        block_on_high=policy_config.block_on_high,
        copilot_strict_mode=policy_config.copilot_strict_mode
    )
    
    _policy_engine.set_repo_policy(repo_name, policy)
    
    logger.info(f"📋 Policy updated: {repo_name} -> {policy.mode}")
    
    return {
        "repository": repo_name,
        "policy": policy.dict(),
        "message": "Policy updated successfully"
    }

@router.get("/scanners/status")
async def get_scanners_status():
    """Get status of all scanners"""
    engine = get_engine()
    
    return {
        "static_analyzers": {
            "python": {"bandit": engine.python.has_bandit},
            "javascript": {"available": True}
        },
        "secrets": {
            "detect_secrets": engine.secrets.has_detect_secrets,
            "patterns": len(engine.secrets.patterns),
            "entropy": True
        },
        "licenses": {
            "scancode": engine.licenses.has_scancode,
            "patterns": len(engine.licenses.license_patterns)
        },
        "ai": {
            "gemini": bool(engine.ai),
            "validation": bool(engine.ai)
        },
        "rules": {
            "available_packs": len(engine.rules.industry_packs)
        }
    }
