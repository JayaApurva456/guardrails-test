"""
ULTIMATE Complete Hybrid Analysis Engine
Integrates ALL scanners for comprehensive analysis:
- Static analysis (Bandit, ESLint patterns)
- Secrets detection (patterns + entropy)
- License scanning (ScanCode patterns)
- Code duplication detection
- Coding standards enforcement
- Enterprise rules (YAML packs)
- AI deep analysis (Gemini)
- AI validation layer
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.analyzers.python_analyzer import PythonAnalyzer
from app.analyzers.javascript_analyzer import JavaScriptAnalyzer
from app.scanners.secrets_scanner import get_secrets_scanner
from app.scanners.license_scanner import get_license_scanner
from app.scanners.duplication_scanner import get_duplication_scanner
from app.scanners.coding_standards_scanner import get_coding_standards_scanner
from app.services.rule_engine import RuleEngine
from app.services.gemini_analyzer import GeminiAnalyzer


class UltimateHybridEngine:
    """
    Ultimate enterprise-grade analysis engine
    10-step pipeline with all detection methods
    """
    
    def __init__(
        self,
        gemini_key: Optional[str] = None,
        rules_dir: str = "/app/config"
    ):
        # Static analyzers
        self.python = PythonAnalyzer()
        self.javascript = JavaScriptAnalyzer()
        
        # Advanced scanners
        self.secrets = get_secrets_scanner()
        self.licenses = get_license_scanner()
        self.duplication = get_duplication_scanner()
        self.coding_standards = get_coding_standards_scanner()
        
        # Enterprise & AI
        self.rules = RuleEngine(rules_dir)
        self.ai = GeminiAnalyzer(gemini_key) if gemini_key else None
        
        print("🚀 Ultimate Hybrid Engine initialized with 10-step pipeline")
    
    async def analyze(
        self,
        code: str,
        filename: str,
        language: str,
        copilot_detected: bool = False,
        enabled_rule_packs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run complete 10-step analysis pipeline
        
        Steps:
        1. Static security analysis (Bandit/ESLint)
        2. Secrets detection (patterns + entropy)
        3. License & IP compliance
        4. Code duplication detection
        5. Coding standards enforcement
        6. Enterprise rule enforcement
        7. AI deep analysis (Gemini)
        8. AI validation (reduce false positives)
        9. Deduplication & merging
        10. Copilot scrutiny (severity boost)
        
        Returns:
            Complete analysis results with all findings
        """
        start_time = time.time()
        
        # Step 1-7: Run all scanners in parallel for speed
        results = await asyncio.gather(
            self._run_static_analysis(code, filename, language),
            self._run_secrets_detection(code, filename),
            self._run_license_scanning(code, filename),
            self._run_duplication_detection(code, filename),
            self._run_coding_standards(code, filename, language),
            self._run_enterprise_rules(code, filename, language, enabled_rule_packs),
            self._run_ai_analysis(code, filename, language, copilot_detected),
            return_exceptions=True  # Don't fail if one scanner fails
        )
        
        # Extract results (handle exceptions)
        static_findings = results[0] if not isinstance(results[0], Exception) else []
        secrets_findings = results[1] if not isinstance(results[1], Exception) else []
        license_findings = results[2] if not isinstance(results[2], Exception) else []
        duplication_findings = results[3] if not isinstance(results[3], Exception) else []
        standards_findings = results[4] if not isinstance(results[4], Exception) else []
        rules_findings = results[5] if not isinstance(results[5], Exception) else []
        ai_findings = results[6] if not isinstance(results[6], Exception) else []
        
        # Step 8: AI validation (reduce false positives from static)
        if self.ai and static_findings:
            try:
                validated_static = await self.ai.validate_findings(static_findings, code, language)
                static_findings = validated_static
            except Exception as e:
                print(f"AI validation failed: {e}")
        
        # Step 9: Merge all findings
        all_findings = []
        all_findings.extend(static_findings)
        all_findings.extend(secrets_findings)
        all_findings.extend(license_findings)
        all_findings.extend(duplication_findings)
        all_findings.extend(standards_findings)
        all_findings.extend(rules_findings)
        all_findings.extend(ai_findings)
        
        # Deduplicate findings
        all_findings = self._deduplicate_findings(all_findings)
        
        # Step 10: Apply Copilot scrutiny (stricter for AI code)
        if copilot_detected:
            all_findings = self._apply_copilot_scrutiny(all_findings)
        
        duration = time.time() - start_time
        
        # Build comprehensive result
        result = {
            'violations': all_findings,
            'total_count': len(all_findings),
            'by_severity': self._count_by_severity(all_findings),
            'by_source': self._count_by_source(all_findings),
            'by_type': self._count_by_type(all_findings),
            'duration': duration,
            'copilot_detected': copilot_detected,
            'language': language,
            'filename': filename,
            'pipeline_steps': {
                'static_analysis': len(static_findings),
                'secrets_detection': len(secrets_findings),
                'license_scanning': len(license_findings),
                'duplication_detection': len(duplication_findings),
                'coding_standards': len(standards_findings),
                'enterprise_rules': len(rules_findings),
                'ai_analysis': len(ai_findings)
            }
        }
        
        return result
    
    async def batch_analyze(
        self,
        files: List[Dict[str, str]],
        copilot_detected: bool = False,
        enabled_rule_packs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze multiple files in parallel"""
        tasks = [
            self.analyze(
                code=file['code'],
                filename=file['filename'],
                language=file['language'],
                copilot_detected=copilot_detected,
                enabled_rule_packs=enabled_rule_packs
            )
            for file in files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        all_violations = []
        total_duration = 0
        
        for result in results:
            if not isinstance(result, Exception):
                all_violations.extend(result['violations'])
                total_duration += result['duration']
        
        return {
            'violations': all_violations,
            'total_count': len(all_violations),
            'by_severity': self._count_by_severity(all_violations),
            'by_source': self._count_by_source(all_violations),
            'files_analyzed': len([r for r in results if not isinstance(r, Exception)]),
            'total_duration': total_duration
        }
    
    # Individual scanner runners
    
    async def _run_static_analysis(self, code: str, filename: str, language: str) -> List[Dict[str, Any]]:
        """Run static security analysis"""
        if language == 'python':
            return await self.python.analyze(code, filename)
        elif language in ['javascript', 'typescript']:
            return await self.javascript.analyze(code, filename)
        return []
    
    async def _run_secrets_detection(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Run secrets detection"""
        return await self.secrets.scan(code, filename)
    
    async def _run_license_scanning(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Run license compliance scanning"""
        return await self.licenses.scan(code, filename)
    
    async def _run_duplication_detection(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Run code duplication detection"""
        return await self.duplication.scan(code, filename)
    
    async def _run_coding_standards(self, code: str, filename: str, language: str) -> List[Dict[str, Any]]:
        """Run coding standards enforcement"""
        return await self.coding_standards.scan(code, filename, language)
    
    async def _run_enterprise_rules(
        self,
        code: str,
        filename: str,
        language: str,
        enabled_packs: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Run enterprise rule packs"""
        if not enabled_packs:
            return []
        
        all_findings = []
        for pack_name in enabled_packs:
            findings = await self.rules.check_rules(code, filename, language, pack_name)
            all_findings.extend(findings)
        
        return all_findings
    
    async def _run_ai_analysis(
        self,
        code: str,
        filename: str,
        language: str,
        copilot_detected: bool
    ) -> List[Dict[str, Any]]:
        """Run AI-powered deep analysis"""
        if not self.ai:
            return []
        
        try:
            findings = await self.ai.analyze_security(code, filename, language)
            return findings
        except Exception as e:
            print(f"AI analysis failed: {e}")
            return []
    
    # Helper methods
    
    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate findings"""
        seen = set()
        unique_findings = []
        
        for finding in findings:
            # Create key from type, line, and severity
            key = (
                finding.get('type', ''),
                finding.get('line', 0),
                finding.get('severity', ''),
                finding.get('message', '')[:50]  # First 50 chars of message
            )
            
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)
        
        return unique_findings
    
    def _apply_copilot_scrutiny(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply stricter scrutiny to AI-generated code"""
        for finding in findings:
            # Add Copilot warning flag
            finding['copilot_warning'] = True
            
            # Upgrade severity for certain violation types
            if finding.get('type') in [
                'weak-crypto', 'insecure-deserialization', 'command-injection',
                'sql-injection', 'xss'
            ]:
                original_severity = finding.get('severity', 'low')
                if original_severity == 'medium':
                    finding['severity'] = 'high'
                    finding['copilot_adjusted'] = True
                    finding['message'] = finding.get('message', '') + ' [Severity increased: AI-generated code]'
                elif original_severity == 'low':
                    finding['severity'] = 'medium'
                    finding['copilot_adjusted'] = True
                    finding['message'] = finding.get('message', '') + ' [Severity increased: AI-generated code]'
        
        return findings
    
    def _count_by_severity(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by severity"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for finding in findings:
            severity = finding.get('severity', 'low')
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def _count_by_source(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by source"""
        counts = defaultdict(int)
        for finding in findings:
            source = finding.get('source', 'unknown')
            counts[source] += 1
        return dict(counts)
    
    def _count_by_type(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by type"""
        counts = defaultdict(int)
        for finding in findings:
            vtype = finding.get('type', 'unknown')
            counts[vtype] += 1
        return dict(counts)


def create_ultimate_engine(gemini_key: Optional[str] = None, rules_dir: str = "/app/config") -> UltimateHybridEngine:
    """Factory function to create ultimate hybrid engine"""
    return UltimateHybridEngine(gemini_key=gemini_key, rules_dir=rules_dir)
