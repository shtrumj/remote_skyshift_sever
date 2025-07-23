@echo off
setlocal enabledelayedexpansion

echo ======================================
echo         System Information Report
echo ======================================

echo Computer Name: %COMPUTERNAME%
echo User: %USERNAME%
echo Date: %DATE%
echo Time: %TIME%
echo.

echo ======================================
echo            Memory Information
echo ======================================

REM Get memory info using simpler commands
for /f "tokens=2 delims==" %%a in ('wmic OS get TotalVisibleMemorySize /value 2^>nul') do set TotalMem=%%a
for /f "tokens=2 delims==" %%a in ('wmic OS get FreePhysicalMemory /value 2^>nul') do set FreeMem=%%a

if defined TotalMem (
    set /a TotalMemMB=%TotalMem% / 1024
    set /a FreeMemMB=%FreeMem% / 1024
    set /a UsedMemMB=%TotalMemMB% - %FreeMemMB%
    
    echo Total Physical Memory: %TotalMemMB% MB
    echo Used Physical Memory: %UsedMemMB% MB
    echo Free Physical Memory: %FreeMemMB% MB
) else (
    echo Memory information not available
)
echo.

echo ======================================
echo         System Information
echo ======================================
echo OS Version:
ver
echo.

echo ======================================
echo         Network Information
echo ======================================
ipconfig | findstr "IPv4"
echo.

echo ======================================
echo         Disk Information
echo ======================================
wmic logicaldisk get size,freespace,caption
echo.

echo ======================================
echo Report completed successfully.
echo ====================================== 