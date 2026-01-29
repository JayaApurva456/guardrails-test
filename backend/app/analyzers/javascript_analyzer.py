"""
JavaScript/TypeScript Security Analyzer
"""
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class JavaScriptAnalyzer:
    """JS/TS security analyzer"""
    
    def __init__(self):
        self.patterns = [
            {
                'regex': r'eval\s*\(',
                'type': 'eval-usage',
                'severity': 'high',
                'message': 'eval() is dangerous',
                'cwe': 'CWE-95',
                'fix': 'Remove eval() and use safe alternatives'
            },
            {
                'regex': r'innerHTML\s*=',
                'type': 'xss',
                'severity': 'medium',
                'message': 'innerHTML can cause XSS',
                'cwe': 'CWE-79',
                'fix': 'Use textContent or sanitize HTML'
            },
            {
                'regex': r'dangerouslySetInnerHTML',
                'type': 'xss',
                'severity': 'high',
                'message': 'dangerouslySetInnerHTML XSS risk',
                'cwe': 'CWE-79',
                'fix': 'Sanitize HTML or use safe alternatives'
            },
            {
                'regex': r'document\.write',
                'type': 'xss',
                'severity': 'medium',
                'message': 'document.write() can be exploited',
                'cwe': 'CWE-79',
                'fix': 'Use DOM methods instead'
            },
            {
                'regex': r'(?:api[_-]?key|password|token)\s*[:=]\s*["\'][^\'"]{8,}["\']',
                'type': 'hardcoded-secret',
                'severity': 'critical',
                'message': 'Hardcoded secret',
                'cwe': 'CWE-798',
                'fix': 'Use environment variables'
            },
            {
                'regex': r'crypto\.createHash\s*\(\s*["\']md5["\']',
                'type': 'weak-crypto',
                'severity': 'medium',
                'message': 'MD5 is weak',
                'cwe': 'CWE-327',
                'fix': 'Use SHA-256 or stronger'
            },
        ]
    
    async def analyze(self, code: str, filename: str) -> List[Dict]:
        """Analyze JS/TS code"""
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
                        'source': 'js-patterns',
                        'confidence': 'high'
                    })
        
        logger.info(f"📜 JavaScript: {len(findings)} issues")
        return findings
