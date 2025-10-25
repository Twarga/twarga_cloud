"""
🧁 LabsBakery Core - VM and Network Models
Defines database schemas for virtual machines and networks
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class VM(SQLModel, table=True):
    """
    Virtual Machine Model
    Represents a single VM in a lab project
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    
    # VM Configuration
    name: str = Field(max_length=100)
    box: str = Field(max_length=200)  # Vagrant box name (e.g., "kalilinux/rolling")
    ram_mb: int = Field(default=2048, ge=512)  # Minimum 512MB
    cpu_cores: int = Field(default=2, ge=1)  # Minimum 1 core
    
    # Network Configuration
    network_id: str = Field(max_length=50)
    ip_address: str = Field(max_length=15)
    
    # Runtime Information
    ssh_port: Optional[int] = None
    vnc_port: Optional[int] = None
    
    # Status: pending, downloading, starting, running, stopping, stopped, error
    status: str = Field(default="pending", max_length=20)
    
    # Vagrant machine ID (for management)
    vagrant_id: Optional[str] = Field(default=None, max_length=100)
    
    # Error message if status is "error"
    error_message: Optional[str] = Field(default=None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "name": "Kali-Linux",
                "box": "kalilinux/rolling",
                "ram_mb": 2048,
                "cpu_cores": 2,
                "network_id": "net_1",
                "ip_address": "192.168.56.10",
                "status": "pending"
            }
        }


class Network(SQLModel, table=True):
    """
    Network Model
    Represents a virtual network connecting VMs in a lab
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    
    # Network Configuration
    name: str = Field(max_length=100)
    subnet: str = Field(max_length=18)  # e.g., "192.168.56.0/24"
    dhcp_enabled: bool = Field(default=True)
    
    # Optional gateway
    gateway: Optional[str] = Field(default=None, max_length=15)
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "name": "Lab Network 1",
                "subnet": "192.168.56.0/24",
                "dhcp_enabled": True
            }
        }


class VMCreate(SQLModel):
    """Schema for creating a new VM"""
    project_id: int
    name: str
    box: str
    ram_mb: int = 2048
    cpu_cores: int = 2
    network_id: str
    ip_address: str


class VMUpdate(SQLModel):
    """Schema for updating a VM"""
    name: Optional[str] = None
    ram_mb: Optional[int] = None
    cpu_cores: Optional[int] = None
    status: Optional[str] = None
    ssh_port: Optional[int] = None
    vnc_port: Optional[int] = None
    error_message: Optional[str] = None


class NetworkCreate(SQLModel):
    """Schema for creating a new network"""
    project_id: int
    name: str
    subnet: str
    dhcp_enabled: bool = True
    gateway: Optional[str] = None
