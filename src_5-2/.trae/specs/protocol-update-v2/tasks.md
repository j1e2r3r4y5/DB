# 任务列表 - 4G DTU 通信协议更新 (v2)

## 任务1: 协议变更分析

- [x] 1.1: 对比 doc_.md 与 agreement.md 协议差异
- [x] 1.2: 识别核心变更点 (0x05 数据格式)
- [x] 1.3: 梳理 Modbus 区域定义表
- [x] 1.4: 确认代码实现与新协议的一致性

## 任务2: 代码实现验证

- [x] 2.1: 验证 payload.go 中 0x05 解析逻辑
- [x] 2.2: 确认 DataItem 结构体包含 SlaveAddr 和 ModbusType
- [x] 2.3: 验证 readBytes 计算正确性
- [x] 2.4: 验证数据写入 InfluxDB 的完整性

## 任务3: Bug 修复

- [x] 3.1: 修复 ModbusType=0 支持 (将 case 1,2 改为 case 0,1)
- [x] 3.2: 添加 default case 处理未知类型
- [x] 3.3: 修复 baseAddr 变量作用域问题
- [x] 3.4: 验证编译通过

## 任务4: 注释和日志增强

- [x] 4.1: 添加 Modbus 区域定义注释 (0x03, 0x05)
- [x] 4.2: 更新日志输出包含完整字段信息
- [x] 4.3: 添加不支持类型的警告日志

## 任务5: 验证检查

- [x] 5.1: `go build` 编译验证通过
- [x] 5.2: 代码审查确认符合新协议
- [x] 5.3: 协议合规性检查表确认

---

## 关键代码变更点

### internal/logic/payload.go

#### 第278-288行 - ModbusType 值计算
```go
// 修改前
case 1, 2:
    valueLen = (length + 7) / 8

// 修改后
case 0, 1:
    valueLen = (length + 7) / 8
default:
    g.Log().Warning(ctx, "不支持的Modbus数据类型:", ...)
    readBytes += 6
    continue
```

#### 第291行 - 数据处理分支
```go
// 修改前
if ModbusType[0] == 1 || ModbusType[0] == 2 {
    // 线圈，按位拆分

// 修改后
if ModbusType[0] == 0 || ModbusType[0] == 1 {
    // 线圈/离散输入，按位拆分
```

#### 第289行 - 日志增强
```go
g.Log().Debug(ctx, "数据上发项",
    "从站地址:", slaveAddr[0],
    "Modbus类型:", ModbusType[0],
    "（0=线圈,1=离散输入,3=输入寄存器,4=保持寄存器）",
    "数据地址:", baseAddr,
    "数据长度:", length)
```

---

## 任务完成状态

| 任务 | 状态 | 完成时间 |
|------|------|----------|
| 任务1 | ✅ 完成 | - |
| 任务2 | ✅ 完成 | - |
| 任务3 | ✅ 完成 | - |
| 任务4 | ✅ 完成 | - |
| 任务5 | ✅ 完成 | - |

**总计**: 5/5 任务完成
