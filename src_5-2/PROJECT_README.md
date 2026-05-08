# 项目说明文档

---

## 📋 目录
1. [项目概述](#项目概述)
2. [项目结构快速索引](#项目结构快速索引)
3. [技术架构](#技术架构)
4. [方案对比（已切换到方案2）](#方案对比已切换到方案2)
5. [功能码说明](#功能码说明)
6. [后端接口说明](#后端接口说明)
7. [前端组件说明](#前端组件说明)
8. [数据流向完整流程](#数据流向完整流程)
9. [快速启动指南](#快速启动指南)

---

## 📁 项目结构快速索引

### 核心模块
| 目录 | 说明 | 文档链接 |
|------|------|----------|
| `dev_back_end/dev/` | 后端服务（Go+GoFrame） | [README.MD](dev_back_end/dev/README.MD) |
| `4G_dev_front/4G_dev/` | 前端界面（Vue3+ElementPlus） | [README.md](4G_dev_front/4G_dev/README.md) |
| `simulator_v3/` | DTU+Modbus 模拟器 | [README.md](simulator_v3/README.md) |

### 工具与测试
| 目录 | 说明 | 文档链接 |
|------|------|----------|
| `tests/` | 测试脚本集合（9个） | [README.md](tests/README.md) |
| `tools/debug/` | 调试工具集合（19个） | [README.md](tools/debug/README.md) |
| `tools/deploy/` | 部署工具集合（4个） | [README.md](tools/deploy/README.md) |

### 文档
| 目录 | 说明 | 文档链接 |
|------|------|----------|
| `MD/` | 项目需求、决策、测试等文档 | [README.md](MD/README.md) |
| `.trae/` | Trae IDE 规范、计划文档 | - |

---

## 📖 项目概述
这是一个基于 **Modbus + MQTT** 的工业物联网设备管理平台，包含：
- **后端服务**：Go + gogf 框架
- **前端界面**：Vue3 + ElementPlus
- **模拟设备**：Python 实现的 Modbus 设备模拟器

> 📚 **推荐阅读**：[完整需求设计文档](MD/01-需求设计/DTU+Modbus模拟器需求设计文档-完整版.md)

---

## 🏗️ 技术架构

### 后端
- **框架**：GoFrame (gogf)
- **数据库**：SQLite (关系型) + InfluxDB (时序型)
- **通信**：MQTT (与设备通信)

### 前端
- **框架**：Vue3 + Vite
- **UI库**：ElementPlus
- **HTTP请求**：Axios

### 模拟设备
- **语言**：Python3
- **MQTT库**：paho-mqtt

---

## ⚡ 方案对比（已切换到方案2）

### ✅ 方案2（推荐，当前在用）
| 项目 | 说明 |
|------|------|
| **模式** | 前端传 JSON → 后端协议编码 → MQTT 发送 |
| **优势** | 前后端解耦、协议细节封装在后端、可扩展（优化算法、参数校验） |
| **使用范围** | 所有新功能都用这个 |
| **关键接口** | /sendcod/module-config、/sendcod/data-config 等 |

### 🔴 方案1（保留，兼容用）
| 项目 | 说明 |
|------|------|
| **模式** | 前端直接构造 Hex 字符串 → 后端透传 MQTT |
| **优势** | 灵活、直接 |
| **使用范围** | 仅保留接口兼容，不做新开发 |
| **关键接口** | /payload |

---

## 📌 功能码说明

| 功能码 | 方向 | 说明 | 前端组件 | 后端接口 |
|--------|------|------|----------|----------|
| **0x00** | 上行 | 心跳包（设备 → 平台） | （自动处理） | payload.go |
| **0x01** | 双向 | 模组配置查询/上报 | （设备端） | payload.go |
| **0x02** | 双向 | 模组配置下发/结果 | DeviceDownDialog.vue | /sendcod/module-config |
| **0x03** | 双向 | 数据配置查询/上报 | Features.vue | /sendcod/query-config |
| **0x04** | 双向 | 数据配置下发/结果 | Features.vue | /sendcod/data-config |
| **0x05** | 上行 | 数据上报（设备 → 平台） | （自动处理） | payload.go |
| **0x06** | 双向 | 远程置数/结果 | RemoteWriteDialog.vue | /sendcod/remote-write |

---

### 发送模式说明

当前仅支持以下发送模式：

| 模式值 | 名称 | 说明 |
|-------|------|------|
| 0x00 | 定时发送 | 根据配置的发送间隔定期上报数据 |

其他模式（线圈置位、寄存器变化）暂未实现，因此前端已禁用这些选项。

---

## 🔧 后端接口说明

### 方案2 接口（推荐用）
| 方法 | URL | 说明 |
|------|-----|------|
| POST | /sendcod/module-config | 下发模组配置（功能码 0x02） |
| POST | /sendcod/data-config | 下发数据配置（功能码 0x04） |
| POST | /sendcod/query-config | 查询数据配置（功能码 0x03） |
| POST | /sendcod/remote-write | 远程置数（功能码 0x06） |

### 方案1 接口（保留）
| 方法 | URL | 说明 |
|------|-----|------|
| POST | /payload | 透传 Hex 字符串（兼容用） |

---

## 🎨 前端组件说明

### DeviceDownDialog.vue（设备配置弹窗）
| 功能 | 说明 |
|------|------|
| **配置项** | 发送模式（仅支持"定时发送"）、发送间隔、波特率 |
| **接口** | api.sendModuleConfig |
| **文件位置** | 4G_dev_front/src/components/DeviceDownDialog.vue |

### variables/Features.vue（变量管理）
| 功能 | 说明 |
|------|------|
| **0x03 查询** | 查询当前数据配置 |
| **0x04 下发** | 下发选中的数据配置（只下发用户勾选的变量） |
| **空配置下发** | 支持下发空配置（不勾选任何变量），会弹窗二次确认，清空所有数据采集配置，停止设备上报数据 |
| **Payload Key 检测** | 基于 localStorage 缓存，精确判断 payload 是否变化（变量名变化不影响） |
| **05长度计算** | 详细展示分组信息、寄存器数量、字节计算过程 |
| **activeVariableIds** | 下发成功后会保存 activeVariableIds 到 localStorage，供数据管理页面使用 |
| **接口** | api.queryDataConfig、api.sendDataConfig |
| **文件位置** | 4G_dev_front/src/components/variables/Features.vue |

### variables/variables.vue（变量列表）
| 功能 | 说明 |
|------|------|
| **变量勾选** | 用户勾选变量后，点击"下发"只下发选中的变量 |
| **有修改操作提示** | 基于 Payload Key 变化判断，变量名变化不会触发 |
| **下发按钮** | 依赖 hasPayloadChanged 计算属性，payload 无变化时禁用 |
| **空配置提示** | 未勾选变量时显示"将下发空配置" |
| **文件位置** | 4G_dev_front/src/components/variables/variables.vue |

### data/data.vue（数据管理）
| 功能 | 说明 |
|------|------|
| **默认显示** | 只显示已下发配置的变量（从localStorage读取activeVariableIds） |
| **空配置时** | 显示"暂无数据"提示 |
| **显示所有变量** | 可以勾选"显示所有变量"查看全部6个变量 |
| **数据显示** | 显示变量名称、数据类型、数据值、最新上传时间、操作等 |
| **文件位置** | 4G_dev_front/src/components/data/data.vue |

### variables/RemoteWriteDialog.vue（远程置数）
| 功能 | 说明 |
|------|------|
| **0x06 置数** | 向 Modbus 寄存器/线圈写入数据 |
| **接口** | api.remoteWrite |
| **文件位置** | 4G_dev_front/src/components/variables/RemoteWriteDialog.vue |

---

## 📊 数据流向完整流程

### 1. 下行（平台 → 设备）示例：下发模组配置（0x02）
```
前端（DeviceDownDialog.vue）
  ↓
  输入发送间隔、波特率（发送模式固定为定时发送）
  ↓
  调用 api.sendModuleConfig({ devSerial, sendMode, configData, baudRate })
  ↓
  后端（payload.go → SendModuleConfig）
  ↓
  协议编码（sendcod.go → encodeModuleConfig）
  ↓
  MQTT 发送（/dtu/{设备序列号}/down）
  ↓
  模拟设备（simulator_v3）
  ↓
  应用配置 → 发送结果到 /dtu/{设备序列号}/up
  ↓
  后端（payload.go → PayloadHandler）
  ↓
  解析结果 → 更新数据库 → 写入 InfluxDB
```

### 2. 上行（设备 → 平台）示例：数据上报（0x05）
```
模拟设备（simulator_v3）
  ↓
  定时 30s 采集 Modbus 数据
  ↓
  构造数据包（0x05） → MQTT 发送到 /dtu/{设备序列号}/up
  ↓
  后端（mqtt.go → messageHandler）
  ↓
  payload.go → PayloadHandler
  ↓
  解析功能码 0x05 → 解析变量数据
  ↓
  写入 InfluxDB（DataItem）
  ↓
  前端（刷新页面）→ 显示最新数据
```

---

## 🚀 快速启动指南

### 1. 后端服务
```bash
cd dev_back_end/dev
go run main.go
# 默认端口 8000
```

### 2. 前端服务
```bash
cd 4G_dev_front/4G_dev
npm run dev
# 默认端口 4325
```

### 3. 模拟设备
```bash
cd simulator_v3
python main.py
# 默认连接 127.0.0.1:1883
```

### 4. MQTT Broker
确保本地有 MQTT Broker 运行在 1883 端口（比如 EMQX 或 Mosquitto）

---

## 🛠️ 工具与脚本

### 快速启动
使用 PowerShell 一键启动所有服务：
```powershell
cd tools/deploy
.\start-all.ps1
```

### 测试工具
所有测试脚本位于 `tests/` 目录：
- `tests/e2e_test.py`：端到端完整流程测试
- `tests/test_data_query.py`：测试数据查询
- 更多测试脚本见 `tests/` 目录

### 调试工具
所有调试工具位于 `tools/debug/` 目录：
- 检查数据库变量、清空数据等
- 快速验证功能

---

## 📁 关键文件位置

### 后端
| 文件 | 说明 |
|------|------|
| internal/logic/payload.go | 协议解析与处理（上行） |
| internal/logic/sendcod.go | 协议编码与发送（下行，方案2） |
| internal/logic/mqtt.go | MQTT 连接管理 |
| internal/controller/payload.go | HTTP 接口实现 |
| api/dev/v1/payload.go | API 接口定义 |

### 前端
| 文件 | 说明 |
|------|------|
| api/index.js | HTTP 接口封装（包含方案2接口） |
| components/DeviceDownDialog.vue | 设备配置弹窗 |
| components/variables/Features.vue | 变量管理（数据配置） |
| components/variables/RemoteWriteDialog.vue | 远程置数 |

---

## 📝 开发注意事项

### ✅ 开发新功能
- 请用 **方案2（/sendcod/* 接口）**
- 不要在前端构造 Hex 字符串，让后端处理

### ✅ 调试
- 后端有详细日志
- 可以用模拟器测试完整流程
- 数据库查看：SQLite + InfluxDB

---

## 📌 更新日志
| 时间 | 说明 |
|------|------|
| 2026-05-05 | 修复SendDataConfig API的空配置验证问题，移除required规则 |
| 2026-05-05 | 增强Features.vue的空配置处理，添加二次确认弹窗 |
| 2026-05-05 | 优化data.vue的变量显示逻辑，默认只显示已下发配置的变量 |
| 2026-05-05 | 修复config_manager.py的空配置处理，确保触发回调 |
| 2026-05-04 | 全部前端组件迁移到方案2 |
| 2026-05-04 | 新增数据配置优化器框架 |
| 2026-05-04 | 整理项目结构，临时脚本归档到tests/和tools/目录 |

---

