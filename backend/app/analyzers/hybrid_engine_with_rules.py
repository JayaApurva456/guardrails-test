"""
Enhanced Hybrid Engine with Enterprise Rule Packs
Combines static + AI + enterprise compliance rules
"""
import logging
from typing import List, Dict, Any, Optional
from app.analyzers.python_analyzer import PythonAnalyzer
from app.analyzers.javascript_analyzer import JavaScriptAnalyzer
from app.services.gemini_analyzer import GeminiAnalyzer
from app.services.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class HybridAnalysisEngineWithRules:
    """
    Production hybrid analyzer with enterprise rule packs
    
    Analysis Pipeline:
    1. Static analyzers (Bandit, ESLint patterns)
    2. Enterprise rule packs (PCI-DSS, HIPAA, FedRAMP, Telecom)
    3. AI analysis (Gemini)
    4. AI validates all findings
    5. Merge and deduplicate
    6. Apply Copilot scrutiny if detected
    """
    
    def __init__(self, gemini_key: str, rules_dir: str = "rules"):
        self.python = PythonAnalyzer()
        self.javascript = JavaScriptAnalyzer()
        self.ai = GeminiAnalyzer(gemini_key) if gemini_key else None
        self.rule_engine = RuleEngine(rules_dir)
        
        logger.info(f"🔬 Hybrid engine with rule packs ready")
        logger.info(f"   Rule packs: {list(self.rule_engine.rule_packs.keys())}")
    
    async def analyze(
        self, 
        code: str, 
        filename: str, 
        language: str, 
        copilot_detected: bool = False,
        repository: Optional[str] = None
    ) -> List[Dict]:
        """
        Comprehensive hybrid analysis with enterprise rules
        """
        try:
            logger.info(f"🔍 Analyzing {filename} ({language})")
            all_findings = []
            
            # Step 1: Static analysis
            static = await self._run_static(code, filename, language)
            logger.info(f"  Static: {len(static)} findings")
            all_findings.extend(static)
            
            # Step 2: Enterprise rule packs (KEY DIFFERENTIATOR!)
            if repository:
                owner, repo = repository.split('/')[-2:]
                enabled_packs = self.rule_engine.get_enabled_packs(owner, repo)
            else:
                enabled_packs = ['security-rules']  # Default
            
            rule_violations = self.rule_engine.analyze_code(code, filename, enabled_packs)
            logger.info(f"  Rules ({', '.join(enabled_packs)}): {len(rule_violations)} violations")
            all_findings.extend(rule_violations)
            
            # Step 3: AI analysis
            ai_findings = []
            if self.ai:
                context = {'copilot_detected': copilot_detected, 'repository': repository}
                ai_findings = await self.ai.analyze_security(code, filename, language, context)
                logger.info(f"  AI: {len(ai_findings)} findings")
                
                # Step 4: AI validates ALL findings (static + rules)
                if all_findings:
                    validated = await self.ai.validate_findings(all_findings, code, language)
                    logger.info(f"  Validated: {len(validated)}/{len(all_findings)}")
                    all_findings = validated
                
                # Add AI-only findings
                all_findings.extend(ai_findings)
            
            # Step 5: Merge and deduplicate
            all_findings = self._merge(all_findings)
            logger.info(f"  Merged: {len(all_findings)} unique findings")
            
            # Step 6: Copilot scrutiny
            if copilot_detected and all_findings:
                all_findings = self._copilot_scrutiny(all_findings)
                logger.info(f"  Applied Copilot scrutiny")
            
            logger.info(f"✅ Analysis complete: {len(all_findings)} total issues")
            return all_findings
            
        except Exception as e:
            logger.error(f"❌ Hybrid analysis failed: {e}", exc_info=True)
            return []
    
    async def _run_static(self, code, filename, language):
        """Run static analyzers"""
        if language == 'python':
            return await self.python.analyze(code, filename)
        elif language in ['javascript', 'typescript', 'jsx', 'tsx']:
            return await self.javascript.analyze(code, filename)
        return []
    
    def _merge(self, findings):
        """Deduplicate findings"""
        seen = set()
        unique = []
        
        for f in findings:
            key = f"{f.get('line')}:{f.get('type')}:{f.get('message', '')[:30]}"
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique
    
    def _copilot_scrutiny(self, findings):
        """Increase severity for AI-generated code"""
        for f in findings:
            if f.get('severity') == 'medium':
                f['severity'] = 'high'
                f['copilot_adjusted'] = True
                f['message'] += ' [Severity increased for AI-generated code]'
        return findings
