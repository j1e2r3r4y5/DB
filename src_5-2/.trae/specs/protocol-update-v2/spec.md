# 4G DTU 通信协议更新规范 (v2)

## 一、协议变更背景

### 1.1 变更原因

原始协议文件 `doc_.md` 与更新后的协议文件 `agreement.md` 存在格式差异，主要问题：

1. **0x05 数据上发格式不完整** - 旧协议缺少从站地址和 Modbus 类型字段
2. **Modbus 区域描述不明确** - 旧协议仅标注"0-4区"，新协议明确为"0134区"
3. **缺少 Modbus 区域定义** - 新协议新增了 Modbus 区域定义表格

### 1.2 协议对比分析

#### 0x00 心跳包（无变化）

| 方向 | 格式 |
|------|------|
| 上发 | `0x00` (无内容) |

#### 0x01 模组配置（描述澄清）

| 项目 | 内容 |
|------|------|
| 上发格式 | `1字节功能码 | 1字节发送模式 | 2字节配置数据 | 1字节波特率` |
| 变更 | 描述从"线圈**器**变化触发"更正为"线圈变化触发" |

#### 0x02 模组配置结果（无变化）

| 成功状态值 | 含义 |
|-----------|------|
| 0x00 | 成功 |
| 0x01 | 打开存储错误 |
| 0x02 | 写入存储失败 |
| 0x03 | 触发模式错误 |
| 0x04 | 数据接收长度错误 |
| 0x05 | 波特率配置错误 |

#### 0x03 数据配置上发（描述澄清）

| 位置 | 旧协议 | 新协议 |
|------|--------|--------|
| 第58行 | `1字节类型（0-4区）` | `1字节类型（0134区，划分参考Modbus区域定义）` |

#### 0x04 数据配置下发（描述澄清）

| 位置 | 旧协议 | 新协议 |
|------|--------|--------|
| 第60行 | `1字节类型（0-4区）` | `1字节类型（0134区，划分参考Modbus区域定义）` |

#### 0x05 数据上发 **（核心变更）**

| 版本 | 数据项格式 |
|------|-----------|
| **旧协议** | `2字节数据长度 + N字节数据` |
| **新协议** | `1字节从站地址 + 1字节数据类型 + 2字节地址 + 2字节数据长度 + N字节数据` |

**新协议完整格式**：
```
上行: 0x05 | 2字节数据数量 | {1字节从站地址 | 1字节类型 | 2字节地址 | 2字节长度 | N字节数据}...
```

#### 0x06 远程置数（无变化）

| 方向 | 格式 |
|------|------|
| 下发 | `1字节功能码 | 1字节类型 | 2字节开始地址 | 2字节数量 | 数值` |
| 上发 | `1字节功能码 | 1字节类型 | 2字节开始地址 | 2字节数量 | 1字节成功状态` |

#### 新增 Modbus 区域定义表

| 区域编号 | 官方名称 | 数据类型 | 读写权限 | 协议地址范围 |
|----------|----------|----------|----------|--------------|
| 0 区 | 线圈寄存器 (Coils) | 1位布尔值 | **可读写** | 0x0000-0xFFFF |
| 1 区 | 离散输入寄存器 | 1位布尔值 | 只读 | 0x0000-0xFFFF |
| 3 区 | 输入寄存器 | 16位字 | 只读 | 0x0000-0xFFFF |
| 4 区 | 保持寄存器 | 16位字 | **可读写** | 0x0000-0xFFFF |

## 二、代码影响分析

### 2.1 受影响文件

| 文件路径 | 影响程度 | 变更内容 |
|----------|----------|----------|
| `internal/logic/payload.go` | **高** | 0x05 解析逻辑完善、注释更新、日志增强 |
| `internal/model/payload.go` | 无 | DataItem 结构体已包含必要字段 |
| `hack/config.yaml` | 无 | 无变更 |

### 2.2 核心代码变更

#### 0x05 数据解析循环（第270-330行）

**关键变量计算**：
```go
// 每个数据项头部 = 1字节从站地址 + 1字节类型 + 2字节地址 + 2字节长度 = 6字节
// 循环条件：readBytes + 6 <= dataItemBytes

for readBytes+6 <= dataItemBytes {
    slaveAddr := scanner.Next(1)   // 从站地址
    ModbusType := scanner.Next(1)  // 数据类型 (0/1/3/4)
    dataAddr := scanner.Next(2)    // 数据地址
    dataLen := scanner.Next(2)     // 数据长度

    // 根据 ModbusType 计算数据值字节数
    switch ModbusType[0] {
    case 0, 1:           // 线圈/离散输入 - 位域
        valueLen = (length + 7) / 8
    case 3, 4:           // 寄存器 - 字
        valueLen = length * 2
    default:             // 不支持的类型 - 记录警告并跳过
        log.Warning("不支持的Modbus数据类型...")
        readBytes += 6
        continue
    }

    dataValue := scanner.Next(valueLen)  // N字节数据
    readBytes += 6 + valueLen            // 累加已读字节数
}
```

#### DataItem 结构体（已存在，无需修改）

