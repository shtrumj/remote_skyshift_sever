@echo off
echo ======================================
echo         Simple System Information
echo ======================================

echo Computer Name: %COMPUTERNAME%
echo User: %USERNAME%
echo Date: %DATE%
echo Time: %TIME%
echo.

echo ======================================
echo         Basic System Info
echo ======================================
echo OS Version:
ver
echo.

echo ======================================
echo         Network Info
echo ======================================
ipconfig | findstr "IPv4"
echo.

echo ======================================
echo         Memory Info
echo ======================================
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value
echo.

echo ======================================
echo         Disk Info
echo ======================================
wmic logicaldisk get caption,size,freespace
echo.

echo ======================================
echo Report completed successfully.
echo ====================================== 