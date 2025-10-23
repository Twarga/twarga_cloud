#!/usr/bin/env python3
"""
Database Test Script for Twarga Cloud MVP
Tests database connectivity and CRUD operations for all models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, get_db_session, check_db_connection, get_database_info
from backend.models import User, VM, Event, Metric
from backend.auth import get_password_hash
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test basic database connection"""
    logger.info("Testing database connection...")
    
    if check_db_connection():
        logger.info("✅ Database connection successful")
        return True
    else:
        logger.error("❌ Database connection failed")
        return False

def test_user_crud():
    """Test CRUD operations for User model"""
    logger.info("Testing User CRUD operations...")
    
    db = get_db_session()
    try:
        # Create a test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_admin=False,
            credits=50
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        logger.info(f"✅ Created test user: {test_user.username} (ID: {test_user.id})")
        
        # Read user
        retrieved_user = db.query(User).filter(User.username == "testuser").first()
        if retrieved_user:
            logger.info(f"✅ Retrieved test user: {retrieved_user.username}")
        else:
            logger.error("❌ Failed to retrieve test user")
            return False
        
        # Update user
        retrieved_user.credits = 75
        db.commit()
        logger.info(f"✅ Updated user credits to: {retrieved_user.credits}")
        
        # Delete user
        db.delete(retrieved_user)
        db.commit()
        logger.info("✅ Deleted test user")
        
        return True
    except Exception as e:
        logger.error(f"❌ User CRUD test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_vm_crud():
    """Test CRUD operations for VM model"""
    logger.info("Testing VM CRUD operations...")
    
    db = get_db_session()
    try:
        # First, create a user to associate with the VM
        test_user = User(
            username="vmowner",
            email="vmowner@example.com",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_admin=False,
            credits=100
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create a test VM
        test_vm = VM(
            name="test-vm",
            os_type="ubuntu",
            ram_mb=1024,
            disk_gb=20,
            cpu_cores=1,
            status="stopped",
            owner_id=test_user.id,
            vm_metadata={"version": "20.04", "purpose": "testing"}
        )
        db.add(test_vm)
        db.commit()
        db.refresh(test_vm)
        logger.info(f"✅ Created test VM: {test_vm.name} (ID: {test_vm.id})")
        
        # Read VM
        retrieved_vm = db.query(VM).filter(VM.name == "test-vm").first()
        if retrieved_vm:
            logger.info(f"✅ Retrieved test VM: {retrieved_vm.name}, Status: {retrieved_vm.status}")
        else:
            logger.error("❌ Failed to retrieve test VM")
            return False
        
        # Update VM
        retrieved_vm.status = "running"
        retrieved_vm.ip_address = "192.168.1.100"
        db.commit()
        logger.info(f"✅ Updated VM status to: {retrieved_vm.status}, IP: {retrieved_vm.ip_address}")
        
        # Delete VM
        db.delete(retrieved_vm)
        db.commit()
        logger.info("✅ Deleted test VM")
        
        # Clean up test user
        db.delete(test_user)
        db.commit()
        
        return True
    except Exception as e:
        logger.error(f"❌ VM CRUD test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_event_crud():
    """Test CRUD operations for Event model"""
    logger.info("Testing Event CRUD operations...")
    
    db = get_db_session()
    try:
        # Create a test user for the event
        test_user = User(
            username="eventuser",
            email="eventuser@example.com",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_admin=False,
            credits=100
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create a test VM for the event
        test_vm = VM(
            name="event-vm",
            os_type="centos",
            ram_mb=2048,
            disk_gb=30,
            cpu_cores=2,
            status="running",
            owner_id=test_user.id
        )
        db.add(test_vm)
        db.commit()
        db.refresh(test_vm)
        
        # Create a test event
        test_event = Event(
            type="vm",
            severity="info",
            message="VM started successfully",
            details={"action": "start", "duration": "5s"},
            user_id=test_user.id,
            vm_id=test_vm.id
        )
        db.add(test_event)
        db.commit()
        db.refresh(test_event)
        logger.info(f"✅ Created test event: {test_event.message} (ID: {test_event.id})")
        
        # Read event
        retrieved_event = db.query(Event).filter(Event.message == "VM started successfully").first()
        if retrieved_event:
            logger.info(f"✅ Retrieved test event: {retrieved_event.message}, Type: {retrieved_event.type}")
        else:
            logger.error("❌ Failed to retrieve test event")
            return False
        
        # Update event
        retrieved_event.severity = "warning"
        db.commit()
        logger.info(f"✅ Updated event severity to: {retrieved_event.severity}")
        
        # Delete event
        db.delete(retrieved_event)
        db.commit()
        logger.info("✅ Deleted test event")
        
        # Clean up test VM and user
        db.delete(test_vm)
        db.delete(test_user)
        db.commit()
        
        return True
    except Exception as e:
        logger.error(f"❌ Event CRUD test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_metric_crud():
    """Test CRUD operations for Metric model"""
    logger.info("Testing Metric CRUD operations...")
    
    db = get_db_session()
    try:
        # Create a test user and VM for the metric
        test_user = User(
            username="metricuser",
            email="metricuser@example.com",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_admin=False,
            credits=100
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        test_vm = VM(
            name="metric-vm",
            os_type="debian",
            ram_mb=4096,
            disk_gb=40,
            cpu_cores=4,
            status="running",
            owner_id=test_user.id
        )
        db.add(test_vm)
        db.commit()
        db.refresh(test_vm)
        
        # Create test metrics
        cpu_metric = Metric(
            name="cpu_usage",
            value=45.5,
            unit="%",
            vm_id=test_vm.id
        )
        db.add(cpu_metric)
        
        memory_metric = Metric(
            name="memory_usage",
            value=2048,
            unit="MB",
            vm_id=test_vm.id
        )
        db.add(memory_metric)
        db.commit()
        db.refresh(cpu_metric)
        db.refresh(memory_metric)
        logger.info(f"✅ Created test metrics: CPU={cpu_metric.value}{cpu_metric.unit}, Memory={memory_metric.value}{memory_metric.unit}")
        
        # Read metrics
        retrieved_metrics = db.query(Metric).filter(Metric.vm_id == test_vm.id).all()
        if len(retrieved_metrics) == 2:
            logger.info(f"✅ Retrieved {len(retrieved_metrics)} metrics for VM")
        else:
            logger.error(f"❌ Expected 2 metrics, got {len(retrieved_metrics)}")
            return False
        
        # Delete metrics
        for metric in retrieved_metrics:
            db.delete(metric)
        db.commit()
        logger.info("✅ Deleted test metrics")
        
        # Clean up test VM and user
        db.delete(test_vm)
        db.delete(test_user)
        db.commit()
        
        return True
    except Exception as e:
        logger.error(f"❌ Metric CRUD test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_database_info():
    """Test database info function"""
    logger.info("Testing database info function...")
    
    try:
        info = get_database_info()
        logger.info(f"✅ Database info: {info}")
        return True
    except Exception as e:
        logger.error(f"❌ Database info test failed: {e}")
        return False

def main():
    """Run all database tests"""
    logger.info("🚀 Starting database tests...")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    
    # Run tests
    tests = [
        test_database_connection,
        test_user_crud,
        test_vm_crud,
        test_event_crud,
        test_metric_crud,
        test_database_info
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        logger.info("-" * 50)
    
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All database tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)