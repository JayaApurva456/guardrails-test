"""
Enterprise Rule Engine
Loads and applies industry-specific compliance rules
"""
import yaml
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RuleEngine:
    """Enterprise Rule Engine for compliance checking"""
    
    def __init__(self, rules_dir: str = "rules"):
        self.rules_dir = Path(rules_dir)
        self.rule_packs = {}
        self.compiled_patterns = {}
        self._load_rule_packs()
    
    def _load_rule_packs(self):
        """Load all YAML rule packs"""
        if not self.rules_dir.exists():
            logger.warning(f"Rules directory not found: {self.rules_dir}")
            return
        
        for rule_file in self.rules_dir.glob("*.yaml"):
            try:
                with open(rule_file, 'r') as f:
                    rule_pack = yaml.safe_load(f)
                
                pack_name = rule_file.stem
                self.rule_packs[pack_name] = rule_pack
                self._compile_patterns(pack_name, rule_pack)
                
                logger.info(f"Loaded rule pack: {pack_name}")
            except Exception as e:
                logger.error(f"Failed to load {rule_file}: {e}")
    
    def _compile_patterns(self, pack_name, rule_pack):
        """Pre-compile regex patterns"""
        self.compiled_patterns[pack_name] = []
        
        rules = rule_pack.get('rules', {})
        for rule_id, rule_def in rules.items():
            patterns = rule_def.get('patterns', [])
            compiled = []
            
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern))
                except:
                    pass
            
            self.compiled_patterns[pack_name].append({
                'rule_id': rule_id,
                'rule_def': rule_def,
                'patterns': compiled
            })
    
    def analyze_code(self, code: str, filename: str, enabled_packs: Optional[List[str]] = None) -> List[Dict]:
        """Analyze code against rule packs"""
        violations = []
        packs = enabled_packs if enabled_packs else list(self.rule_packs.keys())
        
        for pack_name in packs:
            if pack_name not in self.compiled_patterns:
                continue
            violations.extend(self._check_pack(code, filename, pack_name))
        
        return violations
    
    def _check_pack(self, code, filename, pack_name):
        """Check code against specific pack"""
        violations = []
        lines = code.split('\n')
        
        for rule_entry in self.compiled_patterns[pack_name]:
            for pattern in rule_entry['patterns']:
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        violations.append(self._create_violation(
                            rule_entry['rule_id'],
                            rule_entry['rule_def'],
                            i,
                            line.strip(),
                            filename,
                            pack_name
                        ))
        return violations
    
    def _create_violation(self, rule_id, rule_def, line_num, snippet, filename, pack):
        """Create violation dict"""
        compliance = []
        if 'pci_dss' in rule_def:
            compliance.append(f"PCI-DSS {', '.join(rule_def['pci_dss'])}")
        if 'hipaa' in rule_def:
            compliance.append(f"HIPAA {', '.join(rule_def['hipaa'])}")
        if 'nist' in rule_def:
            compliance.append(f"NIST {', '.join(rule_def['nist'])}")
        
        return {
            'type': rule_id,
            'severity': rule_def.get('severity', 'medium').lower(),
            'line': line_num,
            'code_snippet': snippet,
            'filename': filename,
            'vulnerability': rule_def.get('name', rule_id),
            'message': rule_def.get('description', ''),
            'fix': rule_def.get('fix', ''),
            'cwe_id': rule_def.get('cwe', ''),
            'compliance': compliance,
            'source': f'rule-engine:{pack}',
            'rule_pack': pack
        }
    
    def get_enabled_packs(self, owner, repo):
        """Get enabled packs for repo"""
        packs = ['security-rules']
        repo_lower = repo.lower()
        
        if any(w in repo_lower for w in ['bank', 'payment', 'finance']):
            packs.append('banking-pci-dss')
        if any(w in repo_lower for w in ['health', 'medical', 'patient']):
            packs.append('healthcare-hipaa')
        if any(w in repo_lower for w in ['gov', 'federal', 'fedramp']):
            packs.append('government-fedramp')
        if any(w in repo_lower for w in ['telecom', '5g', 'mobile']):
            packs.append('telecommunications')
        
        return packs
