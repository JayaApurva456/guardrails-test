"""
Production Gemini AI Analyzer
Uses chain-of-thought, few-shot learning, structured outputs
"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
import re

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Advanced AI security analyzer"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            'gemini-1.5-pro',
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        logger.info("✅ Gemini initialized")
    
    async def analyze_security(self, code: str, filename: str, language: str, context: Optional[Dict] = None) -> List[Dict]:
        """Deep AI security analysis"""
        try:
            # Build sophisticated prompt
            prompt = self._build_prompt(code, filename, language, context)
            
            # Call Gemini
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            # Parse and validate
            vulns = self._parse_response(response.text)
            
            # Enrich
            enriched = self._enrich(vulns, filename, language)
            
            logger.info(f"✅ AI found {len(enriched)} issues in {filename}")
            return enriched
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return []
    
    def _build_prompt(self, code: str, filename: str, language: str, context: Optional[Dict]) -> str:
        """Advanced prompt with chain-of-thought"""
        
        # Truncate if needed
        if len(code) > 6000:
            code = code[:3000] + "\n\n... [code truncated] ...\n\n" + code[-3000:]
        
        prompt = f"""You are a senior security engineer auditing code.

# ANALYSIS TASK
Perform deep security analysis on this {language} code.

# FILE CONTEXT
- File: {filename}
- Language: {language}
- Lines: {len(code.split(chr(10)))}
"""
        
        if context:
            if context.get('copilot_detected'):
                prompt += f"\n⚠️  AI-GENERATED CODE DETECTED - Apply extra scrutiny!\n"
            prompt += f"- Repository: {context.get('repository', 'N/A')}\n"
        
        prompt += f"""
# METHODOLOGY
Follow systematic approach:
1. Read code and identify security patterns
2. Analyze potential exploits (OWASP Top 10, CWE)
3. Consider real-world attack scenarios
4. Assess severity and impact
5. Provide concrete fixes with code examples

# CODE TO ANALYZE
```{language}
{code}
```

# PRIORITY VULNERABILITIES
Look for:
- 🔴 CRITICAL: SQL injection, command injection, auth bypass, secrets
- 🟠 HIGH: XSS, deserialization, path traversal, weak crypto
- 🟡 MEDIUM: Info disclosure, logging, insecure defaults
- 🔵 LOW: Code quality, performance

# OUTPUT FORMAT (JSON ONLY!)
[
  {{
    "type": "sql-injection",
    "severity": "critical",
    "line": 45,
    "code_snippet": "the vulnerable code",
    "vulnerability": "Clear explanation",
    "exploit_scenario": "How attacker exploits this",
    "impact": "Potential damage",
    "cwe_id": "CWE-89",
    "owasp": "A03:2021 - Injection",
    "fix": "Concrete code example showing fix",
    "confidence": "high"
  }}
]

CRITICAL RULES:
- Be thorough but practical
- Focus on REAL security issues
- Provide ACTIONABLE fixes with code
- Include line numbers
- Return ONLY valid JSON array
- Empty array [] if no issues

Begin analysis:"""
        
        return prompt
    
    def _parse_response(self, text: str) -> List[Dict]:
        """Parse and validate AI response"""
        try:
            # Clean text
            text = text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Find JSON array
            if not text.startswith('['):
                start = text.find('[')
                end = text.rfind(']')
                if start != -1 and end != -1:
                    text = text[start:end+1]
            
            # Parse
            vulns = json.loads(text)
            
            if not isinstance(vulns, list):
                vulns = [vulns] if isinstance(vulns, dict) else []
            
            # Validate
            valid = []
            for v in vulns:
                if isinstance(v, dict) and 'type' in v and 'severity' in v:
                    valid.append(v)
            
            return valid
            
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            return []
    
    def _enrich(self, vulns: List[Dict], filename: str, language: str) -> List[Dict]:
        """Add metadata"""
        enriched = []
        for v in vulns:
            enriched.append({
                **v,
                'filename': filename,
                'language': language,
                'source': 'gemini-ai',
                'severity': v.get('severity', 'medium').lower(),
                'confidence': v.get('confidence', 'medium').lower(),
                'line': int(v.get('line', 0)),
                'fix': v.get('fix') or 'Fix this security issue'
            })
        return enriched
    
    async def validate_findings(self, findings: List[Dict], code: str, language: str) -> List[Dict]:
        """AI validates static findings - reduces false positives"""
        if not findings:
            return []
        
        try:
            # Truncate
            code = code[:3000] if len(code) > 3000 else code
            
            prompt = f"""Validate these security findings - identify TRUE vs FALSE positives.

# FINDINGS TO VALIDATE
{json.dumps(findings, indent=2)}

# CODE CONTEXT
```{language}
{code}
```

# TASK
Return ONLY findings that are TRUE POSITIVES as JSON array.
Exclude false positives.

Return format (JSON only):
[... true positive findings only ...]

If all false positives, return: []

Validate now:"""
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            validated = self._parse_response(response.text)
            
            logger.info(f"✅ Validated: {len(validated)}/{len(findings)} true positives")
            return validated
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return findings  # Fail-safe
