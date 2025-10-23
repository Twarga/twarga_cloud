"""
Pydantic schemas for Twarga Cloud MVP
Defines request/response models for API validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    credits: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class VMBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    os_type: str = Field(..., min_length=2, max_length=50)
    ram_mb: int = Field(..., ge=512, le=16384)
    disk_gb: int = Field(..., ge=10, le=500)
    cpu_cores: int = Field(..., ge=1, le=8)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('VM name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()
    
    @validator('os_type')
    def validate_os_type(cls, v):
        valid_os_types = ['ubuntu', 'ubuntu20', 'ubuntu22', 'centos', 'centos7', 'centos8', 'debian', 'debian10', 'debian11']
        if v.lower() not in valid_os_types:
            raise ValueError(f'OS type must be one of: {", ".join(valid_os_types)}')
        return v.lower()

class VMCreate(VMBase):
    pass

class VMUpdate(BaseModel):
    name: Optional[str] = None
    vm_metadata: Optional[Dict[str, Any]] = None

class VMResponse(VMBase):
    id: int
    status: str
    ip_address: Optional[str] = None
    ssh_port: Optional[int] = None
    uptime_seconds: int
    owner_id: int
    vm_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VMAction(BaseModel):
    action: str = Field(..., pattern='^(start|stop|restart|destroy)$')

class VMQuotaCheck(BaseModel):
    ram_mb: int
    disk_gb: int
    cpu_cores: int
    estimated_cost: int

class EventBase(BaseModel):
    type: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None

class EventCreate(EventBase):
    user_id: Optional[int] = None
    vm_id: Optional[int] = None

class EventResponse(EventBase):
    id: int
    user_id: Optional[int] = None
    vm_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MetricBase(BaseModel):
    name: str
    value: float
    unit: str

class MetricCreate(MetricBase):
    vm_id: Optional[int] = None

class MetricResponse(MetricBase):
    id: int
    vm_id: Optional[int] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class CreditAdjustment(BaseModel):
    user_id: int
    amount: int = Field(..., ge=-10000, le=10000)
    reason: Optional[str] = None

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    version: str
    database: Optional[dict] = None
