#!/usr/bin/env python3
"""
Database utility functions for agent management
"""
import sqlite3
import json
import os
from datetime import datetime
from database import db_manager

def backup_database():
    """Create a backup of the SQLite database"""
    backup_file = f"agents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists("agents.db"):
        import shutil
        shutil.copy2("agents.db", backup_file)
        print(f"✅ Database backed up to: {backup_file}")
        return backup_file
    else:
        print("❌ No database file found to backup")
        return None

def export_agents_to_json():
    """Export all agents to JSON file"""
    agents = db_manager.get_all_agents()
    export_file = f"agents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(export_file, 'w') as f:
        json.dump(agents, f, indent=2, default=str)
    
    print(f"✅ Agents exported to: {export_file}")
    return export_file

def get_database_stats():
    """Get database statistics"""
    agents = db_manager.get_all_agents()
    online_agents = db_manager.get_online_agents()
    
    stats = {
        "total_agents": len(agents),
        "online_agents": len(online_agents),
        "offline_agents": len(agents) - len(online_agents),
        "database_file": "agents.db",
        "last_updated": datetime.now().isoformat()
    }
    
    return stats

def list_all_agents():
    """List all agents in the database"""
    agents = db_manager.get_all_agents()
    
    if not agents:
        print("📭 No agents found in database")
        return
    
    print(f"📊 Found {len(agents)} agents:")
    print("-" * 80)
    
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent['hostname']} ({agent['agent_id']})")
        print(f"   IP: {agent['ip_address']}:{agent['port']}")
        print(f"   Status: {agent['status']}")
        print(f"   Version: {agent['version']}")
        print(f"   Capabilities: {', '.join(agent['capabilities'])}")
        print(f"   Registered: {agent['registered_at']}")
        print(f"   Last heartbeat: {agent['last_heartbeat']}")
        print("-" * 80)

def cleanup_old_agents(days_old: int = 30):
    """Remove agents that haven't been active for specified days"""
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # This would need to be implemented in the database manager
    # For now, just show the concept
    print(f"🧹 Would remove agents inactive since: {cutoff_date}")
    print("💡 Implement cleanup_old_agents in DatabaseManager for full functionality")

if __name__ == "__main__":
    print("🗄️  Database Utilities")
    print("=" * 50)
    
    # Show database stats
    stats = get_database_stats()
    print(f"📊 Database Statistics:")
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Online agents: {stats['online_agents']}")
    print(f"   Offline agents: {stats['offline_agents']}")
    print(f"   Database file: {stats['database_file']}")
    
    print("\n" + "=" * 50)
    
    # List all agents
    list_all_agents()
    
    print("\n" + "=" * 50)
    
    # Export options
    print("💾 Export options:")
    print("   python database_utils.py backup    # Backup database")
    print("   python database_utils.py export    # Export agents to JSON")
    print("   python database_utils.py stats     # Show statistics")
    print("   python database_utils.py list      # List all agents") 