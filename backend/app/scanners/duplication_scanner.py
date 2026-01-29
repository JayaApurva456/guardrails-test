"""
Code Duplication & Clone Detection Scanner
Detects copied code, near-duplicates, and OSS license violations
"""

import re
import hashlib
from typing import List, Dict, Any
from difflib import SequenceMatcher
import asyncio


class DuplicationScanner:
    """Detects code duplication and cloning"""
    
    def __init__(self):
        # Known OSS code snippets (simplified - in production would be a database)
        self.known_oss_patterns = [
            {
                'snippet': 'def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):',
                'source': 'Common sorting algorithm',
                'license': 'Public Domain'
            },
            {
                'snippet': 'class Singleton:\n    _instance = None\n    def __new__(cls):',
                'source': 'Common design pattern',
                'license': 'Public Domain'
            }
        ]
        
    async def scan(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """
        Scan for code duplication and clones
        
        Args:
            code: Source code to analyze
            filename: Name of the file
            
        Returns:
            List of duplication findings
        """
        findings = []
        
        # 1. Self-duplication within file
        findings.extend(self._detect_self_duplication(code, filename))
        
        # 2. Known OSS pattern matching
        findings.extend(self._detect_oss_patterns(code, filename))
        
        # 3. Code block similarity (simulated cross-file for demo)
        findings.extend(self._detect_similar_blocks(code, filename))
        
        return findings
    
    def _detect_self_duplication(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Detect duplicated code blocks within the same file"""
        findings = []
        lines = code.split('\n')
        
        # Extract code blocks (simplified - functions/classes)
        blocks = self._extract_code_blocks(code)
        
        # Compare blocks for similarity
        for i, block1 in enumerate(blocks):
            for j, block2 in enumerate(blocks[i+1:], i+1):
                similarity = self._calculate_similarity(block1['code'], block2['code'])
                
                if similarity > 0.85:  # 85% similar
                    findings.append({
                        'type': 'duplicate-code-block',
                        'severity': 'medium',
                        'line': block1['start_line'],
                        'end_line': block1['end_line'],
                        'message': f"Code block duplicated at lines {block2['start_line']}-{block2['end_line']} (similarity: {similarity*100:.1f}%)",
                        'cwe': 'CWE-1041',  # Use of redundant code
                        'fix': 'Extract common logic into a reusable function',
                        'source': 'duplication-detector',
                        'confidence': 'high',
                        'duplicate_lines': f"{block2['start_line']}-{block2['end_line']}",
                        'similarity_score': round(similarity, 3)
                    })
        
        return findings
    
    def _detect_oss_patterns(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Detect potentially copied OSS code"""
        findings = []
        
        for pattern in self.known_oss_patterns:
            similarity = self._calculate_similarity(code, pattern['snippet'])
            
            if similarity > 0.75:  # 75% match with known OSS
                findings.append({
                    'type': 'potential-oss-code',
                    'severity': 'high',
                    'line': 1,
                    'message': f"Code similar to {pattern['source']} (similarity: {similarity*100:.1f}%)",
                    'cwe': 'CWE-829',  # Inclusion of functionality from untrusted source
                    'fix': f"Verify license compatibility: {pattern['license']}",
                    'source': 'duplication-detector',
                    'confidence': 'medium',
                    'oss_source': pattern['source'],
                    'oss_license': pattern['license'],
                    'similarity_score': round(similarity, 3)
                })
        
        return findings
    
    def _detect_similar_blocks(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Detect repeated patterns that suggest copy-paste"""
        findings = []
        lines = code.split('\n')
        
        # Look for repeated line patterns
        line_hashes = {}
        for i, line in enumerate(lines, 1):
            # Skip empty lines and comments
            clean_line = line.strip()
            if not clean_line or clean_line.startswith('#'):
                continue
            
            # Normalize line (remove variable names)
            normalized = self._normalize_line(clean_line)
            line_hash = hashlib.md5(normalized.encode()).hexdigest()
            
            if line_hash in line_hashes:
                line_hashes[line_hash].append(i)
            else:
                line_hashes[line_hash] = [i]
        
        # Report lines that appear 3+ times (likely copy-paste)
        for line_hash, line_numbers in line_hashes.items():
            if len(line_numbers) >= 3:
                findings.append({
                    'type': 'repeated-code-pattern',
                    'severity': 'low',
                    'line': line_numbers[0],
                    'message': f"Similar code pattern repeated {len(line_numbers)} times (lines: {', '.join(map(str, line_numbers))})",
                    'cwe': 'CWE-1041',
                    'fix': 'Consider creating a helper function to reduce duplication',
                    'source': 'duplication-detector',
                    'confidence': 'medium',
                    'repetition_count': len(line_numbers),
                    'all_occurrences': line_numbers
                })
        
        return findings
    
    def _extract_code_blocks(self, code: str) -> List[Dict[str, Any]]:
        """Extract function and class blocks from code"""
        blocks = []
        lines = code.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect function or class definition
            if line.startswith('def ') or line.startswith('class '):
                start_line = i + 1
                indent = len(lines[i]) - len(lines[i].lstrip())
                
                # Find end of block (next line with same or less indentation)
                j = i + 1
                block_lines = [lines[i]]
                while j < len(lines):
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    if lines[j].strip() and current_indent <= indent:
                        break
                    block_lines.append(lines[j])
                    j += 1
                
                blocks.append({
                    'start_line': start_line,
                    'end_line': start_line + len(block_lines) - 1,
                    'code': '\n'.join(block_lines)
                })
                
                i = j
            else:
                i += 1
        
        return blocks
    
    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity ratio between two code snippets"""
        # Normalize both snippets
        norm1 = self._normalize_code(code1)
        norm2 = self._normalize_code(code2)
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison (remove variable names, etc.)"""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Remove extra whitespace
        code = re.sub(r'\s+', ' ', code)
        
        # Remove string literals (keep structure)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        
        return code.strip()
    
    def _normalize_line(self, line: str) -> str:
        """Normalize a single line for pattern matching"""
        # Replace variable names with placeholders
        line = re.sub(r'\b[a-z_][a-z0-9_]*\b', 'VAR', line)
        
        # Replace numbers with placeholder
        line = re.sub(r'\b\d+\b', 'NUM', line)
        
        # Replace strings with placeholder
        line = re.sub(r'"[^"]*"', 'STR', line)
        line = re.sub(r"'[^']*'", 'STR', line)
        
        return line


# Singleton instance
_scanner_instance = None

def get_duplication_scanner() -> DuplicationScanner:
    """Get singleton instance of duplication scanner"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = DuplicationScanner()
    return _scanner_instance
