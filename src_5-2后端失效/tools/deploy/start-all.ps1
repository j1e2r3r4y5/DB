# 一键启动：InfluxDB（若已安装）、后端、前端、模拟器
# 依赖：MySQL:3306、MQTT:1883 须已启动；InfluxDB 2.x 在 8086（可选路径见下方）
$ErrorActionPreference = "Stop"
$DeployRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Write-Host "仓库根目录: $DeployRoot" -ForegroundColor Gray

Write-Host "检查 MySQL(3306) 与 MQTT(1883)..." -ForegroundColor Yellow
$ports = netstat -ano 2>$null | Select-String -Pattern ":3306|:1883"
if (-not ($ports -match ":3306")) {
    Write-Warning "未检测到 3306 监听，请先启动 MySQL 并创建库 device（见 MD/03-实施部署/完整部署指南.md）。"
}
if (-not ($ports -match ":1883")) {
    Write-Warning "未检测到 1883 监听，请先启动 Mosquitto/EMQX 等 MQTT Broker。"
}

# InfluxDB：优先环境变量，其次常见安装路径
$InfluxCandidates = @(
    $env:INFLUXDB2_HOME,
    "C:\Users\JERRY\influxdb2\influxdb2_windows_amd64",
    (Join-Path $DeployRoot "tools\influxdb2_windows_amd64")
) | Where-Object { $_ -and (Test-Path (Join-Path $_ "influxd.exe")) }

if ($InfluxCandidates.Count -gt 0) {
    $InfluxDir = $InfluxCandidates[0]
    Write-Host "启动 InfluxDB: $InfluxDir" -ForegroundColor Yellow
    Start-Process (Join-Path $InfluxDir "influxd.exe") -WorkingDirectory $InfluxDir
    Start-Sleep -Seconds 2
} else {
    Write-Warning "未找到 influxd.exe。请安装 InfluxDB 2.x 并设置 INFLUXDB2_HOME，或手动启动后再运行本脚本。"
}

$BackendDir = Join-Path $DeployRoot "dev_back_end\dev"
$ExePath = Join-Path $BackendDir "dev.exe"
Write-Host "编译并启动后端..." -ForegroundColor Yellow
Push-Location $BackendDir
try {
    go build -o dev.exe main.go
    if (-not (Test-Path $ExePath)) { throw "go build 未生成 dev.exe" }
    Start-Process $ExePath -WorkingDirectory $BackendDir
    Start-Sleep -Seconds 3
} finally {
    Pop-Location
}

$FrontDir = Join-Path $DeployRoot "4G_dev_front\4G_dev"
Write-Host "启动前端 (Vite 端口见 vite.config.js，当前多为 4325)..." -ForegroundColor Yellow
Push-Location $FrontDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "npm install..." -ForegroundColor Cyan
        npm install
    }
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$FrontDir'; npm run dev"
} finally {
    Pop-Location
}

$SimDir = Join-Path $DeployRoot "simulator_v3"
Write-Host "启动模拟器..." -ForegroundColor Yellow
Push-Location $SimDir
try {
    if (-not (Test-Path "venv")) {
        Write-Host "创建 Python venv..." -ForegroundColor Cyan
        python -m venv venv
    }
    $pip = Join-Path $SimDir "venv\Scripts\pip.exe"
    & $pip install -q -r requirements.txt
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$SimDir'; .\venv\Scripts\Activate.ps1; python main.py"
} finally {
    Pop-Location
}

Write-Host "已尝试启动各组件。" -ForegroundColor Green
Write-Host "前端: http://localhost:4325/ （以 vite.config.js 为准）" -ForegroundColor Cyan
Write-Host "后端: http://127.0.0.1:8000/swagger/" -ForegroundColor Cyan
Write-Host "InfluxDB UI: http://127.0.0.1:8086/" -ForegroundColor Cyan
