"""
Monitoring module for Twarga Cloud MVP
Handles host and VM metrics collection using psutil
"""

import psutil
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from .models import Metric, VM, Event
import time

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    System monitoring class for collecting host and VM metrics
    Uses psutil to collect real-time system performance data
    """
    
    def __init__(self, vms_base_dir: str = "vms"):
        """Initialize the system monitor"""
        self.last_net_io = None
        self.last_net_io_time = None
        self.vms_base_dir = Path(vms_base_dir)
        logger.info("SystemMonitor initialized")
    
    def get_host_metrics(self) -> Dict[str, float]:
        """
        Collect host system metrics (CPU, RAM, disk, network)
        Returns dictionary with current system metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            memory_available_gb = memory.available / (1024 ** 3)
            
            # Swap memory
            swap = psutil.swap_memory()
            swap_percent = swap.percent
            swap_used_gb = swap.used / (1024 ** 3)
            swap_total_gb = swap.total / (1024 ** 3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            disk_free_gb = disk.free / (1024 ** 3)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / (1024 ** 2)
            net_recv_mb = net_io.bytes_recv / (1024 ** 2)
            
            # Calculate network speed if we have previous data
            net_send_speed_mbps = 0.0
            net_recv_speed_mbps = 0.0
            if self.last_net_io and self.last_net_io_time:
                time_diff = time.time() - self.last_net_io_time
                if time_diff > 0:
                    sent_diff = net_io.bytes_sent - self.last_net_io.bytes_sent
                    recv_diff = net_io.bytes_recv - self.last_net_io.bytes_recv
                    net_send_speed_mbps = (sent_diff / time_diff) / (1024 ** 2)
                    net_recv_speed_mbps = (recv_diff / time_diff) / (1024 ** 2)
            
            self.last_net_io = net_io
            self.last_net_io_time = time.time()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 ** 2) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 ** 2) if disk_io else 0
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            metrics = {
                # CPU metrics
                "cpu_percent": round(cpu_percent, 2),
                "cpu_count": cpu_count,
                "cpu_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else 0,
                
                # Memory metrics
                "memory_percent": round(memory_percent, 2),
                "memory_used_gb": round(memory_used_gb, 2),
                "memory_total_gb": round(memory_total_gb, 2),
                "memory_available_gb": round(memory_available_gb, 2),
                
                # Swap metrics
                "swap_percent": round(swap_percent, 2),
                "swap_used_gb": round(swap_used_gb, 2),
                "swap_total_gb": round(swap_total_gb, 2),
                
                # Disk metrics
                "disk_percent": round(disk_percent, 2),
                "disk_used_gb": round(disk_used_gb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "disk_free_gb": round(disk_free_gb, 2),
                
                # Network metrics
                "net_sent_mb": round(net_sent_mb, 2),
                "net_recv_mb": round(net_recv_mb, 2),
                "net_send_speed_mbps": round(net_send_speed_mbps, 2),
                "net_recv_speed_mbps": round(net_recv_speed_mbps, 2),
                
                # Disk I/O metrics
                "disk_read_mb": round(disk_read_mb, 2),
                "disk_write_mb": round(disk_write_mb, 2),
                
                # System uptime
                "uptime_seconds": int(uptime_seconds),
                "uptime_hours": round(uptime_seconds / 3600, 2),
                
                # Timestamp
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Collected host metrics: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting host metrics: {e}")
            return {}
    
    def _get_vm_dir(self, vm_name: str, user_id: int) -> Path:
        """Get VM directory path"""
        return self.vms_base_dir / f"user{user_id}-{vm_name}"
    
    def _load_vm_info(self, vm: VM) -> Optional[Dict]:
        """
        Load VM info from .vm_info file
        
        Args:
            vm: VM database object
            
        Returns:
            VM info dict or None if not found
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, vm.owner_id)
            info_file = vm_dir / ".vm_info"
            
            if not info_file.exists():
                logger.debug(f"VM info file not found for {vm.name}")
                return None
            
            with open(info_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Exception reading VM info for {vm.name}: {e}")
            return None
    
    def update_vm_resource_usage(self, vm: VM, cpu_percent: float, memory_percent: float, 
                                 disk_percent: float, network_rx_mb: float = 0.0, 
                                 network_tx_mb: float = 0.0) -> bool:
        """
        Update VM resource usage in .vm_info file
        
        Args:
            vm: VM database object
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            disk_percent: Disk usage percentage
            network_rx_mb: Network received in MB
            network_tx_mb: Network transmitted in MB
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vm_dir = self._get_vm_dir(vm.name, vm.owner_id)
            info_file = vm_dir / ".vm_info"
            
            if not info_file.exists():
                logger.warning(f"VM info file not found for {vm.name}")
                return False
            
            # Load existing info
            with open(info_file, 'r') as f:
                vm_info = json.load(f)
            
            # Update resource usage
            vm_info["cpu_percent"] = round(cpu_percent, 2)
            vm_info["memory_percent"] = round(memory_percent, 2)
            vm_info["disk_percent"] = round(disk_percent, 2)
            vm_info["network_rx_mb"] = round(network_rx_mb, 2)
            vm_info["network_tx_mb"] = round(network_tx_mb, 2)
            vm_info["last_metrics_update"] = datetime.utcnow().isoformat()
            
            # Write back
            with open(info_file, 'w') as f:
                json.dump(vm_info, f, indent=2)
            
            logger.debug(f"Updated resource usage for VM {vm.name}")
            return True
            
        except Exception as e:
            logger.error(f"Exception updating VM resource usage for {vm.name}: {e}")
            return False
    
    def get_vm_metrics(self, vm: VM, vm_info: Optional[Dict] = None) -> Optional[Dict[str, float]]:
        """
        Collect per-VM resource usage metrics
        Reads from .vm_info file and calculates actual resource usage
        
        Args:
            vm: VM database object
            vm_info: Optional pre-loaded VM info dict (from .vm_info file)
        
        Returns:
            Dictionary with VM metrics or None if failed
        """
        try:
            # Load VM info from file if not provided
            if vm_info is None:
                vm_info = self._load_vm_info(vm)
            
            # Get actual resource usage if VM is running
            cpu_percent = 0.0
            memory_percent = 0.0
            disk_percent = 0.0
            network_rx_mb = 0.0
            network_tx_mb = 0.0
            
            if vm.status == "running":
                # Try to get actual metrics from .vm_info if loaded
                if vm_info:
                    cpu_percent = vm_info.get("cpu_percent", 15.0)
                    memory_percent = vm_info.get("memory_percent", 45.0)
                    disk_percent = vm_info.get("disk_percent", 30.0)
                    network_rx_mb = vm_info.get("network_rx_mb", 0.0)
                    network_tx_mb = vm_info.get("network_tx_mb", 0.0)
                else:
                    # Use simulated metrics for now
                    # In production, this would query libvirt/hypervisor for actual usage
                    cpu_percent = 15.0
                    memory_percent = 45.0
                    disk_percent = 30.0
            
            # Calculate memory and disk in absolute values
            memory_used_mb = (memory_percent / 100.0) * vm.ram_mb if memory_percent > 0 else 0
            disk_used_gb = (disk_percent / 100.0) * vm.disk_gb if disk_percent > 0 else 0
            
            metrics = {
                "vm_id": vm.id,
                "vm_name": vm.name,
                "vm_status": vm.status,
                "ip_address": vm.ip_address,
                
                # Resource allocation
                "ram_allocated_mb": vm.ram_mb,
                "disk_allocated_gb": vm.disk_gb,
                "cpu_allocated_cores": vm.cpu_cores,
                
                # Resource usage (percentage)
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "disk_percent": round(disk_percent, 2),
                
                # Resource usage (absolute)
                "memory_used_mb": round(memory_used_mb, 2),
                "memory_available_mb": round(vm.ram_mb - memory_used_mb, 2),
                "disk_used_gb": round(disk_used_gb, 2),
                "disk_available_gb": round(vm.disk_gb - disk_used_gb, 2),
                
                # Network metrics
                "network_rx_mb": round(network_rx_mb, 2),
                "network_tx_mb": round(network_tx_mb, 2),
                
                # Uptime
                "uptime_seconds": vm.uptime_seconds,
                "uptime_hours": round(vm.uptime_seconds / 3600, 2) if vm.uptime_seconds else 0,
                
                # Timestamp
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Collected metrics for VM {vm.name}: CPU={cpu_percent}%, Memory={memory_percent}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting VM metrics for VM {vm.id}: {e}")
            return None
    
    def store_host_metrics(self, db: Session, metrics: Dict[str, float]) -> bool:
        """
        Store host system metrics in the database
        Returns True if successful, False otherwise
        """
        try:
            # Store key metrics as individual records
            metrics_to_store = [
                ("host_cpu_percent", metrics.get("cpu_percent", 0), "%"),
                ("host_memory_percent", metrics.get("memory_percent", 0), "%"),
                ("host_disk_percent", metrics.get("disk_percent", 0), "%"),
                ("host_memory_used_gb", metrics.get("memory_used_gb", 0), "GB"),
                ("host_disk_used_gb", metrics.get("disk_used_gb", 0), "GB"),
                ("host_net_send_speed", metrics.get("net_send_speed_mbps", 0), "MB/s"),
                ("host_net_recv_speed", metrics.get("net_recv_speed_mbps", 0), "MB/s"),
            ]
            
            for name, value, unit in metrics_to_store:
                metric = Metric(
                    name=name,
                    value=value,
                    unit=unit,
                    vm_id=None  # Host metrics don't belong to a VM
                )
                db.add(metric)
            
            db.commit()
            logger.debug(f"Stored {len(metrics_to_store)} host metrics in database")
            return True
            
        except Exception as e:
            logger.error(f"Error storing host metrics: {e}")
            db.rollback()
            return False
    
    def store_vm_metrics(self, db: Session, vm: VM, metrics: Dict[str, float]) -> bool:
        """
        Store VM metrics in the database
        Returns True if successful, False otherwise
        """
        try:
            metrics_to_store = [
                ("vm_cpu_percent", metrics.get("cpu_percent", 0), "%"),
                ("vm_memory_percent", metrics.get("memory_percent", 0), "%"),
                ("vm_disk_percent", metrics.get("disk_percent", 0), "%"),
                ("vm_memory_used_mb", metrics.get("memory_used_mb", 0), "MB"),
                ("vm_disk_used_gb", metrics.get("disk_used_gb", 0), "GB"),
                ("vm_network_rx_mb", metrics.get("network_rx_mb", 0), "MB"),
                ("vm_network_tx_mb", metrics.get("network_tx_mb", 0), "MB"),
                ("vm_uptime", metrics.get("uptime_seconds", 0), "seconds"),
            ]
            
            for name, value, unit in metrics_to_store:
                metric = Metric(
                    name=name,
                    value=value,
                    unit=unit,
                    vm_id=vm.id
                )
                db.add(metric)
            
            db.commit()
            logger.debug(f"Stored {len(metrics_to_store)} metrics for VM {vm.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing VM metrics for VM {vm.id}: {e}")
            db.rollback()
            return False
    
    def get_historical_metrics(
        self, 
        db: Session, 
        metric_name: str, 
        vm_id: Optional[int] = None, 
        limit: int = 100
    ) -> List[Metric]:
        """
        Retrieve historical metrics from the database
        """
        try:
            query = db.query(Metric).filter(Metric.name == metric_name)
            
            if vm_id is not None:
                query = query.filter(Metric.vm_id == vm_id)
            else:
                query = query.filter(Metric.vm_id.is_(None))
            
            metrics = query.order_by(Metric.timestamp.desc()).limit(limit).all()
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving historical metrics: {e}")
            return []
    
    def check_resource_thresholds(self, db: Session, metrics: Dict[str, float]) -> List[str]:
        """
        Check if any resource usage exceeds thresholds and return alerts
        """
        alerts = []
        
        # CPU threshold: 90%
        if metrics.get("cpu_percent", 0) >= 90:
            alerts.append(f"⚠️ High CPU usage: {metrics['cpu_percent']}%")
            self._log_alert_event(db, "high_cpu", "warning", 
                                f"CPU usage at {metrics['cpu_percent']}%")
        
        # Memory threshold: 85%
        if metrics.get("memory_percent", 0) >= 85:
            alerts.append(f"⚠️ High memory usage: {metrics['memory_percent']}%")
            self._log_alert_event(db, "high_memory", "warning",
                                f"Memory usage at {metrics['memory_percent']}%")
        
        # Disk threshold: 90%
        if metrics.get("disk_percent", 0) >= 90:
            alerts.append(f"⚠️ High disk usage: {metrics['disk_percent']}%")
            self._log_alert_event(db, "high_disk", "warning",
                                f"Disk usage at {metrics['disk_percent']}%")
        
        # Swap threshold: 50%
        if metrics.get("swap_percent", 0) >= 50:
            alerts.append(f"⚠️ High swap usage: {metrics['swap_percent']}%")
            self._log_alert_event(db, "high_swap", "warning",
                                f"Swap usage at {metrics['swap_percent']}%")
        
        return alerts
    
    def _log_alert_event(self, db: Session, event_type: str, severity: str, message: str):
        """
        Log an alert event to the database
        """
        try:
            event = Event(
                type=f"system_{event_type}",
                severity=severity,
                message=message,
                details={"source": "system_monitor"}
            )
            db.add(event)
            db.commit()
            logger.warning(f"Alert logged: {message}")
        except Exception as e:
            logger.error(f"Error logging alert event: {e}")
            db.rollback()
    
    def collect_and_store_all_metrics(self, db: Session) -> Tuple[Dict[str, float], List[str]]:
        """
        Collect all system metrics and store them in the database
        Returns tuple of (metrics_dict, alerts_list)
        """
        # Collect host metrics
        metrics = self.get_host_metrics()
        
        if metrics:
            # Store host metrics
            self.store_host_metrics(db, metrics)
            
            # Check for alerts
            alerts = self.check_resource_thresholds(db, metrics)
            
            # Collect and store VM metrics
            vms = db.query(VM).filter(VM.status == "running").all()
            for vm in vms:
                vm_metrics = self.get_vm_metrics(vm)
                if vm_metrics:
                    self.store_vm_metrics(db, vm, vm_metrics)
            
            return metrics, alerts
        
        return {}, []
    
    def cleanup_old_metrics(self, db: Session, days_to_keep: int = 7) -> int:
        """
        Clean up metrics older than specified days
        Returns number of metrics deleted
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted = db.query(Metric).filter(
                Metric.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted} old metrics (older than {days_to_keep} days)")
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            db.rollback()
            return 0


# Create global monitor instance
system_monitor = SystemMonitor()
