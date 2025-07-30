#!/usr/bin/env python3
"""
Test WebSocket Fix - Verify that WebSocket connections are working after the fix
"""

import asyncio
import json
import uuid

import websockets


async def test_websocket_connection():
    """Test WebSocket connection to verify the fix"""
    print("🧪 Testing WebSocket Connection Fix")
    print("=" * 50)

    # Test parameters
    server_url = "wss://remote.skyshift.dev"
    agent_id = f"test-agent-{uuid.uuid4()}"
    ws_url = f"{server_url}/ws/agent/{agent_id}"

    print(f"🔗 Connecting to: {ws_url}")

    try:
        # Connect to WebSocket
        websocket = await websockets.connect(ws_url)
        print("✅ WebSocket connection established successfully!")

        # Send a heartbeat message
        heartbeat = {"type": "heartbeat", "agent_id": agent_id, "status": "online"}

        print("💓 Sending heartbeat...")
        await websocket.send(json.dumps(heartbeat))
        print("✅ Heartbeat sent successfully")

        # Wait for acknowledgment
        print("⏳ Waiting for heartbeat acknowledgment...")
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        response_data = json.loads(response)

        if response_data.get("type") == "heartbeat_ack":
            print("✅ Received heartbeat acknowledgment!")
            print(f"   Timestamp: {response_data.get('timestamp')}")
        else:
            print(f"⚠️ Unexpected response: {response_data}")

        # Close the connection
        await websocket.close()
        print("🔌 WebSocket connection closed")

        print("\n" + "=" * 50)
        print("✅ WebSocket fix is working correctly!")
        return True

    except websockets.exceptions.InvalidURI:
        print("❌ Invalid WebSocket URI")
        return False
    except websockets.exceptions.ConnectionClosed:
        print("❌ WebSocket connection closed unexpectedly")
        return False
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False


async def main():
    """Main function"""
    success = await test_websocket_connection()
    if success:
        print("\n🎉 WebSocket fix verification completed successfully!")
        print("   The server now properly accepts WebSocket connections.")
        print("   Real-time communication should work for agents.")
    else:
        print("\n❌ WebSocket fix verification failed!")
        print("   There may still be issues with the WebSocket implementation.")


if __name__ == "__main__":
    asyncio.run(main())
