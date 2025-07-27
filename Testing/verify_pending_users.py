#!/usr/bin/env python3
"""
Comprehensive verification script for pending users functionality
"""

import requests
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager
from auth import get_password_hash
import uuid
from datetime import datetime

def test_pending_users_flow():
    """Test the complete pending users flow"""
    base_url = "http://localhost:4433"
    
    print("🚀 Starting comprehensive pending users verification...")
    
    # Step 1: Login as admin
    print("\n1️⃣ Logging in as admin...")
    admin_login_data = {
        "username": "yonatan",
        "password": "Gib$0n579!"
    }
    
    login_response = requests.post(
        f"{base_url}/api/auth/login",
        json=admin_login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    admin_token = login_response.json().get("access_token")
    if not admin_token:
        print("❌ No admin access token received")
        return False
    
    print("✅ Admin login successful")
    
    # Step 2: Check current pending users
    print("\n2️⃣ Checking current pending users...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    pending_response = requests.get(
        f"{base_url}/api/admin/pending-users",
        headers=headers
    )
    
    if pending_response.status_code != 200:
        print(f"❌ Failed to get pending users: {pending_response.status_code}")
        return False
    
    initial_pending = pending_response.json().get("pending_users", [])
    print(f"📋 Initial pending users: {len(initial_pending)}")
    
    # Step 3: Create a test user via API
    print("\n3️⃣ Creating test user via API...")
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_email = f"testuser_{timestamp}@example.com"
    
    # Create user directly in database
    user_data = {
        "id": str(uuid.uuid4()),
        "username": test_username,
        "email": test_email,
        "full_name": "Test User",
        "hashed_password": get_password_hash("testpass123"),
        "is_active": True,
        "is_admin": False,
        "is_approved": False
    }
    
    try:
        user_id = db_manager.create_user(user_data)
        print(f"✅ Test user created: {test_username}")
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return False
    
    # Step 4: Check pending users again
    print("\n4️⃣ Checking pending users after creating test user...")
    time.sleep(1)  # Small delay to ensure database consistency
    
    pending_response = requests.get(
        f"{base_url}/api/admin/pending-users",
        headers=headers
    )
    
    if pending_response.status_code != 200:
        print(f"❌ Failed to get pending users: {pending_response.status_code}")
        return False
    
    updated_pending = pending_response.json().get("pending_users", [])
    print(f"📋 Updated pending users: {len(updated_pending)}")
    
    # Check if our test user is in the list
    test_user_found = False
    for user in updated_pending:
        if user['username'] == test_username:
            test_user_found = True
            print(f"✅ Test user found in pending users: {user['username']}")
            print(f"   is_approved: {user['is_approved']}")
            print(f"   is_active: {user['is_active']}")
            break
    
    if not test_user_found:
        print("❌ Test user NOT found in pending users")
        print("📋 All pending users:")
        for user in updated_pending:
            print(f"   - {user['username']} (approved: {user['is_approved']}, active: {user['is_active']})")
        return False
    
    # Step 5: Clean up test user
    print("\n5️⃣ Cleaning up test user...")
    try:
        db_manager.delete_user(user_id)
        print(f"✅ Test user deleted: {test_username}")
    except Exception as e:
        print(f"❌ Failed to delete test user: {e}")
    
    # Step 6: Final check
    print("\n6️⃣ Final pending users check...")
    final_pending_response = requests.get(
        f"{base_url}/api/admin/pending-users",
        headers=headers
    )
    
    if final_pending_response.status_code == 200:
        final_pending = final_pending_response.json().get("pending_users", [])
        print(f"📋 Final pending users: {len(final_pending)}")
    else:
        print(f"❌ Failed to get final pending users: {final_pending_response.status_code}")
    
    print("\n✅ Comprehensive pending users verification completed successfully!")
    return True

if __name__ == "__main__":
    success = test_pending_users_flow()
    if success:
        print("\n🎉 All tests PASSED - Pending users functionality is working correctly")
    else:
        print("\n❌ Tests FAILED - There are issues with pending users functionality") 