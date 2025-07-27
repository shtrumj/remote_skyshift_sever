#!/usr/bin/env python3
"""
Debug user data from database
"""

from pathlib import Path
import sys

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from database import db_manager
from auth import User

def debug_user_data():
    """Debug user data from database"""
    
    print("🔍 Debugging User Data")
    print("=" * 30)
    
    # Get all users
    users = db_manager.get_all_users()
    if not users:
        print("❌ No users found!")
        return
    
    for i, user in enumerate(users):
        print(f"\n👤 User {i+1}:")
        print(f"   Raw data: {user}")
        print(f"   Keys: {list(user.keys())}")
        print(f"   Types: {[(k, type(v)) for k, v in user.items()]}")
        
        # Try to create User object
        try:
            user_obj = User(**user)
            print(f"   ✅ User object created successfully!")
        except Exception as e:
            print(f"   ❌ Error creating User object: {e}")

if __name__ == "__main__":
    debug_user_data() 