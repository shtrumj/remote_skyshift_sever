#!/usr/bin/env python3
"""
Test script to simulate admin dashboard frontend functionality
"""

import requests
import json

def test_admin_dashboard():
    """Test admin dashboard functionality"""
    base_url = "http://localhost:4433"
    
    print("🔍 Testing admin dashboard functionality...")
    
    # Step 1: Login as admin
    print("📝 Logging in as admin...")
    login_data = {
        "username": "yonatan",
        "password": "Gib$0n579!"
    }
    
    login_response = requests.post(
        f"{base_url}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    access_token = login_data.get("access_token")
    
    if not access_token:
        print("❌ No access token received")
        return False
    
    print("✅ Login successful")
    
    # Step 2: Get pending users
    print("📋 Getting pending users...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    pending_response = requests.get(
        f"{base_url}/api/admin/pending-users",
        headers=headers
    )
    
    if pending_response.status_code != 200:
        print(f"❌ Failed to get pending users: {pending_response.status_code}")
        print(f"Response: {pending_response.text}")
        return False
    
    pending_data = pending_response.json()
    pending_users = pending_data.get("pending_users", [])
    total_pending = pending_data.get("total", 0)
    
    print(f"✅ Found {total_pending} pending users")
    for user in pending_users:
        print(f"   - {user['username']} ({user['email']}) - Approved: {user['is_approved']}")
    
    # Step 3: Get all users
    print("👥 Getting all users...")
    users_response = requests.get(
        f"{base_url}/api/users",
        headers=headers
    )
    
    if users_response.status_code != 200:
        print(f"❌ Failed to get all users: {users_response.status_code}")
        print(f"Response: {users_response.text}")
        return False
    
    users_data = users_response.json()
    all_users = users_data.get("users", [])
    
    print(f"✅ Found {len(all_users)} total users")
    for user in all_users:
        status = "Approved" if user['is_approved'] else "Pending"
        admin = "Admin" if user['is_admin'] else "User"
        print(f"   - {user['username']} ({user['email']}) - {status}, {admin}")
    
    # Step 4: Test with cookies (like frontend does)
    print("🍪 Testing with cookies (frontend method)...")
    
    # Create a new session and set cookies properly
    session = requests.Session()
    
    # Set the cookie manually (simulating browser behavior)
    session.cookies.set(
        name="access_token",
        value=access_token,
        domain="localhost",
        path="/"
    )
    
    print(f"🍪 Set cookie: access_token={access_token[:20]}...")
    print(f"🍪 Session cookies: {dict(session.cookies)}")
    
    # Test pending users with cookies
    cookie_pending_response = session.get(f"{base_url}/api/admin/pending-users")
    
    print(f"🍪 Cookie request status: {cookie_pending_response.status_code}")
    print(f"🍪 Cookie request headers: {dict(cookie_pending_response.request.headers)}")
    
    if cookie_pending_response.status_code != 200:
        print(f"❌ Cookie method failed: {cookie_pending_response.status_code}")
        print(f"Response: {cookie_pending_response.text}")
        
        # Try with explicit Cookie header
        print("🍪 Trying with explicit Cookie header...")
        headers_with_cookie = {"Cookie": f"access_token={access_token}"}
        explicit_cookie_response = requests.get(
            f"{base_url}/api/admin/pending-users",
            headers=headers_with_cookie
        )
        
        print(f"🍪 Explicit cookie status: {explicit_cookie_response.status_code}")
        if explicit_cookie_response.status_code == 200:
            print("✅ Explicit cookie method worked!")
            cookie_pending_data = explicit_cookie_response.json()
            cookie_pending_users = cookie_pending_data.get("pending_users", [])
            cookie_total_pending = cookie_pending_data.get("total", 0)
            
            print(f"✅ Explicit cookie method found {cookie_total_pending} pending users")
            for user in cookie_pending_users:
                print(f"   - {user['username']} ({user['email']}) - Approved: {user['is_approved']}")
            return True
        else:
            print(f"❌ Explicit cookie also failed: {explicit_cookie_response.status_code}")
            print(f"Response: {explicit_cookie_response.text}")
            return False
    
    cookie_pending_data = cookie_pending_response.json()
    cookie_pending_users = cookie_pending_data.get("pending_users", [])
    cookie_total_pending = cookie_pending_data.get("total", 0)
    
    print(f"✅ Cookie method found {cookie_total_pending} pending users")
    for user in cookie_pending_users:
        print(f"   - {user['username']} ({user['email']}) - Approved: {user['is_approved']}")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting admin dashboard frontend test...")
    
    try:
        success = test_admin_dashboard()
        if success:
            print("\n✅ All tests PASSED - Admin dashboard functionality is working")
        else:
            print("\n❌ Tests FAILED - There are issues with admin dashboard functionality")
    except Exception as e:
        print(f"\n❌ Test error: {e}") 