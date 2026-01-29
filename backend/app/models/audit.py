"""Audit model"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Float
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String, unique=True, index=True)
    repository = Column(String, index=True)
    pr_number = Column(Integer)
    total_violations = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    copilot_detected = Column(Boolean, default=False)
    duration = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
