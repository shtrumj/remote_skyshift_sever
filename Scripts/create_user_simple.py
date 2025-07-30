#!/usr/bin/env python3
"""
Simple User Creation Script for Remote Agent Manager

Usage:
    python create_user_simple.py <username> <password>

Example:
    python create_user_simple.py admin password123
"""

import sys
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

import uuid
from datetime import datetime

from Scripts.auth import get_password_hash
from Scripts.database import db_manager


def main():
    """Simple user creation with just username and password"""

    if len(sys.argv) != 3:
        print("Usage: python create_user_simple.py <username> <password>")
        print("Example: python create_user_simple.py admin password123")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    # Validate inputs
    if len(username) < 3:
        print("❌ Username must be at least 3 characters long!")
        sys.exit(1)

    if len(password) < 6:
        print("❌ Password must be at least 6 characters long!")
        sys.exit(1)

    try:
        # Check if user already exists
        existing_user = db_manager.get_user_by_username(username)
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            sys.exit(1)

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create user data
        user_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": f"{username}@example.com",
            "full_name": username,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Save user to database
        user_id = db_manager.create_user(user_data)

        if user_id:
            print(f"✅ User '{username}' created successfully!")
            print(f"Login URL: http://localhost:4433/ui/login")
            print(f"Username: {username}")
            print(f"Password: {password}")
        else:
            print(f"❌ Failed to create user '{username}'!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
