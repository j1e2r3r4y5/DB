# 启动后端（可选先拉起 InfluxDB 2.x）
$ErrorActionPreference = "Stop"
$DeployRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Write-Host "仓库根目录: $DeployRoot" -ForegroundColor Gray

$influxOk = $false
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:8086/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $influxOk = $true
} catch { $influxOk = $false }

if (-not $influxOk) {
    $InfluxCandidates = @(
        $env:INFLUXDB2_HOME,
        "C:\Users\JERRY\influxdb2\influxdb2_windows_amd64",
        (Join-Path $DeployRoot "tools\influxdb2_windows_amd64")
    ) | Where-Object { $_ -and (Test-Path (Join-Path $_ "influxd.exe")) }
    if ($InfluxCandidates.Count -gt 0) {
        $d = $InfluxCandidates[0]
        Write-Host "启动 InfluxDB: $d" -ForegroundColor Yellow
        Start-Process (Join-Path $d "influxd.exe") -WorkingDirectory $d
        Start-Sleep -Seconds 2
    } else {
        Write-Warning "InfluxDB 未响应且未找到 influxd.exe，请手动启动 InfluxDB 2.x 后再启动后端。"
    }
}

$BackendDir = Join-Path $DeployRoot "dev_back_end\dev"
Push-Location $BackendDir
try {
    go build -o dev.exe main.go
    Write-Host "启动后端: $BackendDir\dev.exe" -ForegroundColor Green
    .\dev.exe
} finally {
    Pop-Location
}
