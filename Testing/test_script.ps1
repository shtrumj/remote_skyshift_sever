# Test PowerShell Script for Remote Agent Manager
# This script demonstrates system information gathering

Write-Host "=== System Information ===" -ForegroundColor Green
Write-Host "Computer Name: $env:COMPUTERNAME" -ForegroundColor Yellow
Write-Host "User Name: $env:USERNAME" -ForegroundColor Yellow
Write-Host "OS Version: $(Get-WmiObject -Class Win32_OperatingSystem | Select-Object -ExpandProperty Caption)" -ForegroundColor Yellow

Write-Host "`n=== Disk Space ===" -ForegroundColor Green
Get-WmiObject -Class Win32_LogicalDisk | ForEach-Object {
    $freeSpace = [math]::Round($_.FreeSpace / 1GB, 2)
    $totalSpace = [math]::Round($_.Size / 1GB, 2)
    $usedSpace = $totalSpace - $freeSpace
    $percentUsed = [math]::Round(($usedSpace / $totalSpace) * 100, 2)
    
    Write-Host "Drive $($_.DeviceID): $freeSpace GB free of $totalSpace GB ($percentUsed% used)" -ForegroundColor Cyan
}

Write-Host "`n=== Running Processes (Top 5 by CPU) ===" -ForegroundColor Green
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 | ForEach-Object {
    Write-Host "$($_.ProcessName): $([math]::Round($_.CPU, 2)) CPU, $([math]::Round($_.WorkingSet / 1MB, 2)) MB RAM" -ForegroundColor White
}

Write-Host "`n=== Network Connections ===" -ForegroundColor Green
Get-NetTCPConnection | Where-Object {$_.State -eq "Listen"} | Select-Object -First 5 | ForEach-Object {
    Write-Host "Port $($_.LocalPort): $($_.State)" -ForegroundColor White
}

Write-Host "`n=== Script completed successfully! ===" -ForegroundColor Green 