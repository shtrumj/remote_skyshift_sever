#!/usr/bin/env python3
"""
Create User Script for Remote Agent Manager

Usage:
    python create_user.py <username> <password> [email] [full_name]

Examples:
    python create_user.py admin password123
    python create_user.py john password123 john@example.com "John Doe"
    python create_user.py jane password123 jane@example.com "Jane Smith"
"""

import argparse
import sys
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

import uuid
from datetime import datetime

from Scripts.auth import UserCreate, get_password_hash
from Scripts.database import db_manager


def create_user(username: str, password: str, email: str = None, full_name: str = None):
    """
    Create a new user in the database

    Args:
        username (str): Username for the new user
        password (str): Password for the new user
        email (str, optional): Email address for the new user
        full_name (str, optional): Full name for the new user

    Returns:
        dict: User data if successful, None if failed
    """
    try:
        # Check if user already exists
        existing_user = db_manager.get_user_by_username(username)
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return None

        # Check if email is provided and if it already exists
        if email:
            existing_email = db_manager.get_user_by_email(email)
            if existing_email:
                print(f"❌ Email '{email}' is already registered!")
                return None

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create user data
        user_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email or f"{username}@example.com",
            "full_name": full_name or username,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Save user to database
        user_id = db_manager.create_user(user_data)

        if user_id:
            print(f"✅ User '{username}' created successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Username: {username}")
            print(f"   Email: {user_data['email']}")
            print(f"   Full Name: {user_data['full_name']}")
            print(f"   Status: Active")
            print(
                f"   Created: {user_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return user_data
        else:
            print(f"❌ Failed to create user '{username}'!")
            return None

    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return None


def main():
    """Main function to handle command line arguments and create user"""

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Create a new user for Remote Agent Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_user.py admin password123
  python create_user.py john password123 john@example.com "John Doe"
  python create_user.py jane password123 jane@example.com "Jane Smith"
        """,
    )

    parser.add_argument("username", help="Username for the new user")

    parser.add_argument("password", help="Password for the new user")

    parser.add_argument(
        "--email",
        "-e",
        help="Email address for the new user (default: username@example.com)",
    )

    parser.add_argument(
        "--full-name", "-f", help="Full name for the new user (default: username)"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Parse arguments
    args = parser.parse_args()

    # Validate inputs
    if len(args.username) < 3:
        print("❌ Username must be at least 3 characters long!")
        sys.exit(1)

    if len(args.password) < 6:
        print("❌ Password must be at least 6 characters long!")
        sys.exit(1)

    # Print header
    print("🔧 Remote Agent Manager - User Creation Tool")
    print("=" * 50)

    if args.verbose:
        print(f"📝 Creating user with following details:")
        print(f"   Username: {args.username}")
        print(f"   Email: {args.email or f'{args.username}@example.com'}")
        print(f"   Full Name: {args.full_name or args.username}")
        print(f"   Password: {'*' * len(args.password)}")
        print()

    # Create the user
    user_data = create_user(
        username=args.username,
        password=args.password,
        email=args.email,
        full_name=args.full_name,
    )

    if user_data:
        print()
        print("🎉 User creation completed successfully!")
        print("You can now login to the Remote Agent Manager using these credentials.")
        print()
        print("Login URL: http://localhost:4433/ui/login")
        print("Username:", args.username)
        print("Password:", args.password)
    else:
        print()
        print("💥 User creation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
