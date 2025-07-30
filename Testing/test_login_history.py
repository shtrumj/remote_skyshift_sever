#!/usr/bin/env python3
"""
Test Login History - Verify that login history tracking is working
"""

import sys
from pathlib import Path

# Add Scripts directory to path
sys.path.append(str(Path(__file__).parent.parent / "Scripts"))

from database import db_manager


def test_login_history():
    """Test login history functionality"""
    print("🧪 Testing Login History Functionality")
    print("=" * 50)

    # Test 1: Check if login_history table exists
    print("\n1. Checking login_history table...")
    try:
        # Try to get login history for a test user
        test_user_id = "test-user-123"
        history = db_manager.get_user_login_history(test_user_id, limit=5)
        print("✅ Login history table exists and is accessible")
        print(f"   Found {len(history)} records for test user")
    except Exception as e:
        print(f"❌ Error accessing login history table: {e}")
        return False

    # Test 2: Record a test login attempt
    print("\n2. Recording test login attempt...")
    try:
        login_id = db_manager.record_login_attempt(
            user_id="test-user-123",
            username="testuser",
            source_ip_external="192.168.1.100",
            source_ip_internal="10.0.0.1",
            user_agent="Test Browser/1.0",
            success=True,
        )
        print(f"✅ Successfully recorded login attempt with ID: {login_id}")
    except Exception as e:
        print(f"❌ Error recording login attempt: {e}")
        return False

    # Test 3: Get login count
    print("\n3. Testing login count...")
    try:
        count = db_manager.get_user_login_count("test-user-123")
        print(f"✅ Login count for test user: {count}")
    except Exception as e:
        print(f"❌ Error getting login count: {e}")
        return False

    # Test 4: Get last login
    print("\n4. Testing last login retrieval...")
    try:
        last_login = db_manager.get_user_last_login("test-user-123")
        if last_login:
            print(f"✅ Last login found: {last_login['login_time']}")
            print(f"   IP: {last_login['source_ip_external']}")
        else:
            print("⚠️ No last login found")
    except Exception as e:
        print(f"❌ Error getting last login: {e}")
        return False

    # Test 5: Get login history
    print("\n5. Testing login history retrieval...")
    try:
        history = db_manager.get_user_login_history("test-user-123", limit=10)
        print(f"✅ Retrieved {len(history)} login history records")
        for i, record in enumerate(history[:3]):  # Show first 3 records
            print(f"   Record {i+1}: {record['login_time']} - {record['success']}")
    except Exception as e:
        print(f"❌ Error getting login history: {e}")
        return False

    print("\n" + "=" * 50)
    print("✅ All login history tests passed!")
    return True


if __name__ == "__main__":
    success = test_login_history()
    sys.exit(0 if success else 1)
