#!/usr/bin/env python3
"""
Remote Agent Manager Server with SSL/TLS Support
Supports both HTTP (port 4433) and HTTPS (port 4434)
"""

import asyncio
import uvicorn
import ssl
from pathlib import Path
from main import app, logger

def create_ssl_context():
    """Create SSL context for HTTPS"""
    cert_dir = Path("certs")
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    if not cert_file.exists() or not key_file.exists():
        logger.error("❌ SSL certificates not found!")
        logger.error("Please run: python generate_certificates.py")
        return None
    
    try:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert_file, key_file)
        logger.info("✅ SSL context created successfully")
        return ssl_context
    except Exception as e:
        logger.error(f"❌ Failed to create SSL context: {e}")
        return None

async def run_servers():
    """Run both HTTP and HTTPS servers"""
    
    # Create SSL context
    ssl_context = create_ssl_context()
    
    # HTTP server config (port 4433)
    http_config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=4433,
        log_level="info"
    )
    
    # HTTPS server config (port 4434)
    https_config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=4434,
        ssl_certfile="certs/server.crt" if ssl_context else None,
        ssl_keyfile="certs/server.key" if ssl_context else None,
        log_level="info"
    )
    
    # Create servers
    http_server = uvicorn.Server(http_config)
    https_server = uvicorn.Server(https_config) if ssl_context else None
    
    logger.info("🚀 Starting Remote Agent Manager servers...")
    logger.info(f"📡 HTTP server: http://0.0.0.0:4433")
    
    if https_server:
        logger.info(f"🔒 HTTPS server: https://0.0.0.0:4434")
    else:
        logger.warning("⚠️  HTTPS server disabled (no SSL certificates)")
    
    # Run servers concurrently
    tasks = [asyncio.create_task(http_server.serve())]
    if https_server:
        tasks.append(asyncio.create_task(https_server.serve()))
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down servers...")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(run_servers()) 