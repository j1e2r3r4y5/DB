
# 完整一键启动脚本 - 启动所有组件
Write-Host "🚀 开始启动完整系统..." -ForegroundColor Green

# 1. 启动 InfluxDB
Write-Host "📊 启动 InfluxDB..." -ForegroundColor Yellow
cd "c:\Users\JERRY\influxdb2\influxdb2_windows_amd64"
Start-Process ".\influxd.exe"

# 给 InfluxDB 一点启动时间
Start-Sleep -Seconds 2

# 2. 启动后端（用编译好的 exe，最快）
Write-Host "🔧 启动后端服务..." -ForegroundColor Yellow
cd "c:\Users\JERRY\Desktop\gp\src_5-2\dev _back_end\dev"
Start-Process ".\dev.exe"

# 给后端一点启动时间
Start-Sleep -Seconds 3

# 3. 启动前端
Write-Host "🌐 启动前端..." -ForegroundColor Yellow
cd "c:\Users\JERRY\Desktop\gp\src_5-2\4G_dev_front\4G_dev"
# 检查 node_modules 是否存在
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 首次启动，需要安装依赖..." -ForegroundColor Cyan
    npm install
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

# 4. 启动模拟器
Write-Host "🤖 启动 DTU+Modbus 模拟器..." -ForegroundColor Yellow
cd "c:\Users\JERRY\Desktop\gp\src_5-2\simulator_v3"
# 检查虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "🐍 首次启动，需要创建 Python 虚拟环境..." -ForegroundColor Cyan
    python -m venv venv
}
# 激活虚拟环境并运行
Start-Process powershell -ArgumentList "-NoExit", "-Command", "venv\Scripts\Activate; python main.py"

Write-Host "✅ 所有组件启动完成！" -ForegroundColor Green
Write-Host "🌐 前端地址: http://localhost:4326/" -ForegroundColor Cyan
Write-Host "🔧 后端地址: http://localhost:8000/" -ForegroundColor Cyan
Write-Host "📊 InfluxDB: http://localhost:8086/" -ForegroundColor Cyan
