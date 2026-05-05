Write-Host "=== Checking Local InfluxDB ==="
Write-Host "Testing port 8088..."
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8088/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "SUCCESS on 8088: $($r.StatusCode)"
} catch {
    Write-Host "Port 8088 failed"
}
Write-Host "Testing port 8086..."
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8086/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "SUCCESS on 8086: $($r.StatusCode)"
} catch {
    Write-Host "Port 8086 failed"
}
