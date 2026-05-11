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
| `dev_back_end/dev/` | 后端服务（Go+GoFrame v2.9.0，端口 8000） | [README.MD](dev_back_end/dev/README.MD) |
| `4G_dev_front/4G_dev/` | 前端界面（Vue3+Vite+ElementPlus，端口 4325） | [README.md](4G_dev_front/4G_dev/README.md) |
| `simulator_v1536/` | DTU+Modbus 模拟器（Python，113测试通过） | [README.md](simulator_v1536/README.md) |

### 工具与测试
| 目录 | 说明 | 文档链接 |
|------|------|----------|
| `tests/` | 测试脚本集合（9个） | [README.md](tests/README.md) |
| `tools/debug/` | 调试工具集合（19个） | [README.md](tools/debug/README.md) |
| `tools/deploy/` | 部署工具集合（4个，含一键启动脚本） | [README.md](tools/deploy/README.md) |
| `docs/` | 数据库 SQL 脚本 | - |

### 文档
| 目录 | 说明 | 文档链接 |
|------|------|----------|
| `MD/` | 项目需求、决策、测试等文档（5大类） | [README.md](MD/README.md) |
| `.trae/` | Trae IDE 规范、计划文档（含页面拆分设计） | - |

---

## 📖 项目概述
这是一个基于 **Modbus + MQTT** 的工业物联网设备管理平台，包含：
- **后端服务**：Go + GoFrame (gogf) 框架
- **前端界面**：Vue3 + ElementPlus + Vite
- **模拟设备**：Python 实现的 DTU+Modbus 设备模拟器

> 📚 **推荐阅读**：[完整需求设计文档](MD/01-需求设计/DTU+Modbus模拟器需求设计文档-完整版.md)

---

## 🏗️ 技术架构

### 后端
- **框架**：GoFrame (gogf) v2
- **数据库**：MySQL 8.0 (关系型) + InfluxDB 2.x (时序型)
- **通信**：MQTT (与设备通信，远程 Broker)
- **缓存**：Redis

### 前端
- **框架**：Vue3 + Vite
- **UI库**：ElementPlus
- **HTTP请求**：Axios

### 模拟设备
- **语言**：Python3
- **MQTT库**：paho-mqtt
- **Modbus库**：自研 TCP Master/Slave

### 流量优化算法
- **Python原型**：`ML307DC-CN上发流量与存储联合优化方案/`（5阶段完整算法）
- **Go后端集成**：`dev_back_end/dev/internal/logic/sendcod.go` → PayloadOptimizer
- **优化效果**：原始 83950 字节 → 优化后 24670 字节（节省 70.6%）

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

> ⚠️ **协议修正（v1.8.0）**：03/04/05 功能码中"2字节数据数量"字段实际含义为"报文总长度"，详见 [agreement.md](dev_back_end/dev/resource/配置文件/agreement.md)

| 功能码 | 方向 | 说明 | 前端组件 | 后端接口 |
|--------|------|------|----------|----------|
| **0x00** | 上行 | 心跳包（设备 → 平台） | （自动处理） | payload.go |
| **0x01** | 双向 | 模组配置查询/上报 | （设备端） | payload.go |
| **0x02** | 双向 | 模组配置下发/结果 | DeviceDownDialog.vue | /sendcod/module-config |
| **0x03** | 双向 | 数据配置查询/上报 | Features.vue | /sendcod/query-config |
| **0x04** | 双向 | 数据配置下发/结果 | Features.vue | /sendcod/data-config |
| **0x05** | 上行 | 数据上报（设备 → 平台） | （自动处理） | payload.go |
| **0x06** | 双向 | 远程置数/结果 | RemoteWriteDialog.vue | /sendcod/remote-write |

### 协议结构（v1.8.0 后）

| 功能码 | 报文结构 |
|--------|---------|
| 03 上发 | 1字节功能码 + **2字节报文总长度** + N×6字节数据项 |
| 04 下发 | 1字节功能码 + **2字节报文总长度** + N×6字节数据项 |
| 05 上发 | 1字节功能码 + **2字节报文总长度** + 变长数据项列表 |

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
| **导入变量** | 支持文件上传、粘贴文本、Seed生成三种方式 |
| **批量删除** | 多选后批量删除，二次确认，部分失败不影响其他 |
| **全选计数修复** | syncSelection() 确保刷新后选中数量准确 |
| **序列号校验** | handleShowFeatures/handleShowImport 校验设备SN |
| **文件位置** | 4G_dev_front/src/components/variables/variables.vue |

### data/data.vue（数据管理）
| 功能 | 说明 |
|------|------|
| **默认显示** | 只显示已下发配置的变量（从localStorage读取activeVariableIds） |
| **空配置时** | 显示"暂无数据"提示 |
| **显示所有变量** | 可以勾选"显示所有变量"查看全部变量 |
| **数据显示** | 显示变量名称、数据类型、数据值、最新上传时间 |
| **自动刷新** | 3秒轮询，加载中跳过防止重叠请求 |
| **多条件排序** | 支持按时间（Date.parse数字排序）、数值（_sortNum预计算）排序 |
| **加载状态** | v-loading 显示"数据加载中..." |
| **文件位置** | 4G_dev_front/src/components/data/data.vue |

