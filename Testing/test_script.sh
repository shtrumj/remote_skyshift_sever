#!/bin/bash

# Test Bash Script for Remote Agent Manager
# This script demonstrates system information gathering

echo "=== System Information ==="
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "OS: $(uname -a)"
echo "Uptime: $(uptime)"

echo ""
echo "=== Disk Space ==="
df -h | head -10

echo ""
echo "=== Memory Usage ==="
free -h

echo ""
echo "=== Running Processes (Top 5 by CPU) ==="
ps aux --sort=-%cpu | head -6

echo ""
echo "=== Network Connections ==="
netstat -tuln | head -10

echo ""
echo "=== System Load ==="
cat /proc/loadavg

echo ""
echo "=== Script completed successfully! ===" 