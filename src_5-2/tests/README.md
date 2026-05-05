# 测试脚本目录

## 概述
所有项目测试脚本位于此目录，用于验证功能完整性。

## 测试脚本列表
| 脚本 | 功能 | 说明 |
|------|------|------|
| e2e_test.py | 端到端完整流程测试 | 测试从配置到数据上报完整流程 |
| run_e2e_test.py | 运行 E2E 测试 | 快速运行端到端测试 |
| test_backend_api.py | 后端 API 测试 | 测试 HTTP 接口响应 |
| test_config_down.py | 配置下发测试 | 测试模组配置和数据配置下发 |
| test_data_query.py | 数据查询测试 | 测试数据查询与历史数据功能 |
| test_fix.py | 修复测试 | 临时测试脚本 |
| test_full_flow.py | 完整流程测试 | 完整流程综合测试 |
| test_getvariables.py | 变量查询测试 | 测试变量查询与管理 |
| test_mqtt.py | MQTT 通信测试 | 测试 MQTT 发布和订阅 |

## 运行测试
```bash
# 运行单个测试
python test_full_flow.py

# 运行 E2E 测试
python run_e2e_test.py
```

## 前置条件
- 后端服务运行在 8000 端口
- MQTT Broker 运行在 1883 端口
- （可选）模拟器运行
