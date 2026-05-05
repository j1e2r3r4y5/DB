# 发送模式和数据配置 方案2 改造计划

## 📋 现状分析

### 当前架构

* **后端框架**: GoFrame

* **通信方式**: MQTT

* **时序数据库**: InfluxDB

* **前端框架**: Vue3 + Element Plus

### 当前方案（方案1）

* 前端直接构造十六进制字符串

* 通过 `/payload` 接口下发

* 后端直接转发给设备

### 被注释的方案2

* `sendcod.go` 中有被注释的 JSON 结构体方案

* 服务层接口 `IsendCod` 是空的

***

## 🎯 改造目标

将**模组配置**和**数据配置**均改为使用**方案2（JSON结构体）**，同时：

1. ✅ 保持**向后兼容**（原方案1继续可用）
2. ✅ 协议构建逻辑**完全放在后端**
3. ✅ 预留**优化算法接口**

***

## 📁 文件清单

### 1. API 层（api/dev/v1/payload.go）

**新增接口定义**:

* `SendModuleConfigReq` - 下发模组配置请求

* `SendDataConfigReq` - 下发数据配置请求

* `QueryDataConfigReq` - 查询数据配置请求

* `RemoteWriteReq` - 远程置数请求

### 2. 服务层（internal/service/）

* **sendcod.go** - 完善 `IsendCod` 接口

* **mqtt.go** - 新增 `PublishBytes` 方法（简化发送字节数组）

### 3. 逻辑层（internal/logic/）

* **sendcod.go** - 实现完整功能：

  * 模组配置编码

  * 数据配置编码（含合并/分割算法框架）

  * 查询配置编码

  * 远程置数编码

* **mqtt.go** - 实现 `PublishBytes` 方法

### 4. 控制器层（internal/controller/payload.go）

* 新增对应接口处理函数

### 5. 模型层（internal/model/sendcod.go）

* 补充完善结构体（已有基础，可复用）

***

## 🔧 详细实现步骤

### 步骤 1: 完善 MQTT 服务（添加便捷方法）

**文件**: `internal/service/mqtt.go` + `internal/logic/mqtt.go`

* 在 `IMqtt` 接口新增 `PublishBytes(topic string, payload []byte) error`

* 在 `sMqtt` 实现该方法

* **原因**: 当前 `SendMessage` 签名需要 client 和 msg 对象，使用不便

### 步骤 2: 完善服务层接口

**文件**: `internal/service/sendcod.go`

* 在 `IsendCod` 接口定义方法：

  ```go
  SendModuleConfig(ctx context.Context, req *model.ModbusRequest) error
  SendDataConfig(ctx context.Context, req *model.ModbusRequest) error
  QueryDataConfig(ctx context.Context, devSerial string) error
  RemoteWrite(ctx context.Context, req *model.ModbusRequest) error
  ```

### 步骤 3: 实现协议编码逻辑（核心）

**文件**: `internal/logic/sendcod.go`

* 取消注释并完善代码

* 实现 `encodeModuleConfig` - 功能码 02 编码

* 实现 `encodeDataConfig` - 功能码 04 编码（含算法框架）

* 实现 `encodeQueryConfig` - 功能码 03 编码

* 实现 `encodeRemoteWrite` - 功能码 06 编码

### 步骤 4: 新增 API 接口定义

**文件**: `api/dev/v1/payload.go`

* 新增四个接口的 Request/Response 结构

### 步骤 5: 实现控制器层

**文件**: `internal/controller/payload.go`

* 新增四个接口处理函数

***

## 🧠 数据配置优化算法框架

### 算法预留设计

在 `sendcod.go` 中定义：

```go
// DataConfigOptimizer 数据配置优化器
type DataConfigOptimizer interface {
    // Optimize 优化数据配置项
    Optimize(items []model.Entry) ([]model.Entry, error)
}

// DefaultOptimizer 默认优化器（当前按站号+分区简单合并）
type DefaultOptimizer struct{}
```

### 可扩展点

* ✅ 地址合并（连续地址合并）

* ✅ 包大小分割（超过最大包长时分割）

* ✅ 优先级排序

* ✅ 缓存优化

***

## 🔄 向后兼容策略

### 共存方案

* **原方案1接口** (`/payload`): 继续保留，原样工作

* **新方案2接口** (`/sendcod/xxx`): 新增JSON接口

* 前端可以**逐步迁移**或同时使用

***

## 📊 影响范围

| 层级   | 修改内容   | 风险   |
| ---- | ------ | ---- |
| API层 | 新增接口定义 | 🟢 低 |
| 服务层  | 新增接口方法 | 🟢 低 |
| 逻辑层  | 实现协议编码 | 🟡 中 |
| 控制器  | 新增接口处理 | 🟢 低 |
| 前端   | 可选迁移   | 🟢 低 |

***

## ✅ 验收标准

1. ✅ 原 `/payload` 接口继续正常工作
2. ✅ 新 JSON 接口能正常下发配置
3. ✅ 设备能正常响应新接口下发的指令
4. ✅ 代码结构清晰，预留优化算法接口

***

## 📝 后续优化建议（可选）

完成方案2改造后，可考虑：

1. 前端迁移到新接口
2. 实现真正的数据配置优化算法
3. 添加单元测试覆盖协议编码逻辑
4. 添加配置下发结果的同步等待机制

