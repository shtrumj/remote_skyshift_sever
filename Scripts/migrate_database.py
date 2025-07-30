#!/usr/bin/env python3
"""
Database Migration Script for Admin and Approval System
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3

from Scripts.database import db_manager


def migrate_database():
    """Migrate the database to add admin and approval columns"""
    try:
        # Connect to the database
        conn = sqlite3.connect("./agents.db")
        cursor = conn.cursor()

        print("🔧 Starting database migration...")

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        print(f"📋 Current columns: {columns}")

        # Add new columns if they don't exist
        if "is_admin" not in columns:
            print("➕ Adding is_admin column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

        if "is_approved" not in columns:
            print("➕ Adding is_approved column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0")

        if "approved_by" not in columns:
            print("➕ Adding approved_by column...")
            cursor.execute("ALTER TABLE users ADD COLUMN approved_by TEXT")

        if "approved_at" not in columns:
            print("➕ Adding approved_at column...")
            cursor.execute("ALTER TABLE users ADD COLUMN approved_at DATETIME")

        # Commit changes
        conn.commit()

        # Verify the migration
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"✅ Updated columns: {new_columns}")

        # Update existing users to be approved (for backward compatibility)
        print("🔄 Updating existing users to be approved...")
        cursor.execute("UPDATE users SET is_approved = 1 WHERE is_approved IS NULL")
        conn.commit()

        print("✅ Database migration completed successfully!")

        # Close connection
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate_database()

    if success:
        print("\n✅ Database migration completed!")
        print("   You can now run: python make_yonatan_admin.py")
    else:
        print("\n❌ Database migration failed!")
        sys.exit(1)
