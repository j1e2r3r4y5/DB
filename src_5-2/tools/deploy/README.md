# 部署工具目录

## 概述
所有部署相关的脚本位于此目录，用于快速启动和部署。

## 工具列表
| 工具 | 功能 | 说明 |
|------|------|------|
| start-all.ps1 | 一键启动所有服务 | 启动 InfluxDB、后端、前端、模拟器 |
| start-backend.ps1 | 启动后端 | 单独启动后端服务 |
| restart_backend.ps1 | 重启后端 | 停止并重新启动后端服务 |
| deploy_and_test.py | 部署并测试 | 部署后自动运行测试 |

## 使用说明
### 一键启动所有服务（推荐）
```powershell
cd tools/deploy
.\start-all.ps1
```
前提：先启动 **MySQL:3306** 与 **MQTT:1883**（见 `MD/03-实施部署/完整部署指南.md`）。

脚本会按顺序尝试启动：
1. InfluxDB（若找到 `influxd.exe` 或已设置 `INFLUXDB2_HOME`）
2. 后端（`go build` 后运行 `dev.exe`）
3. 前端（`npm run dev`，端口以 `4G_dev_front/4G_dev/vite.config.js` 为准，当前为 **4325**）
4. 模拟器（venv + `python main.py`）

### 单独启动后端
```powershell
.\start-backend.ps1
```

### 重启后端
```powershell
.\restart_backend.ps1
```

### 部署并测试
```bash
python deploy_and_test.py
```
