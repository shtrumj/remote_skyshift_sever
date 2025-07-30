#!/usr/bin/env python3
"""
Test script to verify admin approval system
"""
import requests
import json

def test_admin_approval_system():
    """Test the admin approval system"""
    base_url = "http://localhost:4433"
    
    print("🧪 Testing Admin Approval System...")
    
    # Test 1: Register a new user
    import time
    timestamp = int(time.time())
    test_username = f"testuser{timestamp}"
    test_email = f"testuser{timestamp}@example.com"
    
    print(f"\n1. Registering new user '{test_username}'...")
    register_data = {
        "username": test_username,
        "email": test_email,
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{base_url}/api/auth/register", json=register_data)
    print(f"   Registration response: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ User registered successfully")
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return False
    
    # Test 2: Try to login with new user (should fail)
    print(f"\n2. Attempting to login with new user '{test_username}' (should fail)...")
    login_data = {
        "username": test_username,
        "password": "testpass123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"   Login response: {response.status_code}")
    if response.status_code == 401:
        print("   ✅ Login correctly blocked - user not approved")
    else:
        print(f"   ❌ Login should have failed: {response.text}")
        return False
    
    # Test 3: Login as admin (yonatan)
    print("\n3. Logging in as admin (yonatan)...")
    admin_login_data = {
        "username": "yonatan",
        "password": "Gib$0n579!"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=admin_login_data)
    print(f"   Admin login response: {response.status_code}")
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        print("   ✅ Admin login successful")
    else:
        print(f"   ❌ Admin login failed: {response.text}")
        return False
    
    # Test 4: Get pending users as admin
    print("\n4. Getting pending users as admin...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{base_url}/api/admin/pending-users", headers=headers)
    print(f"   Pending users response: {response.status_code}")
    if response.status_code == 200:
        pending_users = response.json()["pending_users"]
        print(f"   ✅ Found {len(pending_users)} pending users")
        if len(pending_users) > 0:
            testuser_id = None
            for user in pending_users:
                if user["username"] == test_username:
                    testuser_id = user["id"]
                    break
            if testuser_id:
                print(f"   ✅ Found {test_username} with ID: {testuser_id}")
            else:
                print(f"   ❌ {test_username} not found in pending users")
                return False
        else:
            print("   ❌ No pending users found")
            return False
    else:
        print(f"   ❌ Failed to get pending users: {response.text}")
        return False
    
    # Test 5: Approve the user
    print(f"\n5. Approving {test_username}...")
    response = requests.post(f"{base_url}/api/admin/users/{testuser_id}/approve", headers=headers)
    print(f"   Approve response: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ User approved successfully")
    else:
        print(f"   ❌ Failed to approve user: {response.text}")
        return False
    
    # Test 6: Try to login with approved user (should succeed)
    print("\n6. Attempting to login with approved user (should succeed)...")
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"   Login response: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Login successful - user approved")
    else:
        print(f"   ❌ Login should have succeeded: {response.text}")
        return False
    
    print("\n🎉 All tests passed! Admin approval system is working correctly.")
    return True

if __name__ == "__main__":
    try:
        success = test_admin_approval_system()
        if not success:
            print("\n❌ Some tests failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit(1) 