#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for the Remote Agent Manager
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_certificates():
    """Generate self-signed SSL certificates"""
    
    # Create certificates directory
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    # Certificate paths
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    print("🔐 Generating self-signed SSL certificates...")
    
    # Check if OpenSSL is available
    try:
        subprocess.run(["openssl", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL is not installed or not in PATH")
        print("Please install OpenSSL and try again:")
        print("  - macOS: brew install openssl")
        print("  - Ubuntu/Debian: sudo apt-get install openssl")
        print("  - Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        sys.exit(1)
    
    # Generate private key
    print("📝 Generating private key...")
    subprocess.run([
        "openssl", "genrsa", "-out", str(key_file), "2048"
    ], check=True)
    
    # Generate certificate signing request
    print("📝 Generating certificate signing request...")
    subprocess.run([
        "openssl", "req", "-new", "-key", str(key_file), "-out", "server.csr",
        "-subj", "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=localhost"
    ], check=True)
    
    # Generate self-signed certificate
    print("📝 Generating self-signed certificate...")
    subprocess.run([
        "openssl", "x509", "-req", "-days", "365", "-in", "server.csr",
        "-signkey", str(key_file), "-out", str(cert_file)
    ], check=True)
    
    # Clean up CSR file
    if os.path.exists("server.csr"):
        os.remove("server.csr")
    
    print("✅ SSL certificates generated successfully!")
    print(f"   Certificate: {cert_file}")
    print(f"   Private Key: {key_file}")
    print("\n⚠️  These are self-signed certificates for development/testing only.")
    print("   For production, use certificates from a trusted Certificate Authority.")

if __name__ == "__main__":
    generate_certificates() 