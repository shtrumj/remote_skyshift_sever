#!/usr/bin/env python3
"""
Script to make user 'yonatan' an admin and approved
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_manager
from auth import get_password_hash
import uuid

def make_yonatan_admin():
    """Make user 'yonatan' an admin and approved"""
    try:
        # Check if yonatan exists
        existing_user = db_manager.get_user_by_username("yonatan")
        if not existing_user:
            print("❌ User 'yonatan' not found!")
            print("Creating user 'yonatan' as admin...")
            
            # Create yonatan as admin
            user_data = {
                "id": str(uuid.uuid4()),
                "username": "yonatan",
                "email": "yonatan@trot.co.il",
                "full_name": "Yehonathan shtrum",
                "hashed_password": get_password_hash("Gib$0n579!"),
                "is_active": True,
                "is_admin": True,
                "is_approved": True
            }
            
            user_id = db_manager.create_user(user_data)
            print(f"✅ Created user 'yonatan' as admin with ID: {user_id}")
        else:
            print("✅ User 'yonatan' found!")
            
            # Update yonatan to be admin and approved
            from datetime import datetime
            updates = {
                "is_admin": True,
                "is_approved": True,
                "approved_by": "system",
                "approved_at": datetime.utcnow()
            }
            
            success = db_manager.update_user(existing_user["id"], updates)
            if success:
                print("✅ Updated user 'yonatan' to be admin and approved!")
            else:
                print("❌ Failed to update user 'yonatan'")
                return False
        
        # Verify the changes
        updated_user = db_manager.get_user_by_username("yonatan")
        if updated_user:
            print(f"\n📋 User 'yonatan' details:")
            print(f"   ID: {updated_user['id']}")
            print(f"   Username: {updated_user['username']}")
            print(f"   Email: {updated_user['email']}")
            print(f"   Full Name: {updated_user['full_name']}")
            print(f"   Is Admin: {updated_user['is_admin']}")
            print(f"   Is Approved: {updated_user['is_approved']}")
            print(f"   Is Active: {updated_user['is_active']}")
            print(f"   Approved By: {updated_user['approved_by']}")
            print(f"   Approved At: {updated_user['approved_at']}")
            
            return True
        else:
            print("❌ Failed to verify user 'yonatan'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Making user 'yonatan' an admin...")
    success = make_yonatan_admin()
    
    if success:
        print("\n✅ Successfully made 'yonatan' an admin!")
        print("   You can now log in and approve other users.")
    else:
        print("\n❌ Failed to make 'yonatan' an admin!")
        sys.exit(1) 