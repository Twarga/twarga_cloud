"""
Security Operations Center module for Twarga Cloud MVP
Handles security event feed, log parsing, and event correlation
"""

import os
import re
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from .models import Event, User, VM

logger = logging.getLogger(__name__)


class SOCManager:
    """
    SOC Manager for handling security events, log parsing, and event correlation
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize SOC Manager
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.events_log = self.log_dir / "events.log"
        self.ssh_log = self.log_dir / "ssh_attempts.log"
        
    # ==================== EVENT LOGGING FUNCTIONS ====================
    
    def log_event(
        self,
        db: Session,
        event_type: str,
        severity: str,
        message: str,
        user_id: Optional[int] = None,
        vm_id: Optional[int] = None,
        details: Optional[Dict] = None
    ) -> Event:
        """
        Log a security or system event
        
        Args:
            db: Database session
            event_type: Event type (vm, auth, system, security)
            severity: Event severity (info, warning, critical)
            message: Event message
            user_id: Optional user ID
            vm_id: Optional VM ID
            details: Optional additional details as dict
            
        Returns:
            Created Event object
        """
        event = Event(
            type=event_type,
            severity=severity,
            message=message,
            user_id=user_id,
            vm_id=vm_id,
            details=details or {}
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        # Also log to file for audit trail
        log_level = logging.INFO if severity == "info" else logging.WARNING if severity == "warning" else logging.CRITICAL
        logger.log(log_level, f"[{event_type.upper()}] {message}")
        
        return event
    
    # ==================== VM LIFECYCLE EVENT FUNCTIONS ====================
    
    def log_vm_created(
        self,
        db: Session,
        vm: VM,
        user: User,
        details: Optional[Dict] = None
    ) -> Event:
        """Log VM creation event"""
        message = f"VM '{vm.name}' created by user '{user.username}'"
        event_details = {
            "vm_name": vm.name,
            "vm_id": vm.id,
            "os_type": vm.os_type,
            "ram_mb": vm.ram_mb,
            "disk_gb": vm.disk_gb,
            "cpu_cores": vm.cpu_cores,
            "user": user.username
        }
        
        if details:
            event_details.update(details)
        
        return self.log_event(
            db=db,
            event_type="vm",
            severity="info",
            message=message,
            user_id=user.id,
            vm_id=vm.id,
            details=event_details
        )
    
    def log_vm_started(
        self,
        db: Session,
        vm: VM,
        user: User,
        details: Optional[Dict] = None
    ) -> Event:
        """Log VM start event"""
        message = f"VM '{vm.name}' started by user '{user.username}'"
        event_details = {
            "vm_name": vm.name,
            "vm_id": vm.id,
            "ip_address": vm.ip_address,
            "user": user.username,
            "action": "start"
        }
        
        if details:
            event_details.update(details)
        
        return self.log_event(
            db=db,
            event_type="vm",
            severity="info",
            message=message,
            user_id=user.id,
            vm_id=vm.id,
            details=event_details
        )
    
    def log_vm_stopped(
        self,
        db: Session,
        vm: VM,
        user: User,
        details: Optional[Dict] = None
    ) -> Event:
        """Log VM stop event"""
        message = f"VM '{vm.name}' stopped by user '{user.username}'"
        event_details = {
            "vm_name": vm.name,
            "vm_id": vm.id,
            "uptime_seconds": vm.uptime_seconds,
            "user": user.username,
            "action": "stop"
        }
        
        if details:
            event_details.update(details)
        
        return self.log_event(
            db=db,
            event_type="vm",
            severity="info",
            message=message,
            user_id=user.id,
            vm_id=vm.id,
            details=event_details
        )
    
    def log_vm_destroyed(
        self,
        db: Session,
        vm: VM,
        user: User,
        details: Optional[Dict] = None
    ) -> Event:
        """Log VM destruction event"""
        message = f"VM '{vm.name}' destroyed by user '{user.username}'"
        event_details = {
            "vm_name": vm.name,
            "vm_id": vm.id,
            "user": user.username,
            "action": "destroy",
            "total_uptime": vm.uptime_seconds
        }
        
        if details:
            event_details.update(details)
        
        return self.log_event(
            db=db,
            event_type="vm",
            severity="warning",
            message=message,
            user_id=user.id,
            vm_id=vm.id,
            details=event_details
        )
    
    def log_vm_error(
        self,
        db: Session,
        vm_name: str,
        user: User,
        error_message: str,
        vm_id: Optional[int] = None,
        details: Optional[Dict] = None
    ) -> Event:
        """Log VM error event"""
        message = f"VM '{vm_name}' encountered error: {error_message}"
        event_details = {
            "vm_name": vm_name,
            "error": error_message,
            "user": user.username
        }
        
        if details:
            event_details.update(details)
        
        return self.log_event(
            db=db,
            event_type="vm",
            severity="critical",
            message=message,
            user_id=user.id,
            vm_id=vm_id,
            details=event_details
        )
    
    # ==================== SSH LOGIN MONITORING ====================
    
    def log_ssh_attempt(
        self,
        db: Session,
        vm_id: int,
        success: bool,
        username: str,
        ip_address: str,
        details: Optional[Dict] = None
    ) -> Event:
        """
        Log SSH login attempt
        
        Args:
            db: Database session
            vm_id: VM ID where SSH attempt occurred
            success: Whether login was successful
            username: SSH username attempted
            ip_address: Source IP address
            details: Optional additional details
            
        Returns:
            Created Event object
        """
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            logger.warning(f"SSH attempt logged for non-existent VM ID: {vm_id}")
            return None
        
        severity = "info" if success else "warning"
        status = "successful" if success else "failed"
        message = f"{status.capitalize()} SSH login attempt on VM '{vm.name}' (user: {username}, from: {ip_address})"
        
        event_details = {
            "vm_name": vm.name,
            "vm_id": vm_id,
            "ssh_username": username,
            "source_ip": ip_address,
            "success": success,
            "attempt_type": "ssh"
        }
        
        if details:
            event_details.update(details)
        
        # Log to SSH attempts file
        with open(self.ssh_log, 'a') as f:
            timestamp = datetime.utcnow().isoformat()
            f.write(f"[{timestamp}] {status.upper()} - VM: {vm.name} - User: {username} - IP: {ip_address}\n")
        
        return self.log_event(
            db=db,
            event_type="security",
            severity=severity,
            message=message,
            user_id=vm.owner_id,
            vm_id=vm_id,
            details=event_details
        )
    
    def detect_brute_force(
        self,
        db: Session,
        vm_id: int,
        time_window_minutes: int = 10,
        attempt_threshold: int = 5
    ) -> Tuple[bool, int]:
        """
        Detect potential SSH brute force attacks
        
        Args:
            db: Database session
            vm_id: VM ID to check
            time_window_minutes: Time window to analyze (default: 10 minutes)
            attempt_threshold: Number of failed attempts to trigger alert (default: 5)
            
        Returns:
            Tuple of (is_attack: bool, failed_attempts: int)
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # Query failed SSH attempts in time window
        failed_attempts = db.query(Event).filter(
            Event.vm_id == vm_id,
            Event.type == "security",
            Event.severity == "warning",
            Event.created_at >= cutoff_time,
            Event.details.contains('"success": false')
        ).count()
        
        is_attack = failed_attempts >= attempt_threshold
        
        if is_attack:
            vm = db.query(VM).filter(VM.id == vm_id).first()
            if vm:
                self.log_event(
                    db=db,
                    event_type="security",
                    severity="critical",
                    message=f"Potential SSH brute force attack detected on VM '{vm.name}' ({failed_attempts} failed attempts in {time_window_minutes} minutes)",
                    user_id=vm.owner_id,
                    vm_id=vm_id,
                    details={
                        "attack_type": "brute_force",
                        "failed_attempts": failed_attempts,
                        "time_window_minutes": time_window_minutes
                    }
                )
        
        return is_attack, failed_attempts
    
    # ==================== SYSTEM EVENT FUNCTIONS ====================
    
    def log_system_event(
        self,
        db: Session,
        severity: str,
        message: str,
        details: Optional[Dict] = None
    ) -> Event:
        """Log system-level event"""
        return self.log_event(
            db=db,
            event_type="system",
            severity=severity,
            message=message,
            details=details
        )
    
    def log_resource_alert(
        self,
        db: Session,
        resource_type: str,
        current_value: float,
        threshold: float,
        vm_id: Optional[int] = None
    ) -> Event:
        """
        Log resource usage alert
        
        Args:
            db: Database session
            resource_type: Type of resource (cpu, memory, disk, etc.)
            current_value: Current resource usage value
            threshold: Alert threshold
            vm_id: Optional VM ID if alert is VM-specific
            
        Returns:
            Created Event object
        """
        if vm_id:
            vm = db.query(VM).filter(VM.id == vm_id).first()
            message = f"High {resource_type} usage on VM '{vm.name}': {current_value:.1f}% (threshold: {threshold}%)"
            user_id = vm.owner_id if vm else None
        else:
            message = f"High host {resource_type} usage: {current_value:.1f}% (threshold: {threshold}%)"
            user_id = None
        
        severity = "critical" if current_value >= 95 else "warning"
        
        return self.log_event(
            db=db,
            event_type="system",
            severity=severity,
            message=message,
            user_id=user_id,
            vm_id=vm_id,
            details={
                "resource_type": resource_type,
                "current_value": current_value,
                "threshold": threshold,
                "unit": "%"
            }
        )
    
    # ==================== EVENT ANALYSIS AND CORRELATION ====================
    
    def get_recent_events(
        self,
        db: Session,
        limit: int = 50,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[int] = None,
        vm_id: Optional[int] = None,
        hours: int = 24
    ) -> List[Event]:
        """
        Get recent events with optional filtering
        
        Args:
            db: Database session
            limit: Maximum number of events to return
            event_type: Optional event type filter
            severity: Optional severity filter
            user_id: Optional user ID filter
            vm_id: Optional VM ID filter
            hours: Number of hours to look back (default: 24)
            
        Returns:
            List of Event objects
        """
        query = db.query(Event)
        
        # Time filter
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(Event.created_at >= cutoff_time)
        
        # Apply filters
        if event_type:
            query = query.filter(Event.type == event_type)
        if severity:
            query = query.filter(Event.severity == severity)
        if user_id:
            query = query.filter(Event.user_id == user_id)
        if vm_id:
            query = query.filter(Event.vm_id == vm_id)
        
        # Order by most recent first
        query = query.order_by(Event.created_at.desc())
        
        return query.limit(limit).all()
    
    def get_event_statistics(
        self,
        db: Session,
        hours: int = 24
    ) -> Dict:
        """
        Get event statistics for dashboard
        
        Args:
            db: Database session
            hours: Number of hours to analyze (default: 24)
            
        Returns:
            Dictionary with event statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total events
        total_events = db.query(Event).filter(Event.created_at >= cutoff_time).count()
        
        # Events by type
        events_by_type = {}
        for event_type in ["vm", "auth", "system", "security"]:
            count = db.query(Event).filter(
                Event.type == event_type,
                Event.created_at >= cutoff_time
            ).count()
            events_by_type[event_type] = count
        
        # Events by severity
        events_by_severity = {}
        for severity in ["info", "warning", "critical"]:
            count = db.query(Event).filter(
                Event.severity == severity,
                Event.created_at >= cutoff_time
            ).count()
            events_by_severity[severity] = count
        
        # Critical events
        critical_events = db.query(Event).filter(
            Event.severity == "critical",
            Event.created_at >= cutoff_time
        ).order_by(Event.created_at.desc()).limit(10).all()
        
        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "events_by_severity": events_by_severity,
            "critical_events": [
                {
                    "id": e.id,
                    "type": e.type,
                    "message": e.message,
                    "created_at": e.created_at.isoformat()
                }
                for e in critical_events
            ],
            "time_window_hours": hours
        }
    
    def analyze_user_activity(
        self,
        db: Session,
        user_id: int,
        hours: int = 24
    ) -> Dict:
        """
        Analyze user activity for anomaly detection
        
        Args:
            db: Database session
            user_id: User ID to analyze
            hours: Number of hours to analyze (default: 24)
            
        Returns:
            Dictionary with user activity analysis
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Count events
        total_events = db.query(Event).filter(
            Event.user_id == user_id,
            Event.created_at >= cutoff_time
        ).count()
        
        # VM operations
        vm_events = db.query(Event).filter(
            Event.user_id == user_id,
            Event.type == "vm",
            Event.created_at >= cutoff_time
        ).count()
        
        # Failed auth attempts
        failed_auth = db.query(Event).filter(
            Event.user_id == user_id,
            Event.type == "auth",
            Event.severity == "warning",
            Event.created_at >= cutoff_time
        ).count()
        
        # Active VMs
        active_vms = db.query(VM).filter(
            VM.owner_id == user_id,
            VM.status == "running"
        ).count()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "total_events": total_events,
            "vm_events": vm_events,
            "failed_auth_attempts": failed_auth,
            "active_vms": active_vms,
            "time_window_hours": hours
        }
    
    # ==================== LOG FILE PARSING ====================
    
    def parse_vagrant_logs(
        self,
        log_file: Path
    ) -> List[Dict]:
        """
        Parse Vagrant log files for events
        
        Args:
            log_file: Path to Vagrant log file
            
        Returns:
            List of parsed event dictionaries
        """
        events = []
        
        if not log_file.exists():
            return events
        
        # Patterns to match
        patterns = {
            "vm_up": r"Machine booted in (\d+) seconds",
            "vm_halt": r"Machine gracefully halted",
            "vm_destroy": r"Deleting the machine",
            "error": r"ERROR|Error|error",
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    for event_type, pattern in patterns.items():
                        if re.search(pattern, line):
                            events.append({
                                "type": event_type,
                                "message": line.strip(),
                                "timestamp": datetime.utcnow()
                            })
        except Exception as e:
            logger.error(f"Error parsing Vagrant logs: {e}")
        
        return events
    
    def parse_ssh_logs(
        self,
        log_file: Path
    ) -> List[Dict]:
        """
        Parse SSH log files for login attempts
        
        Args:
            log_file: Path to SSH log file
            
        Returns:
            List of parsed SSH attempt dictionaries
        """
        attempts = []
        
        if not log_file.exists():
            return attempts
        
        # SSH log patterns
        patterns = {
            "accepted": r"Accepted (\w+) for (\w+) from ([\d.]+) port (\d+)",
            "failed": r"Failed (\w+) for (\w+) from ([\d.]+) port (\d+)",
            "invalid": r"Invalid user (\w+) from ([\d.]+)",
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    for attempt_type, pattern in patterns.items():
                        match = re.search(pattern, line)
                        if match:
                            attempts.append({
                                "type": attempt_type,
                                "details": match.groups(),
                                "message": line.strip(),
                                "timestamp": datetime.utcnow()
                            })
        except Exception as e:
            logger.error(f"Error parsing SSH logs: {e}")
        
        return attempts


# Global SOC manager instance
soc_manager = SOCManager()
