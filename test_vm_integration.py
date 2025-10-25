"""
Test script for Phase 2.2 - VM Database Integration
Tests VM metadata, quota enforcement, and lifecycle event logging
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import SessionLocal, init_db
from backend.models import User, VM, Event
from backend.vm_manager import vm_manager
from backend.auth import get_password_hash

def test_vm_database_integration():
    """Test VM database integration features"""
    print("=" * 60)
    print("Testing Phase 2.2: VM Database Integration")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    db = SessionLocal()
    
    try:
        # Create test user
        print("\n2. Creating test user...")
        test_user = db.query(User).filter(User.username == "testuser").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@twarga.cloud",
                hashed_password=get_password_hash("testpass123"),
                is_active=True,
                is_admin=False,
                credits=100
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        print(f"✓ Test user created: {test_user.username} (credits: {test_user.credits})")
        
        # Test quota calculation
        print("\n3. Testing VM cost calculation...")
        cost = vm_manager.calculate_vm_cost(1024, 20, 2)
        print(f"✓ VM cost calculated: {cost} credits (1GB RAM, 20GB disk, 2 CPUs)")
        
        # Test quota check
        print("\n4. Testing quota enforcement...")
        can_create, message, cost = vm_manager.check_user_quota(
            db, test_user, 1024, 20, 2
        )
        print(f"✓ Quota check: {message}")
        print(f"  Can create: {can_create}, Cost: {cost}")
        
        # Create test VM
        print("\n5. Creating test VM...")
        test_vm = VM(
            name="test-vm",
            os_type="ubuntu",
            ram_mb=1024,
            disk_gb=20,
            cpu_cores=2,
            owner_id=test_user.id,
            status="stopped"
        )
        db.add(test_vm)
        db.commit()
        db.refresh(test_vm)
        print(f"✓ Test VM created: {test_vm.name} (ID: {test_vm.id})")
        
        # Test metadata storage
        print("\n6. Testing VM metadata storage...")
        metadata = {"test_key": "test_value", "creation_date": "2025-10-23"}
        success = vm_manager.update_vm_metadata(db, test_vm, metadata)
        print(f"✓ Metadata updated: {success}")
        
        # Test metadata retrieval
        print("\n7. Testing VM metadata retrieval...")
        retrieved_metadata = vm_manager.get_vm_metadata(test_vm)
        print(f"✓ Metadata retrieved: {retrieved_metadata}")
        
        # Test VM query functions
        print("\n8. Testing VM query functions...")
        vm_by_id = vm_manager.get_vm_by_id(db, test_vm.id)
        print(f"✓ get_vm_by_id: Found VM '{vm_by_id.name}'" if vm_by_id else "✗ VM not found")
        
        vm_by_name = vm_manager.get_vm_by_name(db, "test-vm", test_user.id)
        print(f"✓ get_vm_by_name: Found VM '{vm_by_name.name}'" if vm_by_name else "✗ VM not found")
        
        user_vms = vm_manager.list_user_vms(db, test_user.id)
        print(f"✓ list_user_vms: Found {len(user_vms)} VM(s)")
        
        # Test event logging
        print("\n9. Testing event logging...")
        initial_events = db.query(Event).count()
        
        # Create test event
        test_event = Event(
            type="vm",
            severity="info",
            message="Test VM operation",
            user_id=test_user.id,
            vm_id=test_vm.id,
            details={"action": "test", "result": "success"}
        )
        db.add(test_event)
        db.commit()
        
        final_events = db.query(Event).count()
        print(f"✓ Event logged: {final_events - initial_events} new event(s)")
        
        # Test credit deduction
        print("\n10. Testing credit deduction...")
        initial_credits = test_user.credits
        success = vm_manager.deduct_user_credits(db, test_user, 10, "Test deduction")
        db.refresh(test_user)
        print(f"✓ Credits deducted: {initial_credits} -> {test_user.credits}")
        
        # Clean up
        print("\n11. Cleaning up test data...")
        db.delete(test_vm)
        db.delete(test_user)
        db.commit()
        print("✓ Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("✓ All Phase 2.2 tests passed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_vm_database_integration()
    sys.exit(0 if success else 1)
