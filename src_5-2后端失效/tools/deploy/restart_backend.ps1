# 结束占用 8000 的进程并重新启动后端（生成 dev.exe）
$ErrorActionPreference = "Stop"
$DeployRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Write-Host "=== 后端重启 ===" -ForegroundColor Cyan

$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $pids = $conn.OwningProcess | Sort-Object -Unique
    foreach ($procId in $pids) {
        $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "结束进程 PID=$procId ($($p.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction Stop
        }
    }
} else {
    Write-Host "8000 端口未被占用" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

$BackendDir = Join-Path $DeployRoot "dev_back_end\dev"
$ExePath = Join-Path $BackendDir "dev.exe"
Push-Location $BackendDir
try {
    go build -o dev.exe main.go
    if (-not (Test-Path $ExePath)) { throw "未生成 dev.exe" }
    Start-Process $ExePath -WorkingDirectory $BackendDir
    Write-Host "已启动: $ExePath" -ForegroundColor Green
} finally {
    Pop-Location
}

Start-Sleep -Seconds 3
$ok = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($ok) {
    Write-Host "8000 端口已监听" -ForegroundColor Green
} else {
    Write-Host "8000 仍未监听，请查看后端日志" -ForegroundColor Red
}
