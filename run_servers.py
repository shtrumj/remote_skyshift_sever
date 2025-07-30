#!/usr/bin/env python3
"""
Run both HTTP and HTTPS servers simultaneously
"""

import signal
import subprocess
import sys
import time
from pathlib import Path


def check_certificates():
    """Check if SSL certificates exist"""
    cert_file = Path("CertificateConfiguration/certs/server.crt")
    key_file = Path("CertificateConfiguration/certs/server.key")

    if not cert_file.exists() or not key_file.exists():
        print("❌ SSL certificates not found!")
        print("Generating certificates...")

        try:
            subprocess.run(
                [sys.executable, "CertificateConfiguration/generate_certificates.py"],
                check=True,
            )
            print("✅ Certificates generated successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to generate certificates")
            return False

    return True


def main():
    print("🚀 Starting Remote Agent Manager with SSL/TLS support...")

    # Check certificates
    if not check_certificates():
        print("⚠️  Starting HTTP server only (no SSL certificates)")
        http_process = subprocess.Popen([sys.executable, "main.py"])

        try:
            http_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            http_process.terminate()
        return

    # Start HTTP server (port 80)
    print("📡 Starting HTTP server on port 80...")
    http_process = subprocess.Popen([sys.executable, "Scripts/main.py"])

    # Wait a moment for HTTP server to start
    time.sleep(3)

    # Start HTTPS server (port 443)
    print("🔒 Starting HTTPS server on port 443...")
    https_process = subprocess.Popen([sys.executable, "Scripts/main.py", "--https"])

    print("\n✅ Both servers started successfully!")
    print("📡 HTTP server: http://remote.skyshift.dev:80")
    print("🔒 HTTPS server: https://remote.skyshift.dev:443")
    print("\nPress Ctrl+C to stop all servers...")

    def signal_handler(sig, frame):
        print("\n🛑 Shutting down servers...")
        http_process.terminate()
        https_process.terminate()
        http_process.wait()
        https_process.wait()
        print("✅ Servers stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
