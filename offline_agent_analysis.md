# Agent Offline Analysis & Solutions

## 🔍 **Why Agents Get Marked as Offline**

### **Root Cause Analysis**

From your logs, I can see:
```
2025-07-20 15:33:29,404 - __main__ - INFO - ❌ Marked 1 agents as offline
2025-07-20 15:33:59,411 - __main__ - INFO - ❌ Marked 1 agents as offline
```

**The issue is: Your Rust client is NOT sending heartbeats!**

### **How the Offline Detection Works**

1. **Heartbeat Timeout**: 2 minutes (120 seconds)
2. **Cleanup Interval**: Every 30 seconds
3. **Detection Logic**: If `last_heartbeat` is older than 2 minutes → mark as offline

### **The Problem**

Your Rust client registers successfully:
```
🔗 Agent registered in database: DC2 (b5880487-d66f-4fd4-9702-e922ad2f1b6b)
✅ Agent registered successfully: DC2 -> b5880487-d66f-4fd4-9702-e922ad2f1b6b
```

But then **never sends heartbeats**, so after 2 minutes it gets marked as offline.

## 🛠️ **Solutions**

### **Solution 1: Fix Your Rust Client Heartbeat**

Your Rust client needs to send heartbeats every 60 seconds:

```rust
// In your Rust client, add this heartbeat loop
async fn start_heartbeat_loop(agent_id: String, registration_url: String) {
    let client = reqwest::Client::new();
    
    loop {
        let heartbeat_data = serde_json::json!({
            "agent_id": agent_id,
            "status": "online"
        });
        
        match client.post(&format!("{}/api/agents/{}/heartbeat", registration_url, agent_id))
            .json(&heartbeat_data)
            .send()
            .await {
                Ok(response) => {
                    if response.status().is_success() {
                        info!("💓 Heartbeat sent successfully");
                    } else {
                        warn!("⚠️ Heartbeat failed: {}", response.status());
                    }
                }
                Err(e) => {
                    error!("❌ Heartbeat error: {}", e);
                }
        }
        
        // Wait 60 seconds before next heartbeat
        tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
    }
}
```

### **Solution 2: Increase Heartbeat Timeout**

If you want longer timeouts, modify the server:

```python
# In main.py, change the timeout
class AgentManager:
    def __init__(self):
        self.db = db_manager
        self.heartbeat_timeout = timedelta(minutes=5)  # Change from 2 to 5 minutes
```

### **Solution 3: Disable Offline Detection (Temporary)**

For testing, you can disable the cleanup:

```python
# In main.py, comment out the cleanup task
async def cleanup_offline_agents(self):
    """Background task to mark agents as offline if they haven't sent heartbeat"""
    while True:
        # Comment out the cleanup logic for testing
        # try:
        #     offline_count = self.db.cleanup_offline_agents()
        #     if offline_count > 0:
        #         logger.info(f"❌ Marked {offline_count} agents as offline")
        # except Exception as e:
        #     logger.error(f"Error in cleanup task: {e}")
        await asyncio.sleep(30)  # Check every 30 seconds
```

## 🔧 **Testing Commands on Offline Agents**

### **Check Agent Status First**

```bash
# List all agents to see their status
curl -X GET "http://remote.skyshift.dev:4433/api/agents"
```

### **Send Command to Online Agent**

```bash
# Only works if agent is "online"
curl -X POST "http://remote.skyshift.dev:4433/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo \"Hello from command!\"",
    "shell_type": "bash"
  }'
```

## 📊 **Current Agent Status**

Based on your logs, you have:
- **Agent ID**: `2ee09ba5-e227-400b-993e-6a97faaff50d`
- **Hostname**: `DC2`
- **Status**: Likely offline (no heartbeats)

## 🚀 **Immediate Actions**

### **1. Test Command on Current Agent**
```bash
# Try sending a command (will fail if offline)
curl -X POST "http://remote.skyshift.dev:4433/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo \"Test command\"",
    "shell_type": "bash"
  }'
```

### **2. Check Agent Status**
```bash
curl -X GET "http://remote.skyshift.dev:4433/api/agents"
```

### **3. Fix Your Rust Client**
The main issue is your Rust client needs to implement the heartbeat loop as shown above.

## ⚠️ **Important Notes**

1. **Commands only work on online agents** - Offline agents will return 400 errors
2. **Heartbeats are required** - Without heartbeats, agents go offline after 2 minutes
3. **Registration is not enough** - You must also send heartbeats
4. **Check logs** - The server logs show exactly when agents go offline

## 🎯 **Next Steps**

1. **Implement heartbeat in your Rust client**
2. **Test with a simple command**
3. **Monitor the logs for heartbeat activity**
4. **Verify agent stays online** 