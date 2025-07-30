#!/usr/bin/env python3
"""
Database Migration Script - Add Login History Table

This script adds the login_history table to track user login attempts.
"""

import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from database import db_manager


def create_login_history_table():
    """Create the login_history table"""
    try:
        print("🔧 Creating login_history table...")

        # Get the database path
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "Data"
        db_path = data_dir / "agents.db"

        # Backup the database
        backup_path = (
            data_dir / f"agents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        if db_path.exists():
            import shutil

            shutil.copy2(db_path, backup_path)
            print(f"📦 Database backed up to: {backup_path}")

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='login_history'
        """
        )

        if cursor.fetchone():
            print("✅ login_history table already exists!")
            conn.close()
            return True

        # Create the login_history table
        cursor.execute(
            """
            CREATE TABLE login_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                source_ip_external TEXT,
                source_ip_internal TEXT,
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                success BOOLEAN DEFAULT 1,
                failure_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Create indexes for better performance
        cursor.execute(
            "CREATE INDEX idx_login_history_user_id ON login_history(user_id)"
        )
        cursor.execute(
            "CREATE INDEX idx_login_history_username ON login_history(username)"
        )
        cursor.execute(
            "CREATE INDEX idx_login_history_login_time ON login_history(login_time)"
        )
        cursor.execute(
            "CREATE INDEX idx_login_history_success ON login_history(success)"
        )

        # Commit changes
        conn.commit()
        conn.close()

        print("✅ login_history table created successfully!")
        print("📊 Indexes created for optimal performance")

        return True

    except Exception as e:
        print(f"❌ Error creating login_history table: {str(e)}")
        return False


def verify_migration():
    """Verify that the migration was successful"""
    try:
        print("🔍 Verifying migration...")

        # Test the new methods
        test_user_id = "test_migration_user"
        test_username = "test_migration"

        # Test recording a login attempt
        record_id = db_manager.record_login_attempt(
            user_id=test_user_id,
            username=test_username,
            source_ip_external="192.168.1.100",
            source_ip_internal="10.0.0.1",
            user_agent="Test Browser",
            success=True,
        )

        if record_id:
            print("✅ Login attempt recording works!")
        else:
            print("❌ Login attempt recording failed!")
            return False

        # Test getting login count
        count = db_manager.get_user_login_count(test_user_id)
        if count == 1:
            print("✅ Login count retrieval works!")
        else:
            print(f"❌ Login count retrieval failed! Expected 1, got {count}")
            return False

        # Test getting last login
        last_login = db_manager.get_user_last_login(test_user_id)
        if last_login and last_login["username"] == test_username:
            print("✅ Last login retrieval works!")
        else:
            print("❌ Last login retrieval failed!")
            return False

        print("✅ Migration verification completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error verifying migration: {str(e)}")
        return False


def main():
    """Main migration function"""
    print("🚀 Login History Migration Script")
    print("=" * 50)

    # Create the table
    if not create_login_history_table():
        print("❌ Migration failed!")
        sys.exit(1)

    # Verify the migration
    if not verify_migration():
        print("❌ Migration verification failed!")
        sys.exit(1)

    print("✅ Migration completed successfully!")
    print("\n📝 What was added:")
    print("   - login_history table with columns:")
    print("     * id (TEXT PRIMARY KEY)")
    print("     * user_id (TEXT, Foreign Key to users.id)")
    print("     * username (TEXT)")
    print("     * source_ip_external (TEXT)")
    print("     * source_ip_internal (TEXT)")
    print("     * login_time (DATETIME)")
    print("     * user_agent (TEXT)")
    print("     * success (BOOLEAN)")
    print("     * failure_reason (TEXT)")
    print("     * created_at (DATETIME)")
    print("   - Performance indexes on user_id, username, login_time, and success")
    print("   - Database backup created before migration")


if __name__ == "__main__":
    main()
