"""
Policy-Based Enforcement Engine
Implements: Advisory, Warning, Blocking modes with override support
"""
import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EnforcementMode(str, Enum):
    """Enforcement levels"""
    ADVISORY = "advisory"      # Comment only, no blocking
    WARNING = "warning"        # Comment + warning status
    BLOCKING = "blocking"      # Block merge until fixed or overridden


class PolicyConfig(BaseModel):
    """Policy configuration"""
    mode: EnforcementMode = EnforcementMode.WARNING
    allow_override: bool = False
    override_approvers: List[str] = []
    
    # Severity thresholds
    block_on_critical: bool = True
    block_on_high: bool = False
    max_medium_violations: int = 10
    max_low_violations: int = 50
    
    # Special rules
    copilot_strict_mode: bool = True
    require_license_check: bool = True
    require_security_review_above: Optional[int] = 5  # violations count


class PolicyEngine:
    """
    Determines enforcement actions based on policy and violations
    """
    
    def __init__(self, default_policy: Optional[PolicyConfig] = None):
        self.default_policy = default_policy or PolicyConfig()
        self.repo_policies: Dict[str, PolicyConfig] = {}
        
    def set_repo_policy(self, repo_name: str, policy: PolicyConfig):
        """Set custom policy for specific repository"""
        self.repo_policies[repo_name] = policy
        logger.info(f"📋 Policy set for {repo_name}: {policy.mode}")
    
    def get_policy(
        self, 
        repo_name: str,
        is_copilot_generated: bool = False
    ) -> PolicyConfig:
        """
        Get applicable policy for repository
        
        Args:
            repo_name: Repository name
            is_copilot_generated: Whether code is AI-generated
            
        Returns:
            Applicable PolicyConfig
        """
        # Get repo-specific or default
        policy = self.repo_policies.get(repo_name, self.default_policy)
        
        # Apply stricter rules for Copilot code if enabled
        if is_copilot_generated and policy.copilot_strict_mode:
            policy = self._apply_copilot_strictness(policy)
        
        return policy
    
    def _apply_copilot_strictness(self, policy: PolicyConfig) -> PolicyConfig:
        """Make policy stricter for AI-generated code"""
        strict_policy = policy.copy()
        
        # Upgrade to blocking if not already
        if policy.mode == EnforcementMode.ADVISORY:
            strict_policy.mode = EnforcementMode.WARNING
        elif policy.mode == EnforcementMode.WARNING:
            strict_policy.mode = EnforcementMode.BLOCKING
        
        # Stricter thresholds
        strict_policy.block_on_critical = True
        strict_policy.block_on_high = True
        strict_policy.max_medium_violations = max(5, policy.max_medium_violations // 2)
        
        logger.info("🤖 Applied Copilot strict mode")
        return strict_policy
    
    def determine_action(
        self, 
        policy: PolicyConfig,
        violations: List[Dict]
    ) -> Dict[str, Any]:
        """
        Determine enforcement action based on policy and violations
        
        Args:
            policy: Applicable policy
            violations: List of violations found
            
        Returns:
            Action to take with details
        """
        # Count by severity
        severity_counts = self._count_by_severity(violations)
        
        # Determine if should block
        should_block = self._should_block(policy, severity_counts)
        
        # Build action
        action = {
            'mode': policy.mode.value,
            'should_block': should_block,
            'allow_override': policy.allow_override,
            'override_approvers': policy.override_approvers,
            'severity_counts': severity_counts,
            'total_violations': len(violations),
            'reason': self._get_block_reason(policy, severity_counts)
        }
        
        # Determine GitHub status
        action['github_status'] = self._get_github_status(
            policy.mode, 
            should_block
        )
        
        logger.info(f"📊 Policy decision: {action['github_status']} "
                   f"({action['total_violations']} violations)")
        
        return action
    
    def _count_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by severity"""
        counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for v in violations:
            severity = v.get('severity', 'medium').lower()
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def _should_block(
        self,
        policy: PolicyConfig,
        severity_counts: Dict[str, int]
    ) -> bool:
        """Determine if violations should block merge"""
        
        # Check critical
        if policy.block_on_critical and severity_counts['critical'] > 0:
            return True
        
        # Check high
        if policy.block_on_high and severity_counts['high'] > 0:
            return True
        
        # Check medium threshold
        if severity_counts['medium'] > policy.max_medium_violations:
            return True
        
        # Check low threshold
        if severity_counts['low'] > policy.max_low_violations:
            return True
        
        return False
    
    def _get_block_reason(
        self,
        policy: PolicyConfig,
        severity_counts: Dict[str, int]
    ) -> str:
        """Get human-readable reason for blocking"""
        reasons = []
        
        if policy.block_on_critical and severity_counts['critical'] > 0:
            reasons.append(f"{severity_counts['critical']} critical violation(s)")
        
        if policy.block_on_high and severity_counts['high'] > 0:
            reasons.append(f"{severity_counts['high']} high severity violation(s)")
        
        if severity_counts['medium'] > policy.max_medium_violations:
            reasons.append(
                f"{severity_counts['medium']} medium violations "
                f"(max: {policy.max_medium_violations})"
            )
        
        if severity_counts['low'] > policy.max_low_violations:
            reasons.append(
                f"{severity_counts['low']} low violations "
                f"(max: {policy.max_low_violations})"
            )
        
        return '; '.join(reasons) if reasons else 'No blocking violations'
    
    def _get_github_status(
        self,
        mode: EnforcementMode,
        should_block: bool
    ) -> Dict[str, str]:
        """Get GitHub status check details"""
        
        if mode == EnforcementMode.ADVISORY:
            return {
                'state': 'success',
                'context': 'guardrails/advisory',
                'description': 'Advisory scan complete (non-blocking)'
            }
        
        elif mode == EnforcementMode.WARNING:
            return {
                'state': 'success',
                'context': 'guardrails/warning',
                'description': 'Warnings found but not blocking'
            }
        
        elif mode == EnforcementMode.BLOCKING:
            if should_block:
                return {
                    'state': 'failure',
                    'context': 'guardrails/required',
                    'description': 'Blocking violations found - fix or request override'
                }
            else:
                return {
                    'state': 'success',
                    'context': 'guardrails/required',
                    'description': 'No blocking violations'
                }
        
        return {
            'state': 'success',
            'context': 'guardrails',
            'description': 'Scan complete'
        }
    
    def check_override_approval(
        self,
        policy: PolicyConfig,
        approver: str
    ) -> bool:
        """Check if user can approve override"""
        if not policy.allow_override:
            return False
        
        return approver in policy.override_approvers
    
    def get_enforcement_summary(
        self,
        action: Dict[str, Any]
    ) -> str:
        """Get human-readable summary of enforcement action"""
        
        summary = f"""
## 🛡️ Policy Enforcement Summary

**Mode:** {action['mode'].upper()}
**Status:** {'🔴 BLOCKING' if action['should_block'] else '✅ PASSING'}

### Violations Found
- 🔴 Critical: {action['severity_counts']['critical']}
- 🟠 High: {action['severity_counts']['high']}
- 🟡 Medium: {action['severity_counts']['medium']}
- 🟢 Low: {action['severity_counts']['low']}
- ℹ️  Info: {action['severity_counts']['info']}

**Total:** {action['total_violations']}

"""
        
        if action['should_block']:
            summary += f"**Reason:** {action['reason']}\n\n"
            
            if action['allow_override']:
                approvers = ', '.join(f'@{a}' for a in action['override_approvers'])
                summary += f"**Override Available:** {approvers} can approve\n"
        
        return summary


# Singleton
_policy_engine = None

def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
