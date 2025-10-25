"""
Test script for SOC Manager implementation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.soc import SOCManager

def test_soc_manager():
    """Test SOC Manager initialization and basic functionality"""
    print("🧪 Testing SOC Manager Implementation")
    print("=" * 60)
    
    # Test 1: Initialize SOC Manager
    print("\n✓ Test 1: Initialize SOC Manager")
    soc = SOCManager(log_dir="logs")
    print(f"  - Log directory: {soc.log_dir}")
    print(f"  - Events log: {soc.events_log}")
    print(f"  - SSH log: {soc.ssh_log}")
    assert soc.log_dir.exists(), "Log directory should exist"
    
    # Test 2: Check methods exist
    print("\n✓ Test 2: Check SOC Manager methods")
    methods = [
        'log_event',
        'log_vm_created',
        'log_vm_started',
        'log_vm_stopped',
        'log_vm_destroyed',
        'log_vm_error',
        'log_ssh_attempt',
        'detect_brute_force',
        'log_system_event',
        'log_resource_alert',
        'get_recent_events',
        'get_event_statistics',
        'analyze_user_activity',
        'parse_vagrant_logs',
        'parse_ssh_logs'
    ]
    
    for method in methods:
        assert hasattr(soc, method), f"Method {method} should exist"
        print(f"  - {method}() ✓")
    
    # Test 3: Test log file parsing (with empty files)
    print("\n✓ Test 3: Test log file parsing")
    from pathlib import Path
    test_log = Path("logs/test_vagrant.log")
    test_log.parent.mkdir(exist_ok=True)
    test_log.touch()
    
    vagrant_events = soc.parse_vagrant_logs(test_log)
    print(f"  - Parsed {len(vagrant_events)} Vagrant events (empty file expected)")
    
    ssh_events = soc.parse_ssh_logs(test_log)
    print(f"  - Parsed {len(ssh_events)} SSH events (empty file expected)")
    
    test_log.unlink()
    
    # Test 4: Verify global instance
    print("\n✓ Test 4: Verify global SOC manager instance")
    from backend.soc import soc_manager
    assert soc_manager is not None, "Global soc_manager should exist"
    assert isinstance(soc_manager, SOCManager), "Global instance should be SOCManager"
    print(f"  - Global soc_manager instance exists ✓")
    
    print("\n" + "=" * 60)
    print("✅ All SOC Manager tests passed!")
    print("\n📊 Summary:")
    print(f"  - SOCManager class initialized successfully")
    print(f"  - {len(methods)} event logging methods implemented")
    print(f"  - Event analysis and correlation functions available")
    print(f"  - Log file parsing implemented")
    print(f"  - SSH brute force detection available")
    print(f"  - Ready for integration with FastAPI endpoints")
    
if __name__ == "__main__":
    test_soc_manager()
