"""
License & IP Compliance Scanner
Integrates: ScanCode Toolkit, license compatibility checking
"""
import re
import json
import logging
import subprocess
import tempfile
import os
from typing import List, Dict, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class LicenseScanner:
    """
    Comprehensive license detection and compliance checking
    - License text detection
    - Package license checking
    - Compatibility analysis
    - IP risk flagging
    """
    
    def __init__(self):
        self.has_scancode = self._check_scancode()
        self.license_patterns = self._load_license_patterns()
        self.restricted_licenses = self._load_restricted_licenses()
        
    def _check_scancode(self) -> bool:
        try:
            subprocess.run(['scancode', '--version'],
                         capture_output=True, timeout=5)
            logger.info("✅ ScanCode available")
            return True
        except:
            logger.warning("⚠️  ScanCode not available")
            return False
    
    def _load_license_patterns(self) -> List[Dict]:
        """Common license header patterns"""
        return [
            {
                'name': 'GPL-3.0',
                'pattern': r'GNU\s+GENERAL\s+PUBLIC\s+LICENSE\s+Version\s+3',
                'risk': 'high',
                'copyleft': True,
                'commercial_friendly': False
            },
            {
                'name': 'GPL-2.0',
                'pattern': r'GNU\s+GENERAL\s+PUBLIC\s+LICENSE\s+Version\s+2',
                'risk': 'high',
                'copyleft': True,
                'commercial_friendly': False
            },
            {
                'name': 'AGPL-3.0',
                'pattern': r'GNU\s+AFFERO\s+GENERAL\s+PUBLIC\s+LICENSE',
                'risk': 'critical',
                'copyleft': True,
                'commercial_friendly': False
            },
            {
                'name': 'MIT',
                'pattern': r'MIT\s+License|Permission\s+is\s+hereby\s+granted',
                'risk': 'low',
                'copyleft': False,
                'commercial_friendly': True
            },
            {
                'name': 'Apache-2.0',
                'pattern': r'Apache\s+License\s+Version\s+2\.0',
                'risk': 'low',
                'copyleft': False,
                'commercial_friendly': True
            },
            {
                'name': 'BSD-3-Clause',
                'pattern': r'BSD\s+3-Clause|Redistribution\s+and\s+use\s+in\s+source',
                'risk': 'low',
                'copyleft': False,
                'commercial_friendly': True
            },
            {
                'name': 'SSPL',
                'pattern': r'Server\s+Side\s+Public\s+License',
                'risk': 'critical',
                'copyleft': True,
                'commercial_friendly': False
            },
            {
                'name': 'Commons Clause',
                'pattern': r'Commons\s+Clause',
                'risk': 'critical',
                'copyleft': False,
                'commercial_friendly': False
            },
            {
                'name': 'Proprietary',
                'pattern': r'All\s+rights\s+reserved|PROPRIETARY',
                'risk': 'high',
                'copyleft': False,
                'commercial_friendly': False
            },
        ]
    
    def _load_restricted_licenses(self) -> Set[str]:
        """Licenses that trigger IP risk warnings"""
        return {
            'GPL-3.0', 'GPL-2.0', 'AGPL-3.0',
            'SSPL-1.0', 'SSPL',
            'Commons Clause',
            'BUSL-1.1',
            'Proprietary',
            'All Rights Reserved'
        }
    
    async def scan(self, code: str, filename: str) -> List[Dict]:
        """
        Comprehensive license scanning
        """
        results = []
        
        # Pattern-based detection
        results.extend(self._pattern_scan(code, filename))
        
        # ScanCode if available
        if self.has_scancode:
            results.extend(await self._scancode_scan(code, filename))
        
        # Check for copyright statements
        results.extend(self._copyright_scan(code, filename))
        
        # Deduplicate
        results = self._dedupe(results)
        
        logger.info(f"📜 License scan: {len(results)} findings in {filename}")
        return results
    
    def _pattern_scan(self, code: str, filename: str) -> List[Dict]:
        """Pattern-based license detection"""
        findings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for lic in self.license_patterns:
                if re.search(lic['pattern'], line, re.IGNORECASE):
                    severity = self._get_severity(lic)
                    
                    findings.append({
                        'type': 'license-detected',
                        'name': f"License: {lic['name']}",
                        'severity': severity,
                        'line': i,
                        'code_snippet': line.strip(),
                        'message': f"{lic['name']} license detected",
                        'license_name': lic['name'],
                        'risk_level': lic['risk'],
                        'copyleft': lic['copyleft'],
                        'commercial_friendly': lic['commercial_friendly'],
                        'fix': self._get_license_fix(lic),
                        'source': 'license-pattern',
                        'confidence': 'high'
                    })
        
        return findings
    
    async def _scancode_scan(self, code: str, filename: str) -> List[Dict]:
        """Use ScanCode Toolkit"""
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=Path(filename).suffix,
                delete=False
            ) as f:
                f.write(code)
                temp_path = f.name
            
            # Run ScanCode
            result = subprocess.run(
                ['scancode', '--license', '--json-pp', '-', temp_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            os.unlink(temp_path)
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                findings = []
                
                for file_data in data.get('files', []):
                    for license_data in file_data.get('licenses', []):
                        license_key = license_data.get('key', 'unknown')
                        
                        findings.append({
                            'type': 'license-detected',
                            'name': f"License: {license_key}",
                            'severity': self._assess_license_risk(license_key),
                            'line': license_data.get('start_line', 0),
                            'message': f"License detected by ScanCode: {license_key}",
                            'license_name': license_key,
                            'score': license_data.get('score', 0),
                            'matched_text': license_data.get('matched_text', ''),
                            'source': 'scancode',
                            'confidence': 'very-high'
                        })
                
                return findings
            
            return []
            
        except Exception as e:
            logger.error(f"ScanCode failed: {e}")
            return []
    
    def _copyright_scan(self, code: str, filename: str) -> List[Dict]:
        """Detect copyright statements"""
        findings = []
        lines = code.split('\n')
        
        copyright_pattern = r'Copyright\s+(?:\(c\)\s*)?(\d{4}(?:-\d{4})?)\s+(.+)'
        
        for i, line in enumerate(lines, 1):
            match = re.search(copyright_pattern, line, re.IGNORECASE)
            if match:
                year = match.group(1)
                holder = match.group(2).strip()
                
                findings.append({
                    'type': 'copyright-notice',
                    'name': 'Copyright Notice',
                    'severity': 'info',
                    'line': i,
                    'code_snippet': line.strip(),
                    'message': f'Copyright notice found: {holder}',
                    'copyright_year': year,
                    'copyright_holder': holder,
                    'source': 'copyright-detector',
                    'confidence': 'high'
                })
        
        return findings
    
    def check_license_compatibility(
        self, 
        project_license: str,
        dependency_licenses: List[str]
    ) -> Dict[str, Any]:
        """
        Check if dependency licenses are compatible with project license
        """
        incompatibilities = []
        
        # Copyleft licenses require compatible licensing
        if project_license in ['MIT', 'Apache-2.0', 'BSD-3-Clause']:
            # Permissive licenses can't include strong copyleft
            for dep_lic in dependency_licenses:
                if dep_lic in ['GPL-3.0', 'AGPL-3.0']:
                    incompatibilities.append({
                        'dependency_license': dep_lic,
                        'reason': f'Copyleft {dep_lic} incompatible with permissive {project_license}',
                        'severity': 'high'
                    })
        
        return {
            'compatible': len(incompatibilities) == 0,
            'incompatibilities': incompatibilities,
            'warnings': len(incompatibilities)
        }
    
    def _get_severity(self, license_def: Dict) -> str:
        """Determine severity based on license risk"""
        risk_map = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        return risk_map.get(license_def['risk'], 'medium')
    
    def _assess_license_risk(self, license_key: str) -> str:
        """Assess risk of a license"""
        if any(restricted in license_key.upper() 
               for restricted in ['GPL', 'AGPL', 'SSPL']):
            return 'high'
        elif 'PROPRIETARY' in license_key.upper():
            return 'high'
        else:
            return 'low'
    
    def _get_license_fix(self, license_def: Dict) -> str:
        """Get fix recommendation for license"""
        if license_def['risk'] in ['critical', 'high']:
            return f"Review {license_def['name']} terms. Consider alternative with permissive license."
        else:
            return f"{license_def['name']} is generally permissive."
    
    def _dedupe(self, findings: List[Dict]) -> List[Dict]:
        """Remove duplicate findings"""
        seen = set()
        unique = []
        
        for f in findings:
            key = (f.get('type'), f.get('license_name', ''), f.get('line'))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique


# Singleton
_license_scanner = None

def get_license_scanner() -> LicenseScanner:
    global _license_scanner
    if _license_scanner is None:
        _license_scanner = LicenseScanner()
    return _license_scanner