```go
type DataItem struct {
    DevSerial  string  // 设备序列号
    SlaveAddr  int     // 从站地址 ✓
    ModbusType int     // Modbus类型 ✓
    DataAddr   int     // 数据地址
    DataLeng   int     // 数据长度
    DataValue  string  // 数据值
}
```

## 三、已实施的代码变更

### 3.1 修改记录

| 日期 | 文件 | 变更类型 | 描述 |
|------|------|----------|------|
| - | payload.go | 增强注释 | 添加 Modbus 区域定义注释 |
| - | payload.go | 增强日志 | 0x03/0x05 增加详细字段日志输出 |
| - | payload.go | Bug 修复 | 修正 ModbusType=0 的支持 |
| - | payload.go | 健壮性 | 添加 default case 处理未知类型 |

### 3.2 关键代码段

#### Modbus 类型值计算（第277-288行）

```go
var valueLen int
switch ModbusType[0] {
case 0, 1:
    valueLen = (length + 7) / 8  // 位域处理
case 3, 4:
    valueLen = length * 2          // 字处理
default:
    g.Log().Warning(ctx, "不支持的Modbus数据类型:",
        ModbusType[0], "，从站地址:", slaveAddr[0],
        "，数据地址:", baseAddr, "，跳过该数据项")
    readBytes += 6
    continue
}
```

#### 数据项处理（第291-326行）

```go
// 0/1 区：线圈/离散输入，按位拆分
if ModbusType[0] == 0 || ModbusType[0] == 1 {
    for i := 0; i < length; i++ {
        byteIndex := i / 8
        bitOffset := i % 8
        if byteIndex < len(dataValue) {
            bitVal := (dataValue[byteIndex] >> bitOffset) & 0x01
            DataItem := &model.DataItem{
                DevSerial:  devSerial,
                SlaveAddr:  int(slaveAddr[0]),
                ModbusType: int(ModbusType[0]),
                DataAddr:   baseAddr + i,
                DataLeng:   1,
                DataValue:  fmt.Sprintf("%d", bitVal),
            }
            WritdataToInflux(ctx, org, bucket, DataItem, Featurescode)
        }
    }
}
// 3/4 区：寄存器，按2字节拆分
else if ModbusType[0] == 3 || ModbusType[0] == 4 {
    for i := 0; i < length; i++ {
        offset := i * 2
        if offset+1 < len(dataValue) {
            regVal := int(dataValue[offset])<<8 | int(dataValue[offset+1])
            DataItem := &model.DataItem{
                DevSerial:  devSerial,
                SlaveAddr:  int(slaveAddr[0]),
                ModbusType: int(ModbusType[0]),
                DataAddr:   baseAddr + i,
                DataLeng:   1,
                DataValue:  fmt.Sprintf("%d", regVal),
            }
            WritdataToInflux(ctx, org, bucket, DataItem, Featurescode)
        }
    }
}
```

## 四、协议合规性确认

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 0x05 支持从站地址读取 | ✅ | `slaveAddr, _ := scanner.Next(1)` |
| 0x05 支持 ModbusType 读取 | ✅ | `ModbusType, _ := scanner.Next(1)` |
| 0x05 支持 0 区(线圈) | ✅ | `case 0, 1` |
| 0x05 支持 1 区(离散输入) | ✅ | `case 0, 1` |
| 0x05 支持 3 区(输入寄存器) | ✅ | `case 3, 4` |
| 0x05 支持 4 区(保持寄存器) | ✅ | `case 3, 4` |
| 不支持类型处理 | ✅ | default case 记录警告 |
| InfluxDB 写入 | ✅ | 包含完整 tags (slave_addr, data_type) |
| 编译通过 | ✅ | `go build` 无错误 |

## 五、测试建议

### 5.1 单元测试场景

| 场景 | 输入数据 | 预期结果 |
|------|----------|----------|
| ModbusType=0 | 线圈数据 | 正确拆分，按位写入 |
| ModbusType=1 | 离散输入数据 | 正确拆分，按位写入 |
| ModbusType=3 | 输入寄存器数据 | 正确拆分，按字写入 |
| ModbusType=4 | 保持寄存器数据 | 正确拆分，按字写入 |
| ModbusType=2 | 非法类型 | 记录 Warning，跳过该数据项 |
| 空数据 | 无数据项 | 正常返回 |
| 单数据项 | 1个完整数据项 | 正确处理 |

### 5.2 集成测试

1. 使用 MQTT 模拟器发送新协议格式数据
2. 验证 InfluxDB 中 DataItem measurement 的 tag 和 field
3. 验证前端数据展示正确

## 六、风险评估

| 风险项 | 影响等级 | 缓解措施 |
|--------|----------|----------|
| ModbusType=2 处理 | 低 | 已添加警告日志记录 |
| 旧设备兼容 | 低 | 新协议为设备→服务器单向，服务器可识别 |
| 数据溢出 | 低 | 循环条件 `readBytes+6 <= dataItemBytes` 防止 |

## 七、后续建议

1. **协议版本字段**: 建议在未来版本中增加协议版本协商机制
2. **ModbusType=2 支持**: 如设备需要支持2区，需添加 `case 2` 处理逻辑
3. **错误收集**: 考虑汇总所有解析错误并向上游报告
