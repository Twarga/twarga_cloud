#!/usr/bin/env python3
"""
Test script for Phase 3.1 - System Monitoring Implementation
Verifies that the monitoring system is working correctly
"""

import sys
from backend.monitor import system_monitor
from backend.database import SessionLocal

def test_host_metrics():
    """Test host metrics collection"""
    print("\n🔍 Testing Host Metrics Collection...")
    metrics = system_monitor.get_host_metrics()
    
    if not metrics:
        print("❌ Failed to collect host metrics")
        return False
    
    print("✅ Host metrics collected successfully")
    print(f"   - CPU: {metrics.get('cpu_percent')}%")
    print(f"   - Memory: {metrics.get('memory_percent')}%")
    print(f"   - Disk: {metrics.get('disk_percent')}%")
    print(f"   - CPU Count: {metrics.get('cpu_count')}")
    print(f"   - Total Memory: {metrics.get('memory_total_gb')}GB")
    print(f"   - Total Disk: {metrics.get('disk_total_gb')}GB")
    print(f"   - Network Send Speed: {metrics.get('net_send_speed_mbps')}MB/s")
    print(f"   - Network Recv Speed: {metrics.get('net_recv_speed_mbps')}MB/s")
    print(f"   - System Uptime: {metrics.get('uptime_hours')}h")
    
    return True

def test_metric_storage():
    """Test metric storage in database"""
    print("\n🔍 Testing Metric Storage...")
    
    try:
        db = SessionLocal()
        metrics = system_monitor.get_host_metrics()
        
        if not metrics:
            print("❌ Failed to collect metrics for storage test")
            return False
        
        success = system_monitor.store_host_metrics(db, metrics)
        
        if success:
            print("✅ Metrics stored successfully in database")
        else:
            print("❌ Failed to store metrics in database")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during metric storage test: {e}")
        return False

def test_alerts():
    """Test alert threshold checking"""
    print("\n🔍 Testing Alert System...")
    
    try:
        db = SessionLocal()
        metrics = system_monitor.get_host_metrics()
        
        if not metrics:
            print("❌ Failed to collect metrics for alert test")
            return False
        
        alerts = system_monitor.check_resource_thresholds(db, metrics)
        
        if alerts:
            print(f"⚠️  {len(alerts)} alert(s) detected:")
            for alert in alerts:
                print(f"   - {alert}")
        else:
            print("✅ No resource alerts (all systems normal)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during alert test: {e}")
        return False

def test_comprehensive_collection():
    """Test comprehensive metric collection"""
    print("\n🔍 Testing Comprehensive Metric Collection...")
    
    try:
        db = SessionLocal()
        
        metrics, alerts = system_monitor.collect_and_store_all_metrics(db)
        
        if not metrics:
            print("❌ Failed to collect metrics")
            return False
        
        print("✅ Comprehensive metric collection successful")
        print(f"   - Collected {len(metrics)} metric values")
        print(f"   - Generated {len(alerts)} alerts")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during comprehensive collection test: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🧪 Phase 3.1 Monitoring System Test Suite")
    print("="*60)
    
    tests = [
        ("Host Metrics Collection", test_host_metrics),
        ("Metric Storage", test_metric_storage),
        ("Alert System", test_alerts),
        ("Comprehensive Collection", test_comprehensive_collection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 3.1 implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
