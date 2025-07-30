#!/usr/bin/env python3
"""
Generate Customer API Key and Copy to Clipboard
"""
import argparse
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from Scripts.database import db_manager


def copy_to_clipboard(text):
    """Copy text to clipboard"""
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except ImportError:
        print("❌ pyperclip not installed. Install with: pip install pyperclip")
        return False
    except Exception as e:
        print(f"❌ Failed to copy to clipboard: {e}")
        return False


def generate_api_key_for_customer(customer_uuid):
    """Generate API key for a specific customer"""
    try:
        # Check if customer exists
        customer = db_manager.get_customer(customer_uuid)
        if not customer:
            print(f"❌ Customer with UUID {customer_uuid} not found")
            return None

        # Generate API key
        api_key = db_manager.generate_api_key(customer_uuid)
        if not api_key:
            print(f"❌ Failed to generate API key for customer {customer_uuid}")
            return None

        return {
            "customer_uuid": customer_uuid,
            "customer_name": customer["name"],
            "api_key": api_key,
        }
    except Exception as e:
        print(f"❌ Error generating API key: {e}")
        return None


def list_customers():
    """List all customers"""
    try:
        customers = db_manager.get_all_customers()
        if not customers:
            print("📋 No customers found")
            return

        print("📋 Registered Customers:")
        print("-" * 80)
        print(f"{'UUID':<36} {'Name':<20} {'Has API Key':<12} {'Created'}")
        print("-" * 80)

        for customer in customers:
            has_api_key = "✅ Yes" if customer.get("api_key") else "❌ No"
            created = customer.get("created_at", "Unknown")[:10]  # Just the date part
            print(
                f"{customer['uuid']:<36} {customer['name']:<20} {has_api_key:<12} {created}"
            )

        print("-" * 80)
        print(f"Total customers: {len(customers)}")

    except Exception as e:
        print(f"❌ Error listing customers: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Generate Customer API Key and Copy to Clipboard"
    )
    parser.add_argument("--uuid", "-u", help="Customer UUID to generate API key for")
    parser.add_argument("--list", "-l", action="store_true", help="List all customers")
    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        help="Don't copy to clipboard, just display",
    )

    args = parser.parse_args()

    print("🔑 Customer API Key Generator")
    print("=" * 50)

    if args.list:
        list_customers()
        return

    if not args.uuid:
        print(
            "❌ Please provide a customer UUID with --uuid or use --list to see available customers"
        )
        print("\nUsage examples:")
        print("  python generate_customer_api_key.py --list")
        print("  python generate_customer_api_key.py --uuid <customer_uuid>")
        return

    # Generate API key
    result = generate_api_key_for_customer(args.uuid)
    if not result:
        return

    # Display the result
    print(f"✅ API Key generated successfully!")
    print(f"📋 Customer: {result['customer_name']}")
    print(f"🔑 UUID: {result['customer_uuid']}")
    print(f"🔑 API Key: {result['api_key']}")

    # Prepare clipboard text
    clipboard_text = f"Customer: {result['customer_name']}\nUUID: {result['customer_uuid']}\nAPI Key: {result['api_key']}"

    if not args.no_clipboard:
        # Copy to clipboard
        if copy_to_clipboard(clipboard_text):
            print(f"\n📋 Copied to clipboard!")
            print("📋 Clipboard contents:")
            print("-" * 40)
            print(clipboard_text)
            print("-" * 40)
        else:
            print(f"\n📋 Failed to copy to clipboard, but here's the information:")
            print("-" * 40)
            print(clipboard_text)
            print("-" * 40)
    else:
        print(f"\n📋 Information (not copied to clipboard):")
        print("-" * 40)
        print(clipboard_text)
        print("-" * 40)


if __name__ == "__main__":
    main()
