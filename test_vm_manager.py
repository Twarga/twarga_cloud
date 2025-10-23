"""
Test script for VM Manager functionality
Tests VM creation, status monitoring, and Vagrantfile generation
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.vm_manager import VMManager
from backend.models import VM, User
from backend.database import get_db, init_db
from datetime import datetime

def test_vm_manager_initialization():
    """Test VM Manager initialization"""
    print("\n=== Testing VM Manager Initialization ===")
    vm_manager = VMManager()
    print(f"✓ VM Manager initialized with base directory: {vm_manager.vms_base_dir}")
    print(f"✓ VM base directory exists: {vm_manager.vms_base_dir.exists()}")
    return True

def test_vagrantfile_generation():
    """Test Vagrantfile generation for different OS types"""
    print("\n=== Testing Vagrantfile Generation ===")
    vm_manager = VMManager()
    
    test_configs = [
        {
            'name': 'test-ubuntu',
            'os_type': 'ubuntu',
            'ram_mb': 1024,
            'disk_gb': 20,
            'cpu_cores': 2
        },
        {
            'name': 'test-centos',
            'os_type': 'centos',
            'ram_mb': 2048,
            'disk_gb': 30,
            'cpu_cores': 4
        },
        {
            'name': 'test-debian',
            'os_type': 'debian',
            'ram_mb': 512,
            'disk_gb': 10,
            'cpu_cores': 1
        }
    ]
    
    for config in test_configs:
        vagrantfile = vm_manager._generate_vagrantfile(config)
        print(f"\n✓ Generated Vagrantfile for {config['os_type']}:")
        print(f"  - VM Name: {config['name']}")
        print(f"  - RAM: {config['ram_mb']} MB")
        print(f"  - CPU: {config['cpu_cores']} cores")
        print(f"  - Vagrantfile size: {len(vagrantfile)} characters")
        
        # Verify key elements are in the Vagrantfile
        assert config['name'] in vagrantfile
        assert str(config['ram_mb']) in vagrantfile
        assert str(config['cpu_cores']) in vagrantfile
        print(f"  - Content validation: PASSED")
    
    return True

def test_vm_directory_structure():
    """Test VM directory creation logic"""
    print("\n=== Testing VM Directory Structure ===")
    vm_manager = VMManager()
    
    test_cases = [
        {'vm_name': 'test-vm-1', 'user_id': 1, 'expected': 'user1-test-vm-1'},
        {'vm_name': 'web-server', 'user_id': 5, 'expected': 'user5-web-server'},
        {'vm_name': 'db-server', 'user_id': 10, 'expected': 'user10-db-server'},
    ]
    
    for case in test_cases:
        vm_dir = vm_manager._get_vm_dir(case['vm_name'], case['user_id'])
        dir_name = vm_dir.name
        print(f"✓ VM '{case['vm_name']}' for user {case['user_id']} -> {dir_name}")
        assert dir_name == case['expected'], f"Expected {case['expected']}, got {dir_name}"
    
    print("✓ All directory structure tests passed")
    return True

def test_vm_info_file_operations():
    """Test .vm_info file creation and updates"""
    print("\n=== Testing VM Info File Operations ===")
    vm_manager = VMManager()
    
    # Create a temporary test directory
    test_dir = Path("vms/test-vm-info")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Test creating vm_info file
        vm_config = {
            'name': 'test-vm',
            'os_type': 'ubuntu',
            'ram_mb': 1024,
            'disk_gb': 20,
            'cpu_cores': 2
        }
        
        vm_manager._create_vm_info_file(test_dir, vm_config)
        print("✓ Created .vm_info file")
        
        # Test reading vm_info file
        vm_info = vm_manager.get_vm_info(test_dir)
        assert vm_info is not None
        assert vm_info['name'] == 'test-vm'
        assert vm_info['ram_mb'] == 1024
        assert vm_info['status'] == 'pending'
        print(f"✓ Read .vm_info file: {vm_info}")
        
        # Test updating vm_info file
        vm_manager._update_vm_info_file(test_dir, {
            'status': 'running',
            'ip_address': '192.168.1.100'
        })
        print("✓ Updated .vm_info file")
        
        # Verify update
        updated_info = vm_manager.get_vm_info(test_dir)
        assert updated_info['status'] == 'running'
        assert updated_info['ip_address'] == '192.168.1.100'
        assert 'updated_at' in updated_info
        print(f"✓ Verified updates: status={updated_info['status']}, ip={updated_info['ip_address']}")
        
        return True
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("✓ Cleaned up test directory")

def test_vm_database_model():
    """Test VM database model integration"""
    print("\n=== Testing VM Database Model Integration ===")
    
    # Initialize database
    init_db()
    db = next(get_db())
    
    try:
        # Create a test user
        test_user = User(
            username="test_vm_user",
            email="test_vm@example.com",
            hashed_password="hashed_password_here",
            credits=100
        )
        db.add(test_user)
        db.commit()
        print(f"✓ Created test user: {test_user.username}")
        
        # Create a test VM
        test_vm = VM(
            name="test-vm-1",
            os_type="ubuntu",
            ram_mb=1024,
            disk_gb=20,
            cpu_cores=2,
            status="stopped",
            owner_id=test_user.id
        )
        db.add(test_vm)
        db.commit()
        print(f"✓ Created test VM: {test_vm.name} (ID: {test_vm.id})")
        
        # Test VM manager list_user_vms
        vm_manager = VMManager()
        user_vms = vm_manager.list_user_vms(db, test_user.id)
        assert len(user_vms) > 0
        assert user_vms[0].name == "test-vm-1"
        print(f"✓ Retrieved user VMs: {len(user_vms)} VM(s) found")
        
        # Cleanup
        db.delete(test_vm)
        db.delete(test_user)
        db.commit()
        print("✓ Cleaned up test data")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Run all VM Manager tests"""
    print("=" * 70)
    print("VM MANAGER TEST SUITE")
    print("=" * 70)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    tests = [
        ("VM Manager Initialization", test_vm_manager_initialization),
        ("Vagrantfile Generation", test_vagrantfile_generation),
        ("VM Directory Structure", test_vm_directory_structure),
        ("VM Info File Operations", test_vm_info_file_operations),
        ("VM Database Model Integration", test_vm_database_model),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name}: PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name}: FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 70)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
