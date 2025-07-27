#!/usr/bin/env python3
"""
Start Remote Agent Manager with both HTTP and HTTPS support
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

def check_certificates():
    """Check if SSL certificates exist"""
    cert_file = Path("certs/server.crt")
    key_file = Path("certs/server.key")
    
    if not cert_file.exists() or not key_file.exists():
        print("❌ SSL certificates not found!")
        print("Generating certificates...")
        
        try:
            subprocess.run([sys.executable, "generate_certificates.py"], check=True)
            print("✅ Certificates generated successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to generate certificates")
            return False
    
    return True

def start_http_server():
    """Start HTTP server on port 4433"""
    print("📡 Starting HTTP server on port 4433...")
    return subprocess.Popen([
        sys.executable, "main.py"
    ])

def start_https_server():
    """Start HTTPS server on port 4434"""
    print("🔒 Starting HTTPS server on port 4434...")
    return subprocess.Popen([
        sys.executable, "main.py", "--https"
    ])

def main():
    """Main function to start both servers"""
    print("🚀 Remote Agent Manager - Starting servers...")
    
    # Check certificates
    if not check_certificates():
        print("⚠️  Starting HTTP server only (no SSL certificates)")
        http_process = start_http_server()
        
        try:
            http_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            http_process.terminate()
        return
    
    # Start both servers
    http_process = start_http_server()
    time.sleep(2)  # Give HTTP server time to start
    https_process = start_https_server()
    
    print("\n✅ Servers started successfully!")
    print("📡 HTTP server: http://localhost:4433")
    print("🔒 HTTPS server: https://localhost:4434")
    print("\nPress Ctrl+C to stop all servers...")
    
    try:
        # Wait for both processes
        while http_process.poll() is None and https_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        http_process.terminate()
        https_process.terminate()
        
        # Wait for processes to terminate
        http_process.wait()
        https_process.wait()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main() 