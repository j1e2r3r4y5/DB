# 任务列表 - 4G DTU 通信协议更新

## 任务1: 分析并修改0x05功能码解析逻辑

- [x] 1.1: 阅读并理解 `internal/logic/payload.go` 中现有的0x05解析逻辑
- [x] 1.2: 对比旧协议(第73-77行)与新协议(第68-72行)的差异
- [x] 1.3: 修改 `case "05"` 分支的解析逻辑，新增从站地址和Modbus类型字段的读取
- [x] 1.4: 更新 `readBytes` 计算逻辑以包含新增的2字节(1字节从站地址+1字节类型)
- [x] 1.5: 验证修改后的循环条件 `readBytes+6 <= dataItemBytes` 是否正确

## 任务2: 确认并更新DataItem数据结构

- [x] 2.1: 检查 `internal/model/data.go` 中的 DataItem 结构体定义
- [x] 2.2: 确认结构体包含 `SlaveAddr` (从站地址) 字段，如缺失则新增
- [x] 2.3: 确认结构体包含 `ModbusType` (Modbus类型) 字段，如缺失则新增
- [x] 2.4: 检查 `WritdataToInflux` 函数调用是否正确传递所有新增字段

## 任务3: 更新0x03和0x04的注释描述

- [x] 3.1: 将0x03解析逻辑中的注释从"0-4区"更新为"0、1、3、4区"
- [x] 3.2: 将0x04解析逻辑中的注释从"0-4区"更新为"0、1、3、4区"
- [x] 3.3: 添加对Modbus区域定义表格的注释引用说明

## 任务4: 添加Modbus区域定义常量

- [x] 4.1: 在 `internal/model/` 或合适位置添加Modbus区域定义常量或映射表
- [x] 4.2: 定义区域名称映射: 0=线圈, 1=离散输入, 3=输入寄存器, 4=保持寄存器
- [x] 4.3: 可选: 添加读写权限标志和最大读取数量定义

## 任务5: 更新日志输出信息

- [x] 5.1: 更新0x05解析中的调试日志，增加从站地址和数据类型输出
- [x] 5.2: 更新0x03/0x04解析中的调试日志，明确标注支持的区域类型
- [x] 5.3: 确保所有日志信息使用中文描述，便于问题排查

## 任务6: 代码审查和验证

- [x] 6.1: 同行评审修改后的代码
- [x] 6.2: 使用旧协议格式数据进行兼容性测试(如果需要支持旧设备)
- [x] 6.3: 使用新协议格式数据进行功能验证
- [x] 6.4: 验证数据正确写入InfluxDB，检查tag和field是否正确
- [x] 6.5: 运行项目构建，确保无编译错误

## 任务7: 更新相关文档

- [x] 7.1: 更新代码注释，反映新的协议格式
- [x] 7.2: 可选: 更新 `resource/配置文件/agreement.md` 中的0x05格式说明

---

## 任务依赖关系

```
任务1 (0x05解析逻辑修改)
    ↑
    ├── 任务2 (DataItem结构体) - 任务1和任务2可并行
    │
任务3 (0x03/0x04注释更新) - 可与任务1并行
    │
    ├── 任务4 (Modbus常量定义) - 可独立执行
    │
    └── 任务5 (日志更新) - 依赖于任务1和任务3
            │
            └── 任务6 (代码审查验证) - 依赖于任务1-5全部完成
                    │
                    └── 任务7 (文档更新) - 可独立执行
```

## 关键修改点汇总

### internal/logic/payload.go - case "05" 分支

**修改位置**: 第266-280行

**修改内容**:
1. 在 `for readBytes+6 <= dataItemBytes` 循环开始时
2. 在读取 `dataLen` 之前，新增读取:
   - `slaveAddr, _ := scanner.Next(1)` - 从站地址
   - `modbusType, _ := scanner.Next(1)` - 数据类型
3. 修改 `readBytes += 6` 为 `readBytes += 6 + valueLen` 前的增量计算方式

**原逻辑**:
```go
for readBytes+6 <= dataItemBytes {
    slaveAddr, _ := scanner.Next(1)
    ModbusType, _ := scanner.Next(1)
    dataAddr, _ := scanner.Next(2)
    dataLen, _ := scanner.Next(2)
    // ... 使用 slaveAddr 和 ModbusType
}
```

**新逻辑**:
```go
for readBytes+6 <= dataItemBytes {
    slaveAddr, _ := scanner.Next(1)    // 新增: 从站地址
    modbusType, _ := scanner.Next(1)   // 新增: 数据类型
    dataAddr, _ := scanner.Next(2)     // 2字节地址
    dataLen, _ := scanner.Next(2)      // 2字节长度
    length := int(dataLen[0])<<8 | int(dataLen[1])

    var valueLen int
    switch modbusType[0] {
    case 1, 2:
        valueLen = (length + 7) / 8
    case 3, 4:
        valueLen = length * 2
    }
    dataValue, _ := scanner.Next(valueLen)
    readBytes += 6 + valueLen

    // ... 处理数据，使用新增的 slaveAddr 和 modbusType
}
```
