
# 快速启动后端 - 使用编译好的 exe
Write-Host "🚀 快速启动后端服务..." -ForegroundColor Green

# 检查 InfluxDB 是否在运行
$influxdbRunning = $false
try {
    $test = Invoke-WebRequest -Uri "http://localhost:8086/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $influxdbRunning = $true
} catch {
    $influxdbRunning = $false
}

if (-not $influxdbRunning) {
    Write-Host "📊 InfluxDB 未运行，正在启动..." -ForegroundColor Yellow
    cd "c:\Users\JERRY\influxdb2\influxdb2_windows_amd64"
    Start-Process ".\influxd.exe"
    Start-Sleep -Seconds 2
}

# 启动后端 - 用编译好的 exe，最快！
Write-Host "🔧 启动后端..." -ForegroundColor Yellow
cd "c:\Users\JERRY\Desktop\gp\src_5-2\dev _back_end\dev"
.\dev.exe
