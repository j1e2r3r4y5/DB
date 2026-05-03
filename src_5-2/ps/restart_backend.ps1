# 重启后端服务的脚本
# 需要管理员权限运行

Write-Host "=== 4G DTU 后端服务重启脚本 ===" -ForegroundColor Cyan

# 查找占用8000端口的进程
Write-Host "`n[1] 查找占用8000端口的进程..." -ForegroundColor Yellow
$connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connection) {
    $processId = $connection.OwningProcess
    Write-Host "    找到进程 PID: $processId" -ForegroundColor White

    # 获取进程信息
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "    进程名称: $($process.ProcessName)" -ForegroundColor White
        Write-Host "    进程路径: $($process.Path)" -ForegroundColor White

        # 尝试终止进程
        Write-Host "`n[2] 尝试终止进程..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "    进程已成功终止" -ForegroundColor Green
        } catch {
            Write-Host "    无法终止进程: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "    请手动在任务管理器中结束进程，然后重新运行此脚本" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "    未发现占用8000端口的进程，服务可能未运行" -ForegroundColor Yellow
}

# 等待2秒
Start-Sleep -Seconds 2

# 启动新服务
Write-Host "`n[3] 启动后端服务..." -ForegroundColor Yellow
$servicePath = "C:\Users\Jerry\Desktop\gp\src_5-2\dev _back_end\dev\main.exe"
if (Test-Path $servicePath) {
    Write-Host "    服务路径: $servicePath" -ForegroundColor White
    Start-Process -FilePath $servicePath -WorkingDirectory "C:\Users\Jerry\Desktop\gp\src_5-2\dev _back_end\dev"
    Write-Host "    服务已启动" -ForegroundColor Green
} else {
    Write-Host "    服务可执行文件不存在: $servicePath" -ForegroundColor Red
    exit 1
}

# 等待服务启动
Start-Sleep -Seconds 3

# 验证服务状态
Write-Host "`n[4] 验证服务状态..." -ForegroundColor Yellow
$newConnection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($newConnection) {
    Write-Host "    服务已成功启动，监听端口 8000" -ForegroundColor Green
} else {
    Write-Host "    服务可能未正常启动，请检查日志" -ForegroundColor Red
}

Write-Host "`n=== 完成 ===" -ForegroundColor Cyan
