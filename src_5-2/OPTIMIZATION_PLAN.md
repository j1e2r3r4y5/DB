# 工业物联网平台优化方案

**最后更新**: 2026-05-10

---

## 概览

| 优化项 | 优先级 | 状态 |
|--------|--------|------|
| 完整测试体系 | P0 | ✅ 已完成 |
| 安全加固体系 | P0 | 📋 未来规划 |
| 监控告警体系 | P0 | ✅ 已完成 |
| 性能优化 | P1 | ✅ 已完成 |
| 模拟器增强 | P1 | 📋 方案已制定 |

---

## 🎯 P0：高优先级

### 1. 完整测试体系 ✅ **已完成**

**已实施内容**:
- 新增 `utility/datatype_codec_test.go` - 覆盖所有数据类型编解码
- 完善 `logic/sendcod_test.go` - 11 个测试用例（含边界条件和性能基准）
- 修复 `simulator_v1536/tests/` - 10 个测试文件导入路径修复
- 修复 `simulator_v1536/data/address_segment.py` - unit/init_value 字段解析修复

**测试覆盖**:
- ✅ 数据类型信息获取
- ✅ Bool/Int16/Int32/Float32/Float64/String 编解码
- ✅ 通用数据编解码
- ✅ 寄存器数计算
- ✅ 边界条件处理
- ✅ 优化算法基准测试（10/50/100 变量规模）

```bash
cd dev_back_end/dev && go test -v ./...
```

---

### 2. 监控告警体系 ✅ **已完成**

整合到现有 Vue 管理平台内部，无需外部依赖。

#### 已实施内容

**后端 - 监控模块** (`internal/logic/monitor/`):

| 文件 | 功能 |
|------|------|
| `health.go` | 健康检查器：检查 MySQL/Redis/InfluxDB/MQTT 连接状态 |
| `metrics.go` | 指标收集器：设备在线数、MQTT 消息数、数据点计数 |
| `alert.go` | 告警通知：钉钉机器人通知，防告警风暴 |

**后端 - API 端点**:

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 服务健康检查（返回 JSON） |
| `/stats` | GET | 系统统计数据（返回 JSON） |
| `/metrics` | GET | Prometheus 格式指标 |

**后端 - 集成点**:
- `cmd.go`: 设备离线检测（3 分钟阈值，60 秒周期）+ 设备指标更新（30 秒周期）
- `mqtt.go`: MQTT 消息收发计数 + 设备恢复在线检测

**前端 - 主页改造** (`view/home.vue`):
- 系统健康状态卡片（MySQL/Redis/InfluxDB/MQTT 状态）
- 数据统计卡片（在线/离线设备、收发消息数、数据点数、运行时间）
- 15 秒自动刷新

---

### 3. 安全加固体系 📋 **未来规划**

将在后续迭代中实现：
- API 限流防护（令牌桶算法）
- 敏感信息脱敏（日志 + API 响应）
- 操作审计日志（记录/查询/归档）

---

## 🚀 P1：中优先级

### 4. 性能优化 ✅ **已完成**

#### 已实施内容

| 优化项 | 文件 | 说明 |
|--------|------|------|
| Redis 缓存层 | `internal/logic/cache.go` | 设备信息、变量配置缓存（5 分钟 TTL） |
| 数据库查询优化 | `internal/cmd/cmd.go` | 使用 DAO Columns() 替代硬编码字段名 |
| 设备状态批量更新 | `internal/cmd/cmd.go` | 离线检测批量更新，避免 N+1 |

#### 待后续实施
- 数据库索引优化（dev_status、latest_online 等字段）
- 前端虚拟列表（大变量列表）
- MQTT 连接池

---

### 5. 模拟器增强 📋 **方案已制定**

#### 功能 1：网络异常模拟

| 场景 | 延迟 | 抖动 | 丢包 |
|------|------|------|------|
| Normal | 10ms | 5ms | 0% |
| Slow 3G | 100ms | 50ms | 2% |
| Unstable | 50ms | 200ms | 5% |

#### 功能 2：多设备并发模拟
- 批量创建设备（create_batch）
- 独立 MQTT 连接 + 独立配置
- 设备状态统一管理

#### 功能 3：协议录制回放
- 录制 MQTT 消息为 JSON
- 按时间轴精确回放
- 支持倍速、循环、方向过滤

---

## 📁 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `dev/internal/logic/monitor/health.go` | 新增 | 健康检查器 |
| `dev/internal/logic/monitor/metrics.go` | 新增 | 指标收集器 |
| `dev/internal/logic/monitor/alert.go` | 新增 | 告警通知器 |
| `dev/internal/controller/monitor.go` | 新增 | 监控控制器 |
| `dev/internal/cmd/cmd.go` | 修改 | 注册端点 + 离线检测 + 指标更新 |
| `dev/internal/logic/mqtt.go` | 修改 | 集成指标收集 + 恢复在线检测 |
| `4G_dev_front/4G_dev/src/api/index.js` | 修改 | 新增 getHealth/getStats 接口 |
| `4G_dev_front/4G_dev/src/view/home.vue` | 修改 | 监控页面改造 |
| `4G_dev_front/4G_dev/src/utils/request.js` | 不变 | 无需修改 |
| `dev/internal/logic/cache.go` | 已有 | Redis 缓存层 |
| `dev/utility/datatype_codec_test.go` | 已有 | 数据类型测试 |
| `dev/internal/logic/sendcod_test.go` | 修改 | 完善单元测试 |

---

## 📊 验证结果

### API 验证
```
GET /health → {"healthy":true,"checks":{"mysql":{"healthy":true},...}}
GET /stats  → {"devices_online":X, "mqtt_messages_received":Y, "uptime_seconds":Z}
```

### 编译验证
```bash
cd dev_back_end/dev && go build  # ✅ 通过
```

### 前端验证
```bash
cd 4G_dev_front/4G_dev && npm run dev  # ✅ http://localhost:4325
```

---

## 🔧 Bug 修复记录

| Bug | 位置 | 修复 |
|-----|------|------|
| 离线检测字段名错误 (`dev_status` → `DevStatus`) | `cmd.go` | 使用 `dao.Dev.Columns().DevStatus` |
| 前端数据映射不对（checks 包裹 + 字段名） | `home.vue` | 提取 checks + 映射 uptime_seconds |
| Python 测试导入路径错误 | 10 个测试文件 | 移除 simulator_v3 前缀 |
| address_segment unit/init_value 混淆 | `address_segment.py` | 正确分离第 7/8 列 |

---

## 📋 遗留工作

1. **P0 安全加固** - 限流、脱敏、审计日志
2. **P1 数据库索引** - 为高频查询字段添加索引
3. **P1 前端虚拟列表** - 大变量列表滚动优化
4. **P1 MQTT 连接池** - 高并发消息处理
5. **P1 模拟器增强** - 网络模拟、多设备、录制回放