"""
Advanced Secrets Scanner
Integrates: detect-secrets, TruffleHog, custom patterns
"""
import re
import json
import logging
import subprocess
import tempfile
import os
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretsScanner:
    """
    Multi-engine secrets detection
    - detect-secrets (Yelp)
    - TruffleHog patterns
    - Custom high-entropy detection
    """
    
    def __init__(self):
        self.has_detect_secrets = self._check_detect_secrets()
        self.patterns = self._load_patterns()
        
    def _check_detect_secrets(self) -> bool:
        try:
            subprocess.run(['detect-secrets', '--version'], 
                         capture_output=True, timeout=5)
            logger.info("✅ detect-secrets available")
            return True
        except:
            logger.warning("⚠️  detect-secrets not available")
            return False
    
    def _load_patterns(self) -> List[Dict]:
        """Load comprehensive secret patterns"""
        return [
            # API Keys
            {
                'name': 'Generic API Key',
                'pattern': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']([a-z0-9_\-]{20,})["\']',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'hardcoded-api-key'
            },
            {
                'name': 'OpenAI API Key',
                'pattern': r'sk-[A-Za-z0-9]{48}',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'openai-key'
            },
            {
                'name': 'GitHub Token',
                'pattern': r'ghp_[A-Za-z0-9]{36}',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'github-token'
            },
            {
                'name': 'AWS Access Key',
                'pattern': r'AKIA[0-9A-Z]{16}',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'aws-key'
            },
            {
                'name': 'Slack Token',
                'pattern': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'slack-token'
            },
            {
                'name': 'Private Key',
                'pattern': r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'private-key'
            },
            # Passwords
            {
                'name': 'Hardcoded Password',
                'pattern': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\']{4,})["\']',
                'severity': 'critical',
                'cwe': 'CWE-798',
                'type': 'hardcoded-password'
            },
            # Tokens
            {
                'name': 'Generic Secret',
                'pattern': r'(?i)(secret[_-]?key|token)\s*[:=]\s*["\']([a-z0-9_\-]{16,})["\']',
                'severity': 'high',
                'cwe': 'CWE-798',
                'type': 'hardcoded-secret'
            },
            # Database URLs
            {
                'name': 'Database URL with Credentials',
                'pattern': r'(?i)(mysql|postgres|mongodb):\/\/[^:]+:[^@]+@',
                'severity': 'high',
                'cwe': 'CWE-798',
                'type': 'database-url'
            },
            # JWT
            {
                'name': 'JWT Token',
                'pattern': r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
                'severity': 'medium',
                'cwe': 'CWE-798',
                'type': 'jwt-token'
            },
        ]
    
    async def scan(self, code: str, filename: str) -> List[Dict]:
        """
        Comprehensive secrets scanning
        """
        results = []
        
        # Pattern-based detection
        results.extend(self._pattern_scan(code, filename))
        
        # detect-secrets if available
        if self.has_detect_secrets:
            results.extend(await self._detect_secrets_scan(code, filename))
        
        # High entropy detection
        results.extend(self._entropy_scan(code, filename))
        
        # Deduplicate
        results = self._dedupe(results)
        
        logger.info(f"🔐 Secrets scan: {len(results)} findings in {filename}")
        return results
    
    def _pattern_scan(self, code: str, filename: str) -> List[Dict]:
        """Pattern-based secret detection"""
        findings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern_def in self.patterns:
                matches = re.finditer(pattern_def['pattern'], line, re.IGNORECASE)
                
                for match in matches:
                    # Extract the secret value for masking
                    secret_value = match.group(0)
                    if len(match.groups()) >= 2:
                        secret_value = match.group(2)
                    
                    findings.append({
                        'type': pattern_def['type'],
                        'name': pattern_def['name'],
                        'severity': pattern_def['severity'],
                        'line': i,
                        'code_snippet': self._mask_secret(line),
                        'message': f"{pattern_def['name']} detected",
                        'cwe': pattern_def['cwe'],
                        'owasp': 'A07:2021',
                        'fix': 'Use environment variables or secrets manager',
                        'source': 'pattern-detector',
                        'confidence': 'high',
                        'secret_type': pattern_def['type'],
                        'masked_value': self._mask_secret(secret_value)
                    })
        
        return findings
    
    async def _detect_secrets_scan(self, code: str, filename: str) -> List[Dict]:
        """Use detect-secrets tool"""
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix=Path(filename).suffix,
                delete=False
            ) as f:
                f.write(code)
                temp_path = f.name
            
            # Run detect-secrets
            result = subprocess.run(
                ['detect-secrets', 'scan', '--json', temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(temp_path)
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                findings = []
                
                for file_path, secrets in data.get('results', {}).items():
                    for secret in secrets:
                        findings.append({
                            'type': secret.get('type', 'unknown-secret'),
                            'name': f"Secret: {secret.get('type')}",
                            'severity': 'critical',
                            'line': secret.get('line_number', 0),
                            'message': f"Potential secret detected: {secret.get('type')}",
                            'cwe': 'CWE-798',
                            'owasp': 'A07:2021',
                            'fix': 'Remove secret and use environment variables',
                            'source': 'detect-secrets',
                            'confidence': 'high'
                        })
                
                return findings
            
            return []
            
        except Exception as e:
            logger.error(f"detect-secrets failed: {e}")
            return []
    
    def _entropy_scan(self, code: str, filename: str) -> List[Dict]:
        """High-entropy string detection (potential secrets)"""
        import math
        from collections import Counter
        
        findings = []
        lines = code.split('\n')
        
        # Look for high-entropy strings in quotes
        pattern = r'["\']([a-zA-Z0-9+/=_-]{20,})["\']'
        
        for i, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            
            for match in matches:
                value = match.group(1)
                entropy = self._calculate_entropy(value)
                
                # High entropy suggests randomness (potential secret)
                if entropy > 4.5:  # Threshold for "high entropy"
                    findings.append({
                        'type': 'high-entropy-string',
                        'name': 'High Entropy String',
                        'severity': 'medium',
                        'line': i,
                        'code_snippet': self._mask_secret(line),
                        'message': f'High-entropy string detected (entropy: {entropy:.2f})',
                        'cwe': 'CWE-798',
                        'owasp': 'A07:2021',
                        'fix': 'If this is a secret, use environment variables',
                        'source': 'entropy-detector',
                        'confidence': 'medium',
                        'entropy_score': entropy
                    })
        
        return findings
    
    @staticmethod
    def _calculate_entropy(s: str) -> float:
        """Calculate Shannon entropy"""
        import math
        from collections import Counter
        
        if not s:
            return 0.0
        
        counts = Counter(s)
        probabilities = [count / len(s) for count in counts.values()]
        
        entropy = -sum(p * math.log2(p) for p in probabilities)
        return entropy
    
    @staticmethod
    def _mask_secret(text: str) -> str:
        """Mask potential secrets in text"""
        # Mask anything in quotes that looks like a secret
        masked = re.sub(
            r'(["\'])([a-zA-Z0-9+/=_-]{8,})\1',
            lambda m: f'{m.group(1)}{"*" * 8}{m.group(1)}',
            text
        )
        return masked
    
    def _dedupe(self, findings: List[Dict]) -> List[Dict]:
        """Remove duplicate findings"""
        seen = set()
        unique = []
        
        for f in findings:
            key = (f.get('type'), f.get('line'))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique


# Singleton instance
_secrets_scanner = None

def get_secrets_scanner() -> SecretsScanner:
    global _secrets_scanner
    if _secrets_scanner is None:
        _secrets_scanner = SecretsScanner()
    return _secrets_scanner
