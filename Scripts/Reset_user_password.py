#!/usr/bin/env python3
"""
Reset User Password Script for Remote Agent Manager

This script allows administrators to reset user passwords via command line.
It requires the username and new password as arguments.
"""

import argparse
import sys
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from auth import get_password_hash

from database import db_manager


def reset_user_password(username: str, new_password: str):
    """
    Reset a user's password in the database

    Args:
        username (str): Username of the user to reset password for
        new_password (str): New password for the user

    Returns:
        bool: True if successful, False if failed
    """
    try:
        print(f"🔧 Resetting password for user: {username}")

        # Check if user exists
        existing_user = db_manager.get_user_by_username(username)
        if not existing_user:
            print(f"❌ User '{username}' not found!")
            return False

        # Validate new password
        if len(new_password) < 6:
            print("❌ New password must be at least 6 characters long!")
            return False

        # Hash the new password
        hashed_password = get_password_hash(new_password)

        # Update user password
        updates = {
            "hashed_password": hashed_password,
        }

        success = db_manager.update_user(existing_user["id"], updates)
        if success:
            print(f"✅ Password reset successfully for user '{username}'")
            print("📝 New password: " + "*" * len(new_password))
            return True
        else:
            print(f"❌ Failed to reset password for user '{username}'")
            return False

    except Exception as e:
        print(f"❌ Error resetting password: {str(e)}")
        return False


def list_users():
    """List all users in the database"""
    try:
        users = db_manager.get_all_users()

        if not users:
            print("📝 No users found in database.")
            return

        print("👥 Users in database:")
        print("=" * 50)

        for i, user in enumerate(users, 1):
            print(f"{i}. Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Full Name: {user.get('full_name', 'N/A')}")
            print(f"   Status: {'Active' if user['is_active'] else 'Inactive'}")
            print(f"   Admin: {'Yes' if user.get('is_admin') else 'No'}")
            print(f"   Approved: {'Yes' if user.get('is_approved') else 'No'}")
            print(f"   User ID: {user['id']}")
            print("-" * 30)

        print(f"📊 Total users: {len(users)}")

    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")


def main():
    """Main function to handle command line arguments and reset password"""

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Reset User Password - Remote Agent Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python Reset_user_password.py john newpassword123
    python Reset_user_password.py admin securepass456
    python Reset_user_password.py --list
    python Reset_user_password.py --help
        """,
    )

    parser.add_argument(
        "username", nargs="?", help="Username of the user to reset password for"
    )
    parser.add_argument("new_password", nargs="?", help="New password for the user")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all users in the database"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Parse arguments
    args = parser.parse_args()

    # Print header
    print("🔧 Remote Agent Manager - Password Reset Tool")
    print("=" * 50)

    # Handle list command
    if args.list:
        list_users()
        return

    # Check if required arguments are provided
    if not args.username or not args.new_password:
        print("❌ Please provide both username and new password!")
        print("\nUsage:")
        print("  python Reset_user_password.py <username> <new_password>")
        print("  python Reset_user_password.py --list")
        print("  python Reset_user_password.py --help")
        sys.exit(1)

    # Validate inputs
    if len(args.username) < 3:
        print("❌ Username must be at least 3 characters long!")
        sys.exit(1)

    if len(args.new_password) < 6:
        print("❌ New password must be at least 6 characters long!")
        sys.exit(1)

    if args.verbose:
        print("📝 Resetting password with following details:")
        print(f"   Username: {args.username}")
        print("   New Password: " + "*" * len(args.new_password))
        print()

    # Reset the password
    success = reset_user_password(args.username, args.new_password)

    if success:
        print()
        print("✅ Password reset completed successfully!")
        print(f"   User '{args.username}' can now log in with the new password.")
    else:
        print()
        print("❌ Password reset failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
