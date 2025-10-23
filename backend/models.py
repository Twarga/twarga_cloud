"""
SQLAlchemy ORM models for Twarga Cloud MVP
Defines User, VM, and Event database models
"""

import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """
    User model for authentication and user management
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    credits = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    vms = relationship("VM", back_populates="owner", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class VM(Base):
    """
    Virtual Machine model for VM management
    """
    __tablename__ = "vms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    os_type = Column(String(50), nullable=False)  # ubuntu, centos, debian, etc.
    ram_mb = Column(Integer, nullable=False)  # RAM in MB
    disk_gb = Column(Integer, nullable=False)  # Disk in GB
    cpu_cores = Column(Integer, nullable=False)  # Number of CPU cores
    status = Column(String(20), default="stopped", nullable=False)  # running, stopped, pending
    ip_address = Column(String(15), nullable=True)  # VM IP address
    ssh_port = Column(Integer, nullable=True)  # SSH port for terminal access
    uptime_seconds = Column(Integer, default=0, nullable=False)  # VM uptime in seconds
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="vms")
    events = relationship("Event", back_populates="vm", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="vm", cascade="all, delete-orphan")
    
    # VM metadata as JSON (for additional configuration)
    vm_metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<VM(id={self.id}, name='{self.name}', status='{self.status}')>"

class Event(Base):
    """
    Event model for security logging and system events
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # vm, auth, system, security
    severity = Column(String(20), default="info", nullable=False)  # info, warning, critical
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional event details as JSON
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vm_id = Column(Integer, ForeignKey("vms.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="events")
    vm = relationship("VM", back_populates="events")
    
    def __repr__(self):
        return f"<Event(id={self.id}, type='{self.type}', severity='{self.severity}')>"

class Metric(Base):
    """
    Metric model for system and VM monitoring data
    """
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # cpu_usage, memory_usage, disk_usage
    value = Column(Float, nullable=False)  # Metric value
    unit = Column(String(20), nullable=False)  # %, MB, GB, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Foreign Keys
    vm_id = Column(Integer, ForeignKey("vms.id"), nullable=True)
    
    # Relationships
    vm = relationship("VM", back_populates="metrics")
    
    def __repr__(self):
        return f"<Metric(id={self.id}, name='{self.name}', value={self.value}{self.unit})>"

# Update Base metadata to include all models
Base.metadata.reflect_only = False