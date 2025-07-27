#!/usr/bin/env python3
"""
Debug script to test user registration and pending users functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from auth import get_password_hash
import uuid
from datetime import datetime

def test_user_registration():
    """Test user registration and pending users"""
    print("🔍 Testing user registration and pending users...")
    
    # Generate unique username and email
    timestamp = int(datetime.utcnow().timestamp())
    test_username = f"testuser_{timestamp}"
    test_email = f"testuser_{timestamp}@example.com"
    
    print(f"📝 Creating test user: {test_username}")
    
    # Create user data
    user_data = {
        "id": str(uuid.uuid4()),
        "username": test_username,
        "email": test_email,
        "full_name": "Test User",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True,
        "is_admin": False,
        "is_approved": False
    }
    
    try:
        # Create user
        user_id = db_manager.create_user(user_data)
        print(f"✅ User created with ID: {user_id}")
        
        # Check if user exists
        user = db_manager.get_user_by_username(test_username)
        if user:
            print(f"✅ User found in database: {user['username']}")
            print(f"   is_approved: {user['is_approved']}")
            print(f"   is_active: {user['is_active']}")
        else:
            print("❌ User not found in database")
            return False
        
        # Check pending users
        pending_users = db_manager.get_pending_users()
        print(f"📋 Pending users count: {len(pending_users)}")
        
        # Check if our test user is in pending users
        test_user_in_pending = None
        for pending_user in pending_users:
            if pending_user['username'] == test_username:
                test_user_in_pending = pending_user
                break
        
        if test_user_in_pending:
            print(f"✅ Test user found in pending users: {test_user_in_pending['username']}")
            print(f"   is_approved: {test_user_in_pending['is_approved']}")
            print(f"   is_active: {test_user_in_pending['is_active']}")
        else:
            print("❌ Test user NOT found in pending users")
            print("📋 All pending users:")
            for user in pending_users:
                print(f"   - {user['username']} (approved: {user['is_approved']}, active: {user['is_active']})")
        
        # Clean up - delete test user
        db_manager.delete_user(user_id)
        print(f"🧹 Cleaned up test user: {test_username}")
        
        return test_user_in_pending is not None
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def check_all_users():
    """Check all users in the database"""
    print("\n🔍 Checking all users in database...")
    
    all_users = db_manager.get_all_users()
    print(f"📊 Total users: {len(all_users)}")
    
    for user in all_users:
        print(f"   - {user['username']} (approved: {user['is_approved']}, active: {user['is_active']}, admin: {user['is_admin']})")

def check_pending_users():
    """Check pending users specifically"""
    print("\n🔍 Checking pending users...")
    
    pending_users = db_manager.get_pending_users()
    print(f"📋 Pending users count: {len(pending_users)}")
    
    for user in pending_users:
        print(f"   - {user['username']} (approved: {user['is_approved']}, active: {user['is_active']})")

if __name__ == "__main__":
    print("🚀 Starting pending users debug test...")
    
    # Check current state
    check_all_users()
    check_pending_users()
    
    # Test user registration
    success = test_user_registration()
    
    # Check state after test
    print("\n📊 Final state:")
    check_all_users()
    check_pending_users()
    
    if success:
        print("\n✅ Test PASSED - New users are correctly added to pending users")
    else:
        print("\n❌ Test FAILED - New users are NOT being added to pending users") 