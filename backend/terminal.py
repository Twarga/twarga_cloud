"""
Terminal Manager for Twarga Cloud MVP
Handles web terminal access to VMs via ttyd
"""

import os
import subprocess
import logging
import secrets
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import VM, Event, User

logger = logging.getLogger(__name__)

class TerminalSession:
    """Represents an active terminal session"""
    
    def __init__(self, vm_id: int, user_id: int, port: int, token: str, process: subprocess.Popen):
        self.vm_id = vm_id
        self.user_id = user_id
        self.port = port
        self.token = token
        self.process = process
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.session_id = secrets.token_urlsafe(16)
    
    def is_alive(self) -> bool:
        """Check if ttyd process is still running"""
        return self.process.poll() is None
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired due to inactivity"""
        if not self.is_alive():
            return True
        elapsed = datetime.utcnow() - self.last_activity
        return elapsed > timedelta(minutes=timeout_minutes)
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "vm_id": self.vm_id,
            "user_id": self.user_id,
            "port": self.port,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_alive": self.is_alive()
        }


class TerminalManager:
    """
    Terminal Manager for handling web-based terminal access to VMs via ttyd
    """
    
    def __init__(self, base_port: int = 7681, vms_base_dir: str = "vms"):
        """
        Initialize Terminal Manager
        
        Args:
            base_port: Starting port for ttyd instances (default: 7681)
            vms_base_dir: Base directory for VM storage
        """
        self.base_port = base_port
        self.vms_base_dir = Path(vms_base_dir)
        self.sessions: Dict[int, TerminalSession] = {}  # vm_id -> session
        self.port_counter = base_port
        self.session_timeout_minutes = 30
        
        logger.info("Terminal Manager initialized")
    
    def _get_next_port(self) -> int:
        """Get next available port for ttyd"""
        # Simple port allocation - in production, should check if port is actually free
        used_ports = {session.port for session in self.sessions.values()}
        
        while self.port_counter in used_ports:
            self.port_counter += 1
            if self.port_counter > self.base_port + 1000:
                self.port_counter = self.base_port
        
        port = self.port_counter
        self.port_counter += 1
        return port
    
    def _get_vm_ssh_command(self, vm_dir: Path) -> Optional[str]:
        """
        Get SSH command for connecting to VM
        
        Args:
            vm_dir: VM directory path
            
        Returns:
            SSH command string or None if VM not accessible
        """
        try:
            # Use vagrant ssh command which handles SSH config automatically
            vagrant_path = str(vm_dir.absolute())
            ssh_command = f"cd {vagrant_path} && vagrant ssh"
            return ssh_command
            
        except Exception as e:
            logger.error(f"Exception getting SSH command: {e}")
            return None
    
    def start_terminal_session(
        self, 
        db: Session, 
        vm: VM, 
        user: User,
        vm_dir: Path
    ) -> Optional[TerminalSession]:
        """
        Start a new terminal session for a VM
        
        Args:
            db: Database session
            vm: VM object
            user: User object
            vm_dir: VM directory path
            
        Returns:
            TerminalSession object or None if failed
        """
        try:
            # Check if VM is running
            if vm.status != "running":
                logger.warning(f"Cannot start terminal for VM {vm.name} - VM not running (status: {vm.status})")
                self._log_terminal_event(
                    db, user, vm, "warning",
                    f"Failed to start terminal for VM {vm.name} - VM not running"
                )
                return None
            
            # Check if session already exists for this VM
            if vm.id in self.sessions:
                existing_session = self.sessions[vm.id]
                if existing_session.is_alive():
                    logger.info(f"Reusing existing terminal session for VM {vm.name}")
                    existing_session.update_activity()
                    self._log_terminal_event(
                        db, user, vm, "info",
                        f"Reconnected to existing terminal session for VM {vm.name}"
                    )
                    return existing_session
                else:
                    # Clean up dead session
                    logger.info(f"Cleaning up dead session for VM {vm.name}")
                    self.stop_terminal_session(db, vm.id, user)
            
            # Check if ttyd is installed
            if not self._check_ttyd_installed():
                logger.error("ttyd is not installed on the system")
                self._log_terminal_event(
                    db, user, vm, "critical",
                    "Failed to start terminal - ttyd not installed"
                )
                return None
            
            # Get SSH command
            ssh_command = self._get_vm_ssh_command(vm_dir)
            if not ssh_command:
                logger.error(f"Failed to get SSH command for VM {vm.name}")
                self._log_terminal_event(
                    db, user, vm, "critical",
                    f"Failed to start terminal for VM {vm.name} - SSH command unavailable"
                )
                return None
            
            # Generate secure token for this session
            token = secrets.token_urlsafe(32)
            
            # Get port for this session
            port = self._get_next_port()
            
            # Start ttyd process
            # ttyd options:
            # -p: port
            # -c: credential (username:password format, we use token as password)
            # -t: terminal type
            # -W: writable (allow input)
            # -O: check origin (disabled for local development)
            ttyd_command = [
                'ttyd',
                '-p', str(port),
                '-c', f'user:{token}',
                '-t', 'titleFixed=Terminal - ' + vm.name,
                '-W',
                'bash', '-c', ssh_command
            ]
            
            logger.info(f"Starting ttyd on port {port} for VM {vm.name}")
            
            # Start ttyd process
            process = subprocess.Popen(
                ttyd_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL
            )
            
            # Create session object
            session = TerminalSession(
                vm_id=vm.id,
                user_id=user.id,
                port=port,
                token=token,
                process=process
            )
            
            # Store session
            self.sessions[vm.id] = session
            
            # Log event
            self._log_terminal_event(
                db, user, vm, "info",
                f"Started terminal session for VM {vm.name} on port {port}",
                details={
                    "session_id": session.session_id,
                    "port": port
                }
            )
            
            logger.info(f"Terminal session started for VM {vm.name} on port {port}")
            return session
            
        except Exception as e:
            logger.error(f"Exception starting terminal session for VM {vm.name}: {e}")
            self._log_terminal_event(
                db, user, vm, "critical",
                f"Exception starting terminal session: {str(e)}"
            )
            return None
    
    def stop_terminal_session(self, db: Session, vm_id: int, user: User) -> bool:
        """
        Stop terminal session for a VM
        
        Args:
            db: Database session
            vm_id: VM ID
            user: User object
            
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if vm_id not in self.sessions:
                logger.warning(f"No terminal session found for VM {vm_id}")
                return False
            
            session = self.sessions[vm_id]
            
            # Terminate ttyd process
            if session.is_alive():
                session.process.terminate()
                try:
                    session.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    session.process.kill()
                    session.process.wait()
            
            # Remove session
            del self.sessions[vm_id]
            
            # Log event
            vm = db.query(VM).filter(VM.id == vm_id).first()
            if vm:
                self._log_terminal_event(
                    db, user, vm, "info",
                    f"Stopped terminal session for VM {vm.name}",
                    details={"session_id": session.session_id}
                )
            
            logger.info(f"Terminal session stopped for VM {vm_id}")
            return True
            
        except Exception as e:
            logger.error(f"Exception stopping terminal session for VM {vm_id}: {e}")
            return False
    
    def get_terminal_session(self, vm_id: int) -> Optional[TerminalSession]:
        """
        Get terminal session for a VM
        
        Args:
            vm_id: VM ID
            
        Returns:
            TerminalSession object or None if not found
        """
        return self.sessions.get(vm_id)
    
    def verify_session_access(self, vm_id: int, user: User, token: str) -> bool:
        """
        Verify user has access to terminal session
        
        Args:
            vm_id: VM ID
            user: User object
            token: Session token
            
        Returns:
            True if access granted, False otherwise
        """
        session = self.sessions.get(vm_id)
        if not session:
            return False
        
        # Check if user owns the VM or is admin
        if session.user_id != user.id and not user.is_admin:
            logger.warning(f"User {user.username} attempted to access terminal session for VM {vm_id} without permission")
            return False
        
        # Check token (optional - for additional security)
        if token and session.token != token:
            logger.warning(f"Invalid token provided for terminal session VM {vm_id}")
            return False
        
        # Update activity
        session.update_activity()
        
        return True
    
    def list_active_sessions(self, user: User = None) -> List[Dict]:
        """
        List active terminal sessions
        
        Args:
            user: Optional user to filter sessions (None for admin view all)
            
        Returns:
            List of session dictionaries
        """
        sessions = []
        for session in self.sessions.values():
            if user and not user.is_admin and session.user_id != user.id:
                continue
            sessions.append(session.to_dict())
        return sessions
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Clean up expired or dead terminal sessions
        
        Args:
            db: Database session
            
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        
        for vm_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout_minutes):
                expired_sessions.append(vm_id)
        
        cleaned = 0
        for vm_id in expired_sessions:
            session = self.sessions[vm_id]
            user = db.query(User).filter(User.id == session.user_id).first()
            if user and self.stop_terminal_session(db, vm_id, user):
                cleaned += 1
                logger.info(f"Cleaned up expired session for VM {vm_id}")
        
        return cleaned
    
    def stop_all_sessions(self, db: Session) -> int:
        """
        Stop all terminal sessions (emergency stop)
        
        Args:
            db: Database session
            
        Returns:
            Number of sessions stopped
        """
        vm_ids = list(self.sessions.keys())
        stopped = 0
        
        for vm_id in vm_ids:
            session = self.sessions[vm_id]
            user = db.query(User).filter(User.id == session.user_id).first()
            if user and self.stop_terminal_session(db, vm_id, user):
                stopped += 1
        
        logger.warning(f"Emergency stop: {stopped} terminal sessions stopped")
        return stopped
    
    def _check_ttyd_installed(self) -> bool:
        """Check if ttyd is installed on the system"""
        try:
            result = subprocess.run(
                ['which', 'ttyd'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _log_terminal_event(
        self, 
        db: Session, 
        user: User, 
        vm: VM, 
        severity: str, 
        message: str,
        details: Dict = None
    ):
        """
        Log terminal-related event
        
        Args:
            db: Database session
            user: User object
            vm: VM object
            severity: Event severity (info, warning, critical)
            message: Event message
            details: Optional additional details
        """
        try:
            event = Event(
                type="terminal",
                severity=severity,
                message=message,
                user_id=user.id,
                vm_id=vm.id,
                details=details or {}
            )
            db.add(event)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log terminal event: {e}")
            db.rollback()


# Global terminal manager instance
terminal_manager = TerminalManager()
