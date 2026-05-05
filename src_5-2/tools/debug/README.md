# 调试工具目录

## 概述
所有调试工具位于此目录，用于检查数据、排查问题。

## 工具列表
| 工具 | 功能 | 说明 |
|------|------|------|
| check_all.py | 全面检查 | 检查数据库、InfluxDB、设备状态等 |
| check_cache_vars.go | 检查缓存变量 | （Go 语言）检查缓存中的变量 |
| check_current_vars.py | 检查当前变量 | 查看当前数据库中的变量配置 |
| check_db_variables.py | 检查数据库变量 | 详细检查变量配置 |
| check_db_vars.py | 检查数据库变量 | 另一个变量检查脚本 |
| check_influx.ps1 | 检查 InfluxDB | PowerShell 脚本检查 InfluxDB 数据 |
| check_user.py | 检查用户 | 检查用户信息 |
| check_vars.py | 检查变量 | 快速检查变量 |
| check_vars_now.py | 实时检查变量 | 检查当前变量状态 |
| check_vars_struct.py | 检查变量结构 | 检查变量结构定义 |
| checkvars.py | 检查变量 | 变量检查脚本（旧版） |
| clean_and_readd_vars.py | 清理并重添变量 | 清空变量后重新添加 |
| clear_influxdb.py | 清空 InfluxDB | 清空 InfluxDB 中的测试数据 |
| debug_data.go | 调试数据 | （Go 语言）数据调试工具 |
| fix_and_deploy.py | 修复并部署 | 问题修复与部署脚本 |
| quick_check.py | 快速检查 | 快速健康检查 |
| quick_test.py | 快速测试 | 快速功能测试 |
| send_data_config.py | 发送数据配置 | 直接发送数据配置到设备 |
| test_mqtt_publish.go | 测试 MQTT 发布 | （Go 语言）MQTT 发布测试 |
| archive/ | 归档目录 | 存放历史日志文件 |

## 使用说明
```bash
# Python 工具
python quick_check.py

# PowerShell 工具
.\check_influx.ps1

# Go 工具（需编译）
go run check_cache_vars.go
```
