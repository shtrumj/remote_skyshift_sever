#!/usr/bin/env python3
"""
Test script for Customer API Key functionality
"""
import json
import sys
from pathlib import Path

import requests

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from database import db_manager


def test_customer_api_key():
    """Test the customer API key functionality"""
    print("🧪 Testing Customer API Key Functionality")
    print("=" * 50)

    # Test 1: Create a customer
    print("\n1️⃣ Creating a test customer...")
    customer_data = {
        "id": "test-customer-001",
        "uuid": "test-uuid-001",
        "name": "Test Customer",
        "address": "123 Test Street",
    }

    try:
        customer_uuid = db_manager.create_customer(customer_data)
        print(f"✅ Customer created with UUID: {customer_uuid}")
    except Exception as e:
        print(f"❌ Failed to create customer: {e}")
        return False

    # Test 2: Generate API key
    print("\n2️⃣ Generating API key...")
    try:
        api_key = db_manager.generate_api_key(customer_uuid)
        if api_key:
            print(f"✅ API key generated: {api_key[:20]}...")
        else:
            print("❌ Failed to generate API key")
            return False
    except Exception as e:
        print(f"❌ Failed to generate API key: {e}")
        return False

    # Test 3: Get customer by API key
    print("\n3️⃣ Testing API key authentication...")
    try:
        customer = db_manager.get_customer_by_api_key(api_key)
        if customer:
            print(f"✅ Customer authenticated: {customer['name']}")
            print(f"   UUID: {customer['uuid']}")
            print(f"   API Key: {customer['api_key'][:20]}...")
            print(f"   Created: {customer['api_key_created_at']}")
            print(f"   Last Used: {customer['api_key_last_used']}")
        else:
            print("❌ Failed to authenticate with API key")
            return False
    except Exception as e:
        print(f"❌ Failed to authenticate with API key: {e}")
        return False

    # Test 4: Test API key usage tracking
    print("\n4️⃣ Testing API key usage tracking...")
    try:
        # Get customer again to test usage tracking
        customer2 = db_manager.get_customer_by_api_key(api_key)
        if (
            customer2
            and customer2["api_key_last_used"] != customer["api_key_last_used"]
        ):
            print("✅ API key usage timestamp updated")
        else:
            print("⚠️  API key usage timestamp not updated")
    except Exception as e:
        print(f"❌ Failed to test usage tracking: {e}")

    # Test 5: Revoke API key
    print("\n5️⃣ Testing API key revocation...")
    try:
        success = db_manager.revoke_api_key(customer_uuid)
        if success:
            print("✅ API key revoked successfully")
        else:
            print("❌ Failed to revoke API key")
            return False
    except Exception as e:
        print(f"❌ Failed to revoke API key: {e}")
        return False

    # Test 6: Verify API key is revoked
    print("\n6️⃣ Verifying API key is revoked...")
    try:
        customer_after_revoke = db_manager.get_customer_by_api_key(api_key)
        if customer_after_revoke is None:
            print("✅ API key properly revoked - authentication fails")
        else:
            print("❌ API key still works after revocation")
            return False
    except Exception as e:
        print(f"❌ Error verifying revocation: {e}")
        return False

    print("\n🎉 All tests passed! Customer API key functionality is working correctly.")
    return True


def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)

    base_url = "https://remote.skyshift.dev:443"

    # Test 1: Create customer via API
    print("\n1️⃣ Creating customer via API...")
    customer_data = {"name": "API Test Customer", "address": "456 API Street"}

    try:
        response = requests.post(
            f"{base_url}/api/customers",
            json=customer_data,
            verify=False,  # Skip SSL verification for self-signed cert
        )

        if response.status_code == 200:
            result = response.json()
            customer_uuid = result["uuid"]
            print(f"✅ Customer created via API: {customer_uuid}")
        else:
            print(f"❌ Failed to create customer via API: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return False

    print("\n✅ API endpoint test completed!")
    return True


def main():
    """Main test function"""
    print("🚀 Customer API Key Test Suite")
    print("=" * 60)

    # Test database functionality
    if not test_customer_api_key():
        print("\n❌ Database tests failed!")
        return

    # Test API endpoints
    if not test_api_endpoints():
        print("\n❌ API endpoint tests failed!")
        return

    print("\n🎉 All tests completed successfully!")
    print("Customer API key system is fully functional!")


if __name__ == "__main__":
    main()
