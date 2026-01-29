"""
REAL Hybrid Analysis Engine
Combines static + AI with validation
"""
import logging
from typing import List, Dict, Any
from app.analyzers.python_analyzer import PythonAnalyzer
from app.analyzers.javascript_analyzer import JavaScriptAnalyzer
from app.services.gemini_analyzer import GeminiAnalyzer

logger = logging.getLogger(__name__)

class HybridAnalysisEngine:
    """Production hybrid analyzer"""
    
    def __init__(self, gemini_key: str):
        self.python = PythonAnalyzer()
        self.javascript = JavaScriptAnalyzer()
        self.ai = GeminiAnalyzer(gemini_key) if gemini_key else None
        logger.info(f"🔬 Hybrid engine ready (AI: {bool(self.ai)})")
    
    async def analyze(self, code: str, filename: str, language: str, copilot_detected: bool = False) -> List[Dict]:
        """
        Comprehensive hybrid analysis:
        1. Run static analyzers
        2. Run AI analysis
        3. AI validates static findings
        4. Merge and deduplicate
        5. Apply Copilot scrutiny if needed
        """
        try:
            logger.info(f"🔍 Analyzing {filename} ({language})")
            
            # Step 1: Static analysis
            static = await self._run_static(code, filename, language)
            logger.info(f"  Static: {len(static)} findings")
            
            # Step 2: AI analysis
            ai_findings = []
            if self.ai:
                context = {'copilot_detected': copilot_detected}
                ai_findings = await self.ai.analyze_security(code, filename, language, context)
                logger.info(f"  AI: {len(ai_findings)} findings")
                
                # Step 3: AI validates static (KEY FEATURE!)
                if static:
                    validated = await self.ai.validate_findings(static, code, language)
                    logger.info(f"  Validated: {len(validated)}/{len(static)}")
                    static = validated
            
            # Step 4: Merge
            all_findings = self._merge(static, ai_findings)
            logger.info(f"  Merged: {len(all_findings)} total")
            
            # Step 5: Copilot scrutiny
            if copilot_detected and all_findings:
                all_findings = self._copilot_scrutiny(all_findings)
                logger.info(f"  Applied Copilot scrutiny")
            
            logger.info(f"✅ Analysis complete: {len(all_findings)} issues")
            return all_findings
            
        except Exception as e:
            logger.error(f"❌ Hybrid analysis failed: {e}", exc_info=True)
            return []
    
    async def _run_static(self, code: str, filename: str, language: str) -> List[Dict]:
        """Run appropriate static analyzer"""
        if language == 'python':
            return await self.python.analyze(code, filename)
        elif language in ['javascript', 'typescript', 'jsx', 'tsx']:
            return await self.javascript.analyze(code, filename)
        return []
    
    def _merge(self, static: List[Dict], ai: List[Dict]) -> List[Dict]:
        """Merge and deduplicate findings"""
        all_findings = []
        seen = set()
        
        for finding in static + ai:
            key = f"{finding.get('line')}:{finding.get('type')}:{finding.get('message', '')[:30]}"
            if key not in seen:
                seen.add(key)
                all_findings.append(finding)
        
        return all_findings
    
    def _copilot_scrutiny(self, findings: List[Dict]) -> List[Dict]:
        """Increase severity for AI-generated code"""
        for f in findings:
            if f.get('severity') == 'medium':
                f['severity'] = 'high'
                f['copilot_adjusted'] = True
                f['message'] += ' [Severity increased for AI-generated code]'
        return findings
