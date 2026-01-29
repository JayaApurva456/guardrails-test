"""
Enhanced Coding Standards Scanner
Enforces naming conventions, logging requirements, and error handling patterns
"""

import re
from typing import List, Dict, Any


class CodingStandardsScanner:
    """Enforces enterprise coding standards beyond security"""
    
    def __init__(self):
        self.standards = {
            'naming': True,
            'logging': True,
            'error_handling': True,
            'documentation': True
        }
    
    async def scan(self, code: str, filename: str, language: str) -> List[Dict[str, Any]]:
        """
        Scan code for coding standard violations
        
        Args:
            code: Source code to analyze
            filename: Name of the file
            language: Programming language
            
        Returns:
            List of standard violations
        """
        findings = []
        
        if language == 'python':
            findings.extend(self._check_python_standards(code, filename))
        elif language in ['javascript', 'typescript']:
            findings.extend(self._check_javascript_standards(code, filename))
        
        return findings
    
    def _check_python_standards(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Check Python-specific coding standards"""
        findings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 1. Naming convention checks
            findings.extend(self._check_naming_conventions(line, i, 'python'))
            
            # 2. Logging requirement checks
            findings.extend(self._check_logging_standards(line, i, code))
            
            # 3. Error handling checks
            findings.extend(self._check_error_handling(line, i, code))
            
            # 4. Documentation checks
            findings.extend(self._check_documentation(line, i, code))
        
        return findings
    
    def _check_naming_conventions(self, line: str, line_num: int, language: str) -> List[Dict[str, Any]]:
        """Check naming convention violations"""
        findings = []
        
        if language == 'python':
            # Check for camelCase in Python (should be snake_case)
            camel_case_vars = re.findall(r'\b([a-z]+[A-Z][a-zA-Z]*)\s*=', line)
            for var in camel_case_vars:
                findings.append({
                    'type': 'naming-convention-violation',
                    'severity': 'low',
                    'line': line_num,
                    'message': f"Variable '{var}' uses camelCase instead of snake_case",
                    'fix': f"Rename to '{self._to_snake_case(var)}'",
                    'source': 'coding-standards',
                    'confidence': 'high',
                    'standard': 'PEP 8',
                    'variable_name': var,
                    'suggested_name': self._to_snake_case(var)
                })
            
            # Check for uppercase constants not in SCREAMING_SNAKE_CASE
            const_pattern = re.findall(r'\b([A-Z][a-z]+[A-Z][a-zA-Z]*)\s*=', line)
            for const in const_pattern:
                if const not in ['True', 'False', 'None']:
                    findings.append({
                        'type': 'constant-naming-violation',
                        'severity': 'low',
                        'line': line_num,
                        'message': f"Constant '{const}' should use SCREAMING_SNAKE_CASE",
                        'fix': f"Rename to '{self._to_screaming_snake_case(const)}'",
                        'source': 'coding-standards',
                        'confidence': 'high',
                        'standard': 'PEP 8',
                        'constant_name': const,
                        'suggested_name': self._to_screaming_snake_case(const)
                    })
            
            # Check for class names not in PascalCase
            class_def = re.search(r'class\s+([a-z_][a-z0-9_]*)\s*[:\(]', line)
            if class_def:
                class_name = class_def.group(1)
                findings.append({
                    'type': 'class-naming-violation',
                    'severity': 'medium',
                    'line': line_num,
                    'message': f"Class '{class_name}' should use PascalCase",
                    'fix': f"Rename to '{self._to_pascal_case(class_name)}'",
                    'source': 'coding-standards',
                    'confidence': 'high',
                    'standard': 'PEP 8',
                    'class_name': class_name,
                    'suggested_name': self._to_pascal_case(class_name)
                })
        
        return findings
    
    def _check_logging_standards(self, line: str, line_num: int, full_code: str) -> List[Dict[str, Any]]:
        """Check logging requirement violations"""
        findings = []
        
        # Check for print() usage instead of logging
        if 'print(' in line and 'def ' not in line:
            findings.append({
                'type': 'logging-standard-violation',
                'severity': 'medium',
                'line': line_num,
                'message': "Using print() instead of proper logging",
                'fix': "Replace with logger.info() or logger.debug()",
                'source': 'coding-standards',
                'confidence': 'high',
                'standard': 'Enterprise Logging Guidelines',
                'example': 'import logging; logger = logging.getLogger(__name__); logger.info("message")'
            })
        
        # Check for exception handling without logging
        if re.search(r'except\s+\w+\s*:', line):
            # Look ahead for logging in the except block
            except_block = self._extract_except_block(full_code, line_num)
            if 'logger' not in except_block and 'logging' not in except_block:
                findings.append({
                    'type': 'missing-exception-logging',
                    'severity': 'high',
                    'line': line_num,
                    'message': "Exception caught but not logged",
                    'fix': "Add logger.error() or logger.exception() in except block",
                    'source': 'coding-standards',
                    'confidence': 'medium',
                    'standard': 'Enterprise Error Handling',
                    'example': 'except Exception as e: logger.exception("Error occurred")'
                })
        
        return findings
    
    def _check_error_handling(self, line: str, line_num: int, full_code: str) -> List[Dict[str, Any]]:
        """Check error handling pattern violations"""
        findings = []
        
        # Check for bare except clauses
        if re.match(r'\s*except\s*:', line):
            findings.append({
                'type': 'bare-except-clause',
                'severity': 'high',
                'line': line_num,
                'message': "Bare 'except:' clause catches all exceptions including system exits",
                'fix': "Use 'except Exception:' or specific exception types",
                'source': 'coding-standards',
                'confidence': 'high',
                'standard': 'PEP 8',
                'cwe': 'CWE-396'
            })
        
        # Check for pass in except blocks
        if 'except' in line:
            except_block = self._extract_except_block(full_code, line_num)
            if re.search(r'except[^:]*:\s*pass', except_block):
                findings.append({
                    'type': 'silent-exception',
                    'severity': 'high',
                    'line': line_num,
                    'message': "Exception silently swallowed with 'pass'",
                    'fix': "Log the exception or re-raise it",
                    'source': 'coding-standards',
                    'confidence': 'high',
                    'standard': 'Enterprise Error Handling',
                    'cwe': 'CWE-391'
                })
        
        # Check for functions without try-except
        if re.match(r'\s*def\s+\w+', line) and 'main' not in line:
            func_body = self._extract_function_body(full_code, line_num)
            # Check if function does I/O or external calls
            has_io = any(keyword in func_body for keyword in ['open(', 'requests.', 'http', 'db.', 'subprocess'])
            has_try = 'try:' in func_body
            
            if has_io and not has_try:
                findings.append({
                    'type': 'missing-error-handling',
                    'severity': 'medium',
                    'line': line_num,
                    'message': "Function performs I/O operations without error handling",
                    'fix': "Wrap I/O operations in try-except block",
                    'source': 'coding-standards',
                    'confidence': 'medium',
                    'standard': 'Enterprise Reliability'
                })
        
        return findings
    
    def _check_documentation(self, line: str, line_num: int, full_code: str) -> List[Dict[str, Any]]:
        """Check documentation requirements"""
        findings = []
        
        # Check for public functions without docstrings
        if re.match(r'\s*def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\(', line):
            func_name = re.search(r'def\s+([a-zA-Z][a-zA-Z0-9_]*)', line).group(1)
            
            # Skip private functions
            if not func_name.startswith('_'):
                func_body = self._extract_function_body(full_code, line_num)
                lines_after = func_body.split('\n')[:3]
                
                has_docstring = any('"""' in l or "'''" in l for l in lines_after)
                
                if not has_docstring and len(func_body) > 50:  # Only for non-trivial functions
                    findings.append({
                        'type': 'missing-docstring',
                        'severity': 'low',
                        'line': line_num,
                        'message': f"Public function '{func_name}' missing docstring",
                        'fix': "Add docstring describing function purpose, parameters, and return value",
                        'source': 'coding-standards',
                        'confidence': 'high',
                        'standard': 'PEP 257',
                        'function_name': func_name
                    })
        
        # Check for class without docstring
        if re.match(r'\s*class\s+\w+', line):
            class_body_start = line_num + 1
            lines = full_code.split('\n')
            if class_body_start < len(lines):
                next_line = lines[class_body_start].strip()
                if not (next_line.startswith('"""') or next_line.startswith("'''")):
                    class_name = re.search(r'class\s+(\w+)', line).group(1)
                    findings.append({
                        'type': 'missing-class-docstring',
                        'severity': 'low',
                        'line': line_num,
                        'message': f"Class '{class_name}' missing docstring",
                        'fix': "Add docstring describing class purpose",
                        'source': 'coding-standards',
                        'confidence': 'high',
                        'standard': 'PEP 257',
                        'class_name': class_name
                    })
        
        return findings
    
    def _check_javascript_standards(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Check JavaScript/TypeScript coding standards"""
        findings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for var usage (should use const/let)
            if re.match(r'\s*var\s+', line):
                findings.append({
                    'type': 'deprecated-var-usage',
                    'severity': 'medium',
                    'line': i,
                    'message': "Using 'var' instead of 'const' or 'let'",
                    'fix': "Use 'const' for constants or 'let' for mutable variables",
                    'source': 'coding-standards',
                    'confidence': 'high',
                    'standard': 'ES6+'
                })
            
            # Check for console.log (should use proper logging)
            if 'console.log(' in line:
                findings.append({
                    'type': 'console-log-usage',
                    'severity': 'low',
                    'line': i,
                    'message': "Using console.log instead of proper logging",
                    'fix': "Use Winston, Bunyan, or similar logging library",
                    'source': 'coding-standards',
                    'confidence': 'high',
                    'standard': 'Enterprise Logging'
                })
        
        return findings
    
    # Helper methods
    def _to_snake_case(self, name: str) -> str:
        """Convert camelCase to snake_case"""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def _to_screaming_snake_case(self, name: str) -> str:
        """Convert to SCREAMING_SNAKE_CASE"""
        return self._to_snake_case(name).upper()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def _extract_except_block(self, code: str, except_line: int) -> str:
        """Extract the content of an except block"""
        lines = code.split('\n')
        if except_line >= len(lines):
            return ""
        
        start = except_line
        indent = len(lines[start]) - len(lines[start].lstrip())
        
        block = [lines[start]]
        for i in range(start + 1, len(lines)):
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if lines[i].strip() and current_indent <= indent:
                break
            block.append(lines[i])
        
        return '\n'.join(block)
    
    def _extract_function_body(self, code: str, func_line: int) -> str:
        """Extract the body of a function"""
        lines = code.split('\n')
        if func_line >= len(lines):
            return ""
        
        start = func_line
        indent = len(lines[start]) - len(lines[start].lstrip())
        
        body = []
        for i in range(start + 1, len(lines)):
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if lines[i].strip() and current_indent <= indent:
                break
            body.append(lines[i])
        
        return '\n'.join(body)


# Singleton instance
_scanner_instance = None

def get_coding_standards_scanner() -> CodingStandardsScanner:
    """Get singleton instance of coding standards scanner"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = CodingStandardsScanner()
    return _scanner_instance
