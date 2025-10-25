"""
🧁 LabsBakery Core - Configuration Module
Handles application settings and environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "LabsBakery Core"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./labsbakery.db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Vagrant/VM Settings
    vm_base_dir: str = "/tmp/labsbakery"
    vagrant_provider: str = "libvirt"  # or "hyperv" for Windows
    
    # Resource Limits
    max_vms_per_lab: int = 10
    default_ram_mb: int = 2048
    default_cpu_cores: int = 2
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/labsbakery.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
