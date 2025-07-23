Write-Host "======================================" -ForegroundColor Green
Write-Host "        System Information Report" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

Write-Host "Computer Name: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "Date: $(Get-Date -Format 'MM/dd/yyyy')"
Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')"
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "            Memory Information" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

try {
    $os = Get-WmiObject -Class Win32_OperatingSystem
    $totalMem = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeMem = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $usedMem = $totalMem - $freeMem
    
    Write-Host "Total Physical Memory: $totalMem MB"
    Write-Host "Used Physical Memory: $usedMem MB"
    Write-Host "Free Physical Memory: $freeMem MB"
} catch {
    Write-Host "Memory information not available: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "            System Information" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host "OS Version:"
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture | Format-List
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "            Network Information" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Get-NetIPAddress | Where-Object {$_.AddressFamily -eq "IPv4"} | Format-Table IPAddress, InterfaceAlias
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "            Disk Information" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace | ForEach-Object {
    $sizeGB = [math]::Round($_.Size / 1GB, 2)
    $freeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    Write-Host "Drive $($_.DeviceID): Size=$sizeGB GB, Free=$freeGB GB"
}
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "            Latest User Logins" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
try {
    Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 5 | ForEach-Object {
        $props = $_.Properties
        $username = $props[5].Value
        $time = $_.TimeCreated
        Write-Host "User: $username, Time: $time"
    }
} catch {
    Write-Host "Login information not available: $($_.Exception.Message)"
}
Write-Host ""

Write-Host "======================================" -ForegroundColor Green
Write-Host "Report generated successfully." -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green 