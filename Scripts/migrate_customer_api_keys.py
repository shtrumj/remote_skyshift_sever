#!/usr/bin/env python3
"""
Database Migration Script for Customer API Keys
Adds new API key columns to the existing customers table
"""
import os
import sqlite3
from pathlib import Path


def migrate_customer_api_keys():
    """Migrate the customers table to add API key columns"""
    db_path = Path("agents.db")

    if not db_path.exists():
        print("❌ Database file 'agents.db' not found!")
        print("Please run the application first to create the database.")
        return False

    print("🔧 Starting customer API key migration...")

    try:
        # Connect to the database
        conn = sqlite3.connect("agents.db")
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cursor.fetchall()]

        print(f"📋 Current columns in customers table: {columns}")

        # Add new columns if they don't exist (without UNIQUE constraint initially)
        new_columns = [
            ("api_key", "TEXT"),
            ("api_key_created_at", "DATETIME"),
            ("api_key_last_used", "DATETIME"),
            ("is_active", "BOOLEAN DEFAULT 1"),
        ]

        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"➕ Adding column: {column_name}")
                cursor.execute(
                    f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}"
                )
            else:
                print(f"✅ Column already exists: {column_name}")

        # Create a unique index on api_key if it doesn't exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='ix_customers_api_key'"
        )
        if not cursor.fetchone():
            print("➕ Creating unique index on api_key")
            cursor.execute(
                "CREATE UNIQUE INDEX ix_customers_api_key ON customers(api_key)"
            )
        else:
            print("✅ Unique index on api_key already exists")

        # Commit changes
        conn.commit()

        # Verify the migration
        cursor.execute("PRAGMA table_info(customers)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Final columns in customers table: {final_columns}")

        # Update existing customers to have is_active = True
        cursor.execute("UPDATE customers SET is_active = 1 WHERE is_active IS NULL")
        updated_count = cursor.rowcount
        if updated_count > 0:
            print(f"✅ Updated {updated_count} existing customers to active status")

        conn.commit()
        conn.close()

        print("✅ Customer API key migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def backup_database():
    """Create a backup of the database before migration"""
    db_path = Path("agents.db")
    if db_path.exists():
        backup_path = Path("agents_backup.db")
        import shutil

        shutil.copy2(db_path, backup_path)
        print(f"💾 Database backed up to: {backup_path}")
        return True
    return False


def main():
    """Main migration function"""
    print("🚀 Customer API Key Database Migration")
    print("=" * 50)

    # Create backup
    if backup_database():
        print("✅ Backup created successfully")
    else:
        print("⚠️  No existing database to backup")

    # Run migration
    if migrate_customer_api_keys():
        print("\n🎉 Migration completed successfully!")
        print("You can now create customers with API key support.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")


if __name__ == "__main__":
    main()
