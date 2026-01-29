"""
Real Python Analyzer with Bandit + Pattern Matching
"""
import subprocess
import json
import tempfile
import os
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PythonAnalyzer:
    """Production Python security analyzer"""
    
    def __init__(self):
        self.has_bandit = self._check_bandit()
        self.patterns = [
            {
                'regex': r'eval\s*\(',
                'type': 'eval-usage',
                'severity': 'high',
                'message': 'eval() is dangerous',
                'cwe': 'CWE-95',
                'fix': 'Use ast.literal_eval() or json.loads()'
            },
            {
                'regex': r'exec\s*\(',
                'type': 'exec-usage',
                'severity': 'high',
                'message': 'exec() allows arbitrary code execution',
                'cwe': 'CWE-95',
                'fix': 'Remove exec() and refactor'
            },
            {
                'regex': r'pickle\.load',
                'type': 'insecure-deserialization',
                'severity': 'medium',
                'message': 'pickle is unsafe for untrusted data',
                'cwe': 'CWE-502',
                'fix': 'Use JSON for serialization'
            },
            {
                'regex': r'hashlib\.(md5|sha1)\s*\(',
                'type': 'weak-crypto',
                'severity': 'medium',
                'message': 'Weak cryptographic hash',
                'cwe': 'CWE-327',
                'fix': 'Use hashlib.sha256() or sha512()'
            },
            {
                'regex': r'(?:password|api[_-]?key|secret|token)\s*=\s*["\'][^\'"]{8,}["\']',
                'type': 'hardcoded-secret',
                'severity': 'critical',
                'message': 'Hardcoded secret detected',
                'cwe': 'CWE-798',
                'fix': 'Use environment variables'
            },
            {
                'regex': r'os\.system\s*\(',
                'type': 'command-injection',
                'severity': 'high',
                'message': 'os.system() enables command injection',
                'cwe': 'CWE-78',
                'fix': 'Use subprocess.run() with shell=False'
            },
            {
                'regex': r'subprocess\.(call|run|Popen).*shell\s*=\s*True',
                'type': 'command-injection',
                'severity': 'high',
                'message': 'shell=True enables command injection',
                'cwe': 'CWE-78',
                'fix': 'Set shell=False and use list arguments'
            },
        ]
    
    def _check_bandit(self) -> bool:
        try:
            subprocess.run(['bandit', '--version'], capture_output=True, timeout=5)
            logger.info("✅ Bandit available")
            return True
        except:
            logger.warning("⚠️  Bandit not available")
            return False
    
    async def analyze(self, code: str, filename: str) -> List[Dict]:
        """Analyze Python code"""
        results = []
        
        # Bandit if available
        if self.has_bandit:
            results.extend(await self._run_bandit(code))
        
        # Pattern matching
        results.extend(self._pattern_check(code))
        
        # Dedupe
        results = self._dedupe(results)
        
        logger.info(f"🐍 Python: {len(results)} issues")
        return results
    
    async def _run_bandit(self, code: str) -> List[Dict]:
        """Run Bandit scanner"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp = f.name
            
            result = subprocess.run(
                ['bandit', '-f', 'json', '-q', temp],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(temp)
            
            if result.stdout:
                data = json.loads(result.stdout)
                findings = []
                for issue in data.get('results', []):
                    findings.append({
                        'type': issue.get('test_id'),
                        'severity': issue.get('issue_severity', 'MEDIUM').lower(),
                        'line': issue.get('line_number', 0),
                        'message': issue.get('issue_text'),
                        'cwe': issue.get('cwe', {}).get('id', ''),
                        'source': 'bandit',
                        'confidence': issue.get('issue_confidence', 'MEDIUM').lower()
                    })
                return findings
            
            return []
        except Exception as e:
            logger.error(f"Bandit failed: {e}")
            return []
    
    def _pattern_check(self, code: str) -> List[Dict]:
        """Pattern-based checks"""
        findings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.patterns:
                if re.search(pattern['regex'], line, re.IGNORECASE):
                    findings.append({
                        'type': pattern['type'],
                        'severity': pattern['severity'],
                        'line': i,
                        'message': pattern['message'],
                        'cwe': pattern['cwe'],
                        'fix': pattern['fix'],
                        'source': 'pattern-matcher',
                        'confidence': 'medium'
                    })
        
        return findings
    
    def _dedupe(self, findings: List[Dict]) -> List[Dict]:
        """Remove duplicates"""
        seen = set()
        unique = []
        for f in findings:
            key = (f.get('type'), f.get('line'))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
