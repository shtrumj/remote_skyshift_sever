#!/usr/bin/env python3
"""
Create a persistent test user for frontend testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from auth import get_password_hash
import uuid

def create_test_user():
    """Create a test user for frontend testing"""
    print("🔍 Creating test user for frontend testing...")
    
    # Create user data
    user_data = {
        "id": str(uuid.uuid4()),
        "username": "testuser_frontend",
        "email": "testuser_frontend@example.com",
        "full_name": "Frontend Test User",
        "hashed_password": get_password_hash("testpass123"),
        "is_active": True,
        "is_admin": False,
        "is_approved": False
    }
    
    try:
        # Check if user already exists
        existing_user = db_manager.get_user_by_username("testuser_frontend")
        if existing_user:
            print("⚠️ Test user already exists, deleting...")
            db_manager.delete_user(existing_user["id"])
        
        # Create user
        user_id = db_manager.create_user(user_data)
        print(f"✅ Test user created with ID: {user_id}")
        print(f"   Username: {user_data['username']}")
        print(f"   Email: {user_data['email']}")
        print(f"   is_approved: {user_data['is_approved']}")
        print(f"   is_active: {user_data['is_active']}")
        
        # Verify user is in pending users
        pending_users = db_manager.get_pending_users()
        test_user_in_pending = None
        for user in pending_users:
            if user['username'] == "testuser_frontend":
                test_user_in_pending = user
                break
        
        if test_user_in_pending:
            print("✅ Test user found in pending users list")
        else:
            print("❌ Test user NOT found in pending users list")
        
        print("\n🎯 Now you can:")
        print("1. Go to http://localhost:4433/ui/login")
        print("2. Login as yonatan (admin)")
        print("3. Go to http://localhost:4433/ui/admin")
        print("4. Check if the test user appears in pending users")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

if __name__ == "__main__":
    success = create_test_user()
    if success:
        print("\n✅ Test user created successfully!")
    else:
        print("\n❌ Failed to create test user!") 