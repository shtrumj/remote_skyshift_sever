#!/usr/bin/env python3
"""
Test script to verify profile page functionality
"""

from urllib.parse import urljoin

import requests

# Configuration
BASE_URL = "https://remote.skyshift.dev"
LOGIN_URL = urljoin(BASE_URL, "/api/auth/login")
PROFILE_URL = urljoin(BASE_URL, "/api/users/profile")


def test_profile_functionality():
    """Test profile page functionality"""

    print("🧪 Testing Profile Page Functionality")
    print("=" * 50)

    # Test 1: Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        return False

    # Test 2: Test profile endpoint without authentication
    try:
        response = requests.get(PROFILE_URL, timeout=5)
        print(f"📊 Profile endpoint without auth: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly requires authentication")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Profile endpoint error: {e}")

    # Test 3: Test with authentication (if credentials available)
    print("\n🔐 Testing with authentication...")
    print("Note: This requires valid credentials")

    # You can uncomment and modify these lines to test with real credentials
    # credentials = {
    #     "username": "yonatan",
    #     "password": "your_password_here"
    # }
    #
    # try:
    #     # Login
    #     login_response = requests.post(LOGIN_URL, json=credentials, timeout=5)
    #     if login_response.status_code == 200:
    #         cookies = login_response.cookies
    #
    #         # Get profile
    #         profile_response = requests.get(PROFILE_URL, cookies=cookies, timeout=5)
    #         if profile_response.status_code == 200:
    #             profile_data = profile_response.json()
    #             print("✅ Profile data retrieved successfully:")
    #             print(f"   Username: {profile_data.get('username')}")
    #             print(f"   Email: {profile_data.get('email')}")
    #             print(f"   Full Name: {profile_data.get('full_name')}")
    #             print(f"   Status: {'Active' if profile_data.get('is_active') else 'Inactive'}")
    #         else:
    #             print(f"❌ Profile request failed: {profile_response.status_code}")
    #     else:
    #         print(f"❌ Login failed: {login_response.status_code}")
    # except Exception as e:
    #     print(f"❌ Authentication test error: {e}")

    print("\n📋 Manual Testing Instructions:")
    print("1. Open browser and go to: https://remote.skyshift.dev/ui/profile")
    print("2. Check browser console (F12) for any JavaScript errors")
    print("3. Look for these console messages:")
    print("   - '🔍 Profile page document ready - calling loadProfile()'")
    print("   - '🔍 Delayed loadProfile() call'")
    print("   - '🔍 loadProfile() function called'")
    print("   - '✅ Profile data received: {...}'")
    print("   - '🔍 Populating form fields...'")
    print("   - '✅ Form fields populated successfully'")
    print("4. Test the 'Test Password' button to verify change password functionality")
    print("5. If fields are empty, try clicking 'Refresh' button")

    return True


if __name__ == "__main__":
    test_profile_functionality()
