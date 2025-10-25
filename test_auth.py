#!/usr/bin/env python3
"""
Test script for authentication system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import init_db, SessionLocal
from backend.models import User
from backend.auth import get_password_hash

def test_auth_setup():
    """Test authentication setup"""
    print("Testing authentication system setup...")
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Create a test user
    db = SessionLocal()
    try:
        # Check if test user exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print("✓ Test user already exists")
        else:
            # Create test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpass123"),
                is_active=True,
                is_admin=False,
                credits=100
            )
            db.add(test_user)
            db.commit()
            print("✓ Test user created successfully")
        
        # Create admin user if doesn't exist
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("✓ Admin user already exists")
        else:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
                credits=1000
            )
            db.add(admin_user)
            db.commit()
            print("✓ Admin user created successfully")
        
        # Count users
        user_count = db.query(User).count()
        print(f"✓ Total users in database: {user_count}")
        
        print("\n✅ Authentication system setup complete!")
        print("\nTest credentials:")
        print("  Regular user: testuser / testpass123")
        print("  Admin user: admin / admin123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_auth_setup()
