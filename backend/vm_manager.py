"""
VM Manager for Twarga Cloud MVP
Handles VM creation, destruction, and lifecycle management via Vagrant
"""

import os
import json
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from .models import VM, Event, User

logger = logging.getLogger(__name__)

class VMManager:
    """
    VM Manager for handling Vagrant-based VM lifecycle operations
    """
    
    def __init__(self, vms_base_dir: str = "vms"):
        """
        Initialize VM Manager
        
        Args:
            vms_base_dir: Base directory for VM storage
        """
        self.vms_base_dir = Path(vms_base_dir)
        self.vms_base_dir.mkdir(exist_ok=True)
        
    def _get_vm_dir(self, vm_name: str, user_id: int) -> Path:
        """Get VM directory path"""
        return self.vms_base_dir / f"user{user_id}-{vm_name}"
    
    def _generate_vagrantfile(self, vm_config: Dict) -> str:
        """
        Generate Vagrantfile content based on VM configuration
        
        Args:
            vm_config: Dict with keys: name, os_type, ram_mb, disk_gb, cpu_cores
            
        Returns:
            Vagrantfile content as string
        """
        os_boxes = {
            "ubuntu": "ubuntu/focal64",
            "ubuntu20": "ubuntu/focal64",
            "ubuntu22": "ubuntu/jammy64",
            "centos": "centos/7",
            "centos7": "centos/7",
            "centos8": "centos/stream8",
            "debian": "debian/bullseye64",
            "debian11": "debian/bullseye64",
            "debian10": "debian/buster64",
        }
        
        box = os_boxes.get(vm_config['os_type'].lower(), "ubuntu/focal64")
        
        vagrantfile = f'''# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "{box}"
  config.vm.hostname = "{vm_config['name']}"
  
  # Provider-specific configuration
  config.vm.provider "virtualbox" do |vb|
    vb.name = "{vm_config['name']}"
    vb.memory = {vm_config['ram_mb']}
    vb.cpus = {vm_config['cpu_cores']}
  end
  
  config.vm.provider "libvirt" do |lv|
    lv.memory = {vm_config['ram_mb']}
    lv.cpus = {vm_config['cpu_cores']}
  end
  
  # Network configuration - private network with DHCP
  config.vm.network "private_network", type: "dhcp"
  
  # Sync folder disabled for minimal setup
  config.vm.synced_folder ".", "/vagrant", disabled: true
  
  # Basic provisioning
  config.vm.provision "shell", inline: <<-SHELL
    echo "VM {vm_config['name']} provisioned successfully"
    echo "Hostname: $(hostname)"
    echo "IP Address: $(hostname -I)"
  SHELL
end
'''
        return vagrantfile
    
    def _create_vm_info_file(self, vm_dir: Path, vm_config: Dict):
        """Create .vm_info JSON file with VM metadata"""
        vm_info = {
            "name": vm_config['name'],
            "os_type": vm_config['os_type'],
            "ram_mb": vm_config['ram_mb'],
            "disk_gb": vm_config['disk_gb'],
            "cpu_cores": vm_config['cpu_cores'],
            "status": "pending",
            "ip_address": None,
            "created_at": datetime.utcnow().isoformat(),
            "uptime_seconds": 0
        }
        
        info_file = vm_dir / ".vm_info"
        with open(info_file, 'w') as f:
            json.dump(vm_info, f, indent=2)
    
    def _update_vm_info_file(self, vm_dir: Path, updates: Dict):
        """Update .vm_info JSON file"""
        info_file = vm_dir / ".vm_info"
        
        if info_file.exists():
            with open(info_file, 'r') as f:
                vm_info = json.load(f)
        else:
            vm_info = {}
        
        vm_info.update(updates)
        vm_info['updated_at'] = datetime.utcnow().isoformat()
        
        with open(info_file, 'w') as f:
            json.dump(vm_info, f, indent=2)
    
    def _run_vagrant_command(self, vm_dir: Path, command: List[str], timeout: int = 300) -> tuple:
        """
        Run vagrant command in VM directory
        
        Args:
            vm_dir: VM directory path
            command: Vagrant command as list (e.g., ['up'], ['halt'])
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success: bool, output: str, error: str)
        """
        try:
            full_command = ['vagrant'] + command
            logger.info(f"Running command in {vm_dir}: {' '.join(full_command)}")
            
            result = subprocess.run(
                full_command,
                cwd=str(vm_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            if success:
                logger.info(f"Command successful: {' '.join(full_command)}")
            else:
                logger.error(f"Command failed: {' '.join(full_command)}, Error: {error}")
            
            return success, output, error
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Exception running command: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def create_vm(self, db: Session, vm: VM, user: User) -> tuple:
        """
        Create a new VM with Vagrant
        
        Args:
            db: Database session
            vm: VM database object
            user: User who owns the VM
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, user.id)
            
            # Check if VM directory already exists
            if vm_dir.exists():
                return False, f"VM directory already exists: {vm_dir}"
            
            # Create VM directory
            vm_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created VM directory: {vm_dir}")
            
            # Generate Vagrantfile
            vm_config = {
                'name': vm.name,
                'os_type': vm.os_type,
                'ram_mb': vm.ram_mb,
                'disk_gb': vm.disk_gb,
                'cpu_cores': vm.cpu_cores
            }
            
            vagrantfile_content = self._generate_vagrantfile(vm_config)
            vagrantfile_path = vm_dir / "Vagrantfile"
            
            with open(vagrantfile_path, 'w') as f:
                f.write(vagrantfile_content)
            logger.info(f"Created Vagrantfile: {vagrantfile_path}")
            
            # Create .vm_info file
            self._create_vm_info_file(vm_dir, vm_config)
            
            # Update VM status to pending
            vm.status = "pending"
            db.commit()
            
            # Log event
            event = Event(
                type="vm",
                severity="info",
                message=f"User '{user.username}' initiated VM creation: {vm.name}",
                user_id=user.id,
                vm_id=vm.id,
                details=vm_config
            )
            db.add(event)
            db.commit()
            
            # Start vagrant up
            logger.info(f"Starting vagrant up for VM: {vm.name}")
            success, output, error = self._run_vagrant_command(vm_dir, ['up'])
            
            if success:
                # Get VM IP and update database
                ip_address = self._get_vm_ip(vm_dir)
                vm.ip_address = ip_address
                vm.status = "running"
                
                # Update .vm_info file
                self._update_vm_info_file(vm_dir, {
                    "status": "running",
                    "ip_address": ip_address
                })
                
                db.commit()
                
                # Log success event
                event = Event(
                    type="vm",
                    severity="info",
                    message=f"VM '{vm.name}' created successfully with IP {ip_address}",
                    user_id=user.id,
                    vm_id=vm.id,
                    details={"ip": ip_address, "status": "running"}
                )
                db.add(event)
                db.commit()
                
                logger.info(f"VM {vm.name} created successfully with IP {ip_address}")
                return True, f"VM created successfully with IP {ip_address}"
            else:
                # Update status to failed
                vm.status = "failed"
                db.commit()
                
                # Log failure event
                event = Event(
                    type="vm",
                    severity="critical",
                    message=f"Failed to create VM '{vm.name}': {error}",
                    user_id=user.id,
                    vm_id=vm.id,
                    details={"error": error}
                )
                db.add(event)
                db.commit()
                
                logger.error(f"Failed to create VM {vm.name}: {error}")
                return False, f"Failed to create VM: {error}"
                
        except Exception as e:
            error_msg = f"Exception creating VM: {str(e)}"
            logger.error(error_msg)
            
            # Update status to failed
            if vm:
                vm.status = "failed"
                db.commit()
            
            return False, error_msg
    
    def start_vm(self, db: Session, vm: VM, user: User) -> tuple:
        """
        Start a stopped VM
        
        Args:
            db: Database session
            vm: VM database object
            user: User who owns the VM
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, user.id)
            
            if not vm_dir.exists():
                return False, f"VM directory not found: {vm_dir}"
            
            logger.info(f"Starting VM: {vm.name}")
            success, output, error = self._run_vagrant_command(vm_dir, ['up'])
            
            if success:
                ip_address = self._get_vm_ip(vm_dir)
                vm.ip_address = ip_address
                vm.status = "running"
                
                self._update_vm_info_file(vm_dir, {
                    "status": "running",
                    "ip_address": ip_address
                })
                
                db.commit()
                
                event = Event(
                    type="vm",
                    severity="info",
                    message=f"VM '{vm.name}' started successfully",
                    user_id=user.id,
                    vm_id=vm.id
                )
                db.add(event)
                db.commit()
                
                logger.info(f"VM {vm.name} started successfully")
                return True, "VM started successfully"
            else:
                logger.error(f"Failed to start VM {vm.name}: {error}")
                return False, f"Failed to start VM: {error}"
                
        except Exception as e:
            error_msg = f"Exception starting VM: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def stop_vm(self, db: Session, vm: VM, user: User) -> tuple:
        """
        Stop a running VM
        
        Args:
            db: Database session
            vm: VM database object
            user: User who owns the VM
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, user.id)
            
            if not vm_dir.exists():
                return False, f"VM directory not found: {vm_dir}"
            
            logger.info(f"Stopping VM: {vm.name}")
            success, output, error = self._run_vagrant_command(vm_dir, ['halt'])
            
            if success:
                vm.status = "stopped"
                
                self._update_vm_info_file(vm_dir, {
                    "status": "stopped"
                })
                
                db.commit()
                
                event = Event(
                    type="vm",
                    severity="info",
                    message=f"VM '{vm.name}' stopped successfully",
                    user_id=user.id,
                    vm_id=vm.id
                )
                db.add(event)
                db.commit()
                
                logger.info(f"VM {vm.name} stopped successfully")
                return True, "VM stopped successfully"
            else:
                logger.error(f"Failed to stop VM {vm.name}: {error}")
                return False, f"Failed to stop VM: {error}"
                
        except Exception as e:
            error_msg = f"Exception stopping VM: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def destroy_vm(self, db: Session, vm: VM, user: User) -> tuple:
        """
        Destroy a VM and remove its directory
        
        Args:
            db: Database session
            vm: VM database object
            user: User who owns the VM
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, user.id)
            
            if not vm_dir.exists():
                logger.warning(f"VM directory not found: {vm_dir}, removing from database only")
                
                # Log event
                event = Event(
                    type="vm",
                    severity="warning",
                    message=f"VM '{vm.name}' directory not found, removing from database",
                    user_id=user.id,
                    vm_id=vm.id
                )
                db.add(event)
                
                # Delete VM from database
                db.delete(vm)
                db.commit()
                
                return True, "VM removed from database (directory not found)"
            
            logger.info(f"Destroying VM: {vm.name}")
            success, output, error = self._run_vagrant_command(vm_dir, ['destroy', '-f'])
            
            # Remove VM directory even if vagrant destroy fails
            try:
                shutil.rmtree(vm_dir)
                logger.info(f"Removed VM directory: {vm_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove VM directory: {e}")
            
            # Log event
            event = Event(
                type="vm",
                severity="info",
                message=f"VM '{vm.name}' destroyed successfully",
                user_id=user.id,
                vm_id=vm.id
            )
            db.add(event)
            
            # Delete VM from database
            db.delete(vm)
            db.commit()
            
            logger.info(f"VM {vm.name} destroyed successfully")
            return True, "VM destroyed successfully"
            
        except Exception as e:
            error_msg = f"Exception destroying VM: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_vm_status(self, vm_dir: Path) -> str:
        """
        Get VM status from vagrant status command
        
        Args:
            vm_dir: VM directory path
            
        Returns:
            VM status string (running, stopped, not_created, unknown)
        """
        try:
            if not vm_dir.exists():
                return "not_created"
            
            success, output, error = self._run_vagrant_command(vm_dir, ['status'], timeout=30)
            
            if not success:
                return "unknown"
            
            # Parse vagrant status output
            if "running" in output.lower():
                return "running"
            elif "poweroff" in output.lower() or "stopped" in output.lower():
                return "stopped"
            elif "not created" in output.lower():
                return "not_created"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Exception getting VM status: {e}")
            return "unknown"
    
    def _get_vm_ip(self, vm_dir: Path) -> Optional[str]:
        """
        Get VM IP address from vagrant ssh-config
        
        Args:
            vm_dir: VM directory path
            
        Returns:
            IP address string or None if not found
        """
        try:
            success, output, error = self._run_vagrant_command(
                vm_dir, ['ssh-config'], timeout=30
            )
            
            if not success:
                return None
            
            # Parse ssh-config output to find HostName
            for line in output.split('\n'):
                if 'HostName' in line:
                    ip = line.split()[-1]
                    return ip
            
            return None
            
        except Exception as e:
            logger.error(f"Exception getting VM IP: {e}")
            return None
    
    def update_vm_status(self, db: Session, vm: VM, user: User) -> bool:
        """
        Update VM status from Vagrant
        
        Args:
            db: Database session
            vm: VM database object
            user: User who owns the VM
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, user.id)
            status = self.get_vm_status(vm_dir)
            
            if status != vm.status:
                vm.status = status
                db.commit()
                
                self._update_vm_info_file(vm_dir, {
                    "status": status
                })
                
                logger.info(f"Updated VM {vm.name} status to {status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Exception updating VM status: {e}")
            return False
    
    def list_user_vms(self, db: Session, user_id: int) -> List[VM]:
        """
        List all VMs for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of VM objects
        """
        return db.query(VM).filter(VM.owner_id == user_id).all()
    
    def get_vm_info(self, vm_dir: Path) -> Optional[Dict]:
        """
        Read .vm_info JSON file
        
        Args:
            vm_dir: VM directory path
            
        Returns:
            VM info dict or None if not found
        """
        try:
            info_file = vm_dir / ".vm_info"
            
            if not info_file.exists():
                return None
            
            with open(info_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Exception reading VM info: {e}")
            return None


# Global VM manager instance
vm_manager = VMManager()
