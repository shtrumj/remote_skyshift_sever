#!/usr/bin/env python3
"""
Test script to simulate frontend pending users functionality
"""

import requests
import json

def test_frontend_pending_users():
    """Test the frontend pending users functionality"""
    base_url = "http://localhost:4433"
    
    print("🔍 Testing frontend pending users functionality...")
    
    # Step 1: Simulate UI login (like the frontend does)
    print("📝 Step 1: Simulating UI login...")
    
    # Create a session to handle cookies like a browser
    session = requests.Session()
    
    # Simulate the login form submission
    login_data = {
        "username": "yonatan",
        "password": "Gib$0n579!"
    }
    
    # This simulates the UI login form submission
    login_response = session.post(
        f"{base_url}/ui/login",
        data=login_data,  # Form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"📊 UI Login response status: {login_response.status_code}")
    print(f"📊 UI Login response headers: {dict(login_response.headers)}")
    print(f"📊 UI Login cookies: {dict(session.cookies)}")
    
    # Check if we got the access_token cookie
    access_token = session.cookies.get("access_token")
    if access_token:
        print(f"✅ Got access_token cookie: {access_token[:20]}...")
    else:
        print("❌ No access_token cookie received")
        return False
    
    # Step 2: Test the profile endpoint (like main.js does)
    print("\n📝 Step 2: Testing profile endpoint (like main.js)...")
    
    profile_response = session.get(f"{base_url}/api/users/profile")
    print(f"📊 Profile response status: {profile_response.status_code}")
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(f"✅ Profile data received: {profile_data['username']}")
        print(f"   is_admin: {profile_data['is_admin']}")
    else:
        print(f"❌ Profile request failed: {profile_response.status_code}")
        print(f"   Response: {profile_response.text}")
        return False
    
    # Step 3: Test pending users endpoint (like admin dashboard does)
    print("\n📝 Step 3: Testing pending users endpoint...")
    
    pending_response = session.get(f"{base_url}/api/admin/pending-users")
    print(f"📊 Pending users response status: {pending_response.status_code}")
    
    if pending_response.status_code == 200:
        pending_data = pending_response.json()
        pending_users = pending_data.get("pending_users", [])
        total_pending = pending_data.get("total", 0)
        print(f"✅ Pending users data received: {total_pending} users")
        
        for user in pending_users:
            print(f"   - {user['username']} ({user['email']}) - Approved: {user['is_approved']}")
    else:
        print(f"❌ Pending users request failed: {pending_response.status_code}")
        print(f"   Response: {pending_response.text}")
        return False
    
    # Step 4: Test with explicit cookie header (like our previous tests)
    print("\n📝 Step 4: Testing with explicit cookie header...")
    
    headers_with_cookie = {"Cookie": f"access_token={access_token}"}
    explicit_pending_response = requests.get(
        f"{base_url}/api/admin/pending-users",
        headers=headers_with_cookie
    )
    
    print(f"📊 Explicit cookie response status: {explicit_pending_response.status_code}")
    
    if explicit_pending_response.status_code == 200:
        explicit_data = explicit_pending_response.json()
        explicit_pending = explicit_data.get("pending_users", [])
        explicit_total = explicit_data.get("total", 0)
        print(f"✅ Explicit cookie method: {explicit_total} users")
    else:
        print(f"❌ Explicit cookie method failed: {explicit_pending_response.status_code}")
    
    print("\n✅ Frontend simulation completed successfully!")
    return True

if __name__ == "__main__":
    success = test_frontend_pending_users()
    if success:
        print("\n🎉 Frontend tests PASSED - The issue might be browser-specific")
    else:
        print("\n❌ Frontend tests FAILED - There are issues with the frontend") 