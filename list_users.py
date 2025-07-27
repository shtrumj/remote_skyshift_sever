#!/usr/bin/env python3
"""
List Users Script for Remote Agent Manager

Usage:
    python list_users.py
"""

from pathlib import Path
import sys

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from database import db_manager


def main():
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
            print(f"   Full Name: {user['full_name']}")
            print(f"   Status: {'Active' if user['is_active'] else 'Inactive'}")
            print(f"   Created: {user['created_at']}")
            print(f"   User ID: {user['id']}")
            print("-" * 30)
        
        print(f"📊 Total users: {len(users)}")
        
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 