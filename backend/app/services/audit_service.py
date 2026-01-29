"""
Audit Logging Service
Records all violations, actions, and resolutions for compliance
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import sqlite3
from contextlib import contextmanager


class AuditLogger:
    """Audit logging for compliance and traceability"""
    
    def __init__(self, db_path: str = "audit_logs.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for audit logs"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scan_id TEXT NOT NULL,
                    repository TEXT,
                    file_path TEXT,
                    language TEXT,
                    total_violations INTEGER,
                    critical_count INTEGER,
                    high_count INTEGER,
                    medium_count INTEGER,
                    low_count INTEGER,
                    policy_mode TEXT,
                    action_taken TEXT,
                    blocked BOOLEAN,
                    copilot_detected BOOLEAN,
                    duration_seconds REAL,
                    user_id TEXT,
                    pr_number INTEGER,
                    violations_json TEXT,
                    resolution_state TEXT,
                    override_approved BOOLEAN,
                    override_approver TEXT,
                    notes TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS violation_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_log_id INTEGER,
                    violation_type TEXT,
                    severity TEXT,
                    line_number INTEGER,
                    source TEXT,
                    message TEXT,
                    cwe TEXT,
                    owasp TEXT,
                    fixed BOOLEAN DEFAULT 0,
                    fix_timestamp TEXT,
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id)
                )
            ''')
            
            # Create indices for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_repository ON audit_logs(repository)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_severity ON violation_details(severity)')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    async def log_scan(
        self,
        scan_id: str,
        repository: str,
        file_path: str,
        language: str,
        violations: List[Dict[str, Any]],
        policy_action: Dict[str, Any],
        duration: float,
        copilot_detected: bool = False,
        user_id: Optional[str] = None,
        pr_number: Optional[int] = None
    ) -> int:
        """
        Log a complete scan with all violations
        
        Returns:
            audit_log_id: ID of the created audit log entry
        """
        # Count violations by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for v in violations:
            severity = v.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        timestamp = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO audit_logs (
                    timestamp, scan_id, repository, file_path, language,
                    total_violations, critical_count, high_count, medium_count, low_count,
                    policy_mode, action_taken, blocked, copilot_detected,
                    duration_seconds, user_id, pr_number, violations_json,
                    resolution_state, override_approved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                scan_id,
                repository,
                file_path,
                language,
                len(violations),
                severity_counts['critical'],
                severity_counts['high'],
                severity_counts['medium'],
                severity_counts['low'],
                policy_action.get('mode', 'unknown'),
                policy_action.get('reason', ''),
                policy_action.get('should_block', False),
                copilot_detected,
                duration,
                user_id,
                pr_number,
                json.dumps(violations),
                'open',
                False
            ))
            
            audit_log_id = cursor.lastrowid
            
            # Log individual violation details
            for violation in violations:
                conn.execute('''
                    INSERT INTO violation_details (
                        audit_log_id, violation_type, severity, line_number,
                        source, message, cwe, owasp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_log_id,
                    violation.get('type', 'unknown'),
                    violation.get('severity', 'low'),
                    violation.get('line', 0),
                    violation.get('source', 'unknown'),
                    violation.get('message', ''),
                    violation.get('cwe', ''),
                    violation.get('owasp', '')
                ))
            
            conn.commit()
        
        return audit_log_id
    
    async def update_resolution(
        self,
        scan_id: str,
        resolution_state: str,
        override_approved: bool = False,
        override_approver: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Update the resolution state of a scan"""
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE audit_logs
                SET resolution_state = ?,
                    override_approved = ?,
                    override_approver = ?,
                    notes = ?
                WHERE scan_id = ?
            ''', (resolution_state, override_approved, override_approver, notes, scan_id))
            conn.commit()
    
    async def mark_violation_fixed(self, audit_log_id: int, violation_type: str):
        """Mark a specific violation as fixed"""
        timestamp = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE violation_details
                SET fixed = 1, fix_timestamp = ?
                WHERE audit_log_id = ? AND violation_type = ?
            ''', (timestamp, audit_log_id, violation_type))
            conn.commit()
    
    async def get_scan_history(
        self,
        repository: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get scan history with optional filters"""
        query = 'SELECT * FROM audit_logs WHERE 1=1'
        params = []
        
        if repository:
            query += ' AND repository = ?'
            params.append(repository)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    async def get_statistics(
        self,
        repository: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get aggregate statistics"""
        query = '''
            SELECT 
                COUNT(*) as total_scans,
                SUM(total_violations) as total_violations,
                SUM(critical_count) as critical_violations,
                SUM(high_count) as high_violations,
                SUM(medium_count) as medium_violations,
                SUM(low_count) as low_violations,
                AVG(duration_seconds) as avg_duration,
                SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked_scans,
                SUM(CASE WHEN copilot_detected THEN 1 ELSE 0 END) as copilot_scans
            FROM audit_logs
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        '''
        params = [days]
        
        if repository:
            query += ' AND repository = ?'
            params.append(repository)
        
        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else {}
    
    async def export_to_csv(
        self,
        output_path: str,
        repository: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """Export audit logs to CSV file"""
        scans = await self.get_scan_history(repository, start_date, end_date, limit=10000)
        
        with open(output_path, 'w', newline='') as csvfile:
            if not scans:
                return output_path
            
            fieldnames = scans[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(scans)
        
        return output_path
    
    async def export_to_json(
        self,
        output_path: str,
        repository: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """Export audit logs to JSON file"""
        scans = await self.get_scan_history(repository, start_date, end_date, limit=10000)
        
        with open(output_path, 'w') as jsonfile:
            json.dump(scans, jsonfile, indent=2)
        
        return output_path
    
    async def get_violation_trends(
        self,
        repository: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get violation trends over time"""
        query = '''
            SELECT 
                date(timestamp) as date,
                COUNT(*) as scan_count,
                SUM(total_violations) as violation_count,
                SUM(critical_count) as critical,
                SUM(high_count) as high,
                SUM(medium_count) as medium,
                SUM(low_count) as low
            FROM audit_logs
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        '''
        params = [days]
        
        if repository:
            query += ' AND repository = ?'
            params.append(repository)
        
        query += ' GROUP BY date(timestamp) ORDER BY date'
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return {'trends': [dict(row) for row in rows]}
    
    async def get_top_violations(
        self,
        repository: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most common violation types"""
        query = '''
            SELECT 
                v.violation_type,
                v.severity,
                COUNT(*) as count,
                SUM(CASE WHEN v.fixed THEN 1 ELSE 0 END) as fixed_count
            FROM violation_details v
            JOIN audit_logs a ON v.audit_log_id = a.id
            WHERE 1=1
        '''
        params = []
        
        if repository:
            query += ' AND a.repository = ?'
            params.append(repository)
        
        query += ' GROUP BY v.violation_type, v.severity ORDER BY count DESC LIMIT ?'
        params.append(limit)
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]


# Singleton instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get singleton instance of audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