### admin/UserList.vue（用户列表）
| 功能 | 说明 |
|------|------|
| **用户类型** | 超级管理员(Type=0)、系统管理员(Type=1)、设备管理员(Type=2)、普通用户(Type=3) |
| **操作按钮** | 修改（跳转至/home/users/edit/{id}）、删除（确认弹窗） |
| **权限判断** | Type=0全部可编辑，Type=1可编辑Type>=2的用户和自己 |
| **文件位置** | 4G_dev_front/src/components/admin/UserList.vue |

### admin/UserModify.vue（修改用户）
| 功能 | 说明 |
|------|------|
| **双入口** | 有userId参数直接加载，无参数时显示用户选择器 |
| **类型修改** | 集成授权功能，修改类型时同步调用Changeuser+Permuser |
| **权限控制** | canChangeType计算属性防止越权修改类型 |
| **文件位置** | 4G_dev_front/src/components/admin/UserModify.vue |

### admin/UserCreate.vue（新建用户）
| 功能 | 说明 |
|------|------|
| **创建表单** | 用户名、密码、昵称、用户类型 |
| **权限校验** | 超级管理员可创建所有类型，系统管理员可创建Type>=2的用户 |
| **文件位置** | 4G_dev_front/src/components/admin/UserCreate.vue |

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
ML307C设备 / 模拟器（simulator_v3）
  ↓
  定时采集 Modbus 数据（间隔由0x04配置）
  ↓
  构造数据包（0x05 + 报文总长度 + 变长数据项）→ MQTT(QoS2) 发送到 /dtu/{序列号}/up
  ↓
  后端（mqtt.go → messageHandler）
  ↓
  payload.go → PayloadHandler
  ↓
  解析功能码 0x05 → 按变量缓存表匹配解析
  ↓
  写入 InfluxDB（DataItem measurement）
  ↓
  前端（轮询刷新）→ 调用 /dataquery → 显示最新数据
```

### 3. 沙箱数据流（v1.9.0 新增）
```
前端（导入变量到沙箱环境）
  ↓
  沙箱变量自动标记 scope=sandbox
  ↓
  后端（mqtt.go → 独立 MQTT 主题 /dtu/{serial}/sandbox/{up|down}）
  ↓
  模拟器（simulator_v1536）生成模拟数据上报
  ↓
  写入 InfluxDB（scope=sandbox 标签，与 scope=production 隔离）
  ↓
  前端（data.vue 沙箱标签页）→ POST /sandbox/dataquery
```

### 4. 离线检测机制（v1.8.0 新增）
```
后台定时任务（每60秒执行）:
  ↓
  检查所有设备: dev_status=1 AND latest_online < 当前时间-3分钟
  ↓
  符合条件的设备 → 更新 dev_status=0（离线）
  ↓
  前端刷新 → 显示设备离线
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
cd simulator_v1536
python main.py
# 默认连接 127.0.0.1:1883
```

也可使用一键启动脚本：
```powershell
python start_simulator.py
```

### 4. MQTT Broker
默认连接远程 MQTT Broker（112.6.224.25:20042），也支持本地部署。

> 注意：生产环境使用远程 Broker，需确保网络可达。

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
| internal/logic/payload.go | 协议解析与处理（上行，含解析增强逻辑 WriteEnhancedDataToInflux） |
| internal/logic/sendcod.go | 协议编码与发送（下行，方案2）、PayloadOptimizer 优化器 |
| internal/logic/mqtt.go | MQTT 连接管理 |
| internal/controller/payload.go | HTTP 接口实现（含 InfluxDB 查询） |
| internal/cmd/cmd.go | 启动入口、离线检测定时任务 |
| utility/datatype_codec.go | 数据类型编解码（bool/int16/int32/float32/float64/string） |
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
| 版本 | 时间 | 说明 |
|------|------|------|
| **v1.10.0** | 2026-05-10 | P0优化完成：前后端优化前基准对齐、PayloadOptimizer单元测试(20.7%覆盖率)、Python模拟器113测试全部通过 |
| **v1.9.0** | 2026-05-09 | 沙箱功能（独立MQTT主题、scope标签隔离、/sandbox/dataquery API）、用户管理拆分为3个子页面 |
| **v1.8.0** | 2026-05-09 | 协议修正（"数据数量"→"报文总长度"）、离线检测机制（3分钟超时）、修复除零问题 |
| - | 2026-05-05 | 修复SendDataConfig API的空配置验证、前端空配置二次确认弹窗 |
| - | 2026-05-05 | data.vue默认只显示已下发配置的变量、修复导入变量/批量删除功能 |
| - | 2026-05-04 | 全部前端组件迁移到方案2、PayloadOptimizer框架、项目结构整理 |

---

