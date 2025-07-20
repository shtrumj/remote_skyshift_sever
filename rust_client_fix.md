# Rust Client HTTP Configuration Fix

## Problem
Your Rust client is trying to connect to `https://remote.skyshift.dev:4433` (HTTPS) but the server is running on HTTP, causing SSL certificate validation errors.

## Solution: Change to HTTP

### 1. Update Registration URL
In your Rust client code, change:
```rust
// OLD (causing SSL errors)
let registration_url = std::env::var("REGISTRATION_URL")
    .unwrap_or_else(|_| "https://remote.skyshift.dev:4433".to_string());

// NEW (use HTTP)
let registration_url = std::env::var("REGISTRATION_URL")
    .unwrap_or_else(|_| "http://remote.skyshift.dev:4433".to_string());
```

### 2. Environment Variable (Optional)
You can also set the environment variable:
```bash
export REGISTRATION_URL="http://remote.skyshift.dev:4433"
```

### 3. Verify Connection
Test the connection with curl:
```bash
curl -X GET "http://remote.skyshift.dev:4433/health"
# Should return: {"status":"healthy","timestamp":"...","agents":{"total":0,"online":0,"offline":0}}
```

## Expected Behavior After Fix

1. **Registration**: `POST http://remote.skyshift.dev:4433/api/agents/register`
2. **Heartbeat**: `POST http://remote.skyshift.dev:4433/api/agents/{agent_id}/heartbeat`
3. **Commands**: `POST http://remote.skyshift.dev:4433/api/agents/{agent_id}/commands`

## Server Status
✅ **Server is running**: `http://remote.skyshift.dev:4433`  
✅ **Health endpoint**: Working correctly  
✅ **Agent registration**: Ready to accept clients  
✅ **Command tunneling**: Functional  

## Debugging Tips

If you still have issues after changing to HTTP:

1. **Check network connectivity**:
   ```bash
   curl -v http://remote.skyshift.dev:4433/health
   ```

2. **Verify your Rust client logs**:
   - Look for `INFO` messages about successful registration
   - Check for any remaining SSL/TLS errors

3. **Test with a simple HTTP client**:
   ```bash
   curl -X POST "http://remote.skyshift.dev:4433/api/agents/register" \
     -H "Content-Type: application/json" \
     -d '{"hostname":"test","ip_address":"192.168.1.100","port":3000,"capabilities":["bash"],"version":"1.0.0"}'
   ```

## Key Changes Summary

| Component | Old URL | New URL |
|-----------|---------|---------|
| Registration | `https://remote.skyshift.dev:4433` | `http://remote.skyshift.dev:4433` |
| Heartbeat | `https://remote.skyshift.dev:4433` | `http://remote.skyshift.dev:4433` |
| Commands | `https://remote.skyshift.dev:4433` | `http://remote.skyshift.dev:4433` |

After making this change, your Rust client should connect successfully without SSL certificate errors. 