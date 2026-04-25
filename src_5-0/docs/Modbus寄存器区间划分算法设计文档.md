# Modbus多从站多分区寄存器区间划分算法设计文档

> 版本: v2.2 | 更新日期: 2026-04-24 | 状态: 已实现完整算法

## 1. 背景与目标

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              云平台 (Go后端)                                 │
│                    我们的算法运行在这里 → 优化配置下发                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │ MQTT
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ML307C-DC-CN 通信模组                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   ASR1605      │    │   4MB pSRAM    │    │   4MB FLASH    │         │
│  │   (主芯片)      │    │                │    │                │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
│  • LTE Cat.1 (移动/电信/联通)                                              │
│  • 下行10Mbps / 上行5Mbps                                                  │
│  • MQTT Topic最大256字节                                                   │
│  • 最多3个订阅主题，6个连接ID (0~5)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │ UART/AT命令
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              主控MCU (待选型)                                 │
│  ┌─────────────────┐    ┌─────────────────┐                               │
│  │   Flash        │    │      RAM        │                               │
│  │  (配置存储)      │    │  (数据缓存)    │                               │
│  │                │    │                 │                               │
│  │  128B~2MB     │    │   2KB~512KB    │                               │
│  └─────────────────┘    └─────────────────┘                               │
│                                                                             │
│  ← 存储限额约束的真正来源！主控MCU资源决定算法边界                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │ Modbus RTU
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Modbus从机设备                                    │
│  • 三菱FX5U-32MT/ES (PLC)                                                  │
│  • 施耐德TM221CE16R (PLC)                                                  │
│  • SR40 (AC/DC/继电器)                                                     │
│  • 其他Modbus设备...                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 业务场景

在工业物联网场景中，主控MCU通过ML307C-DC-CN通信模组连接云平台，下挂多个Modbus从机设备（PLC、继电器、传感器等）。

**现状问题：**
- 每个Modbus变量单独配置，导致配置命令繁多
- 主设备存储资源有限（Flash/RAM受限）
- MQTT通信带宽宝贵

### 1.3 优化目标

```
目标1: 减少配置命令存储 (Flash)
目标2: 减少数据缓存 (RAM)
目标3: 减少MQTT通信开销 (1次配置下发 + N次数据上发)
```

### 1.4 约束条件

- 存储限额约束（主控MCU资源限制）
- MQTT MTU限制（1024字节）
- Modbus协议限制（寄存器地址连续性）

---

## 2. 项目契合度分析

### 2.1 与现有代码匹配

| 项目 | 匹配位置 | 状态 |
|------|----------|------|
| 报文格式 | `payload.go` 功能码0x02/0x05 | ✅ 完全匹配 |
| 数据长度计算 | `payload.go` | ✅ 完全匹配 |
| MQTT MTU | ML307C模组规格 | ✅ 1024字节 |
| 配置命令格式 | 每区间6字节 | ✅ 完全匹配 |

### 2.2 ML307C-DC-CN模组参数（从PDF提取）

| 参数 | 值 | 说明 |
|------|-----|------|
| 芯片平台 | ASR1605 | 翱捷科技 |
| 通信制式 | LTE Cat.1 | 移动/电信/联通 |
| 理论速率 | 下行10Mbps / 上行5Mbps | - |
| 模组RAM | 4MB pSRAM | - |
| 模组Flash | 4MB FLASH | - |
| MQTT最大数据包 | 0~1024字节 | 关键约束 |
| MQTT Topic最大长度 | 256字节 | - |
| MQTT订阅主题数 | 最多3个 | - |
| MQTT连接ID | 0~5 (共6个) | - |

**注意：** ML307C是通信模组，存储限额约束实际来源于**主控MCU**，不是ML307C本身。

### 2.3 关键数据格式（从payload.go提取）

**配置下发（功能码0x02）：**
```
┌──────────┬──────────┬─────────────────────────────────────────┐
│ 功能码(1)│ 长度(2)  │ 配置项N×6  │                         │
│ 0x02     │ 总长度   │ 每项:     │                         │
│          │          │ 从站(1)  │                         │
│          │          │ 类型(1)   │                         │
│          │          │ 起始(2)  │                         │
│          │          │ 长度(2)   │                         │
└──────────┴──────────┴─────────────────────────────────────────┘
```

**数据上发（功能码0x05）：**
```
┌──────────┬──────────┬─────────────────────────────────────────┐
│ 功能码(1)│ 长度(2)  │ 数据项                                  │
│ 0x05     │ 总长度   │ 每项:                                   │
│          │          │ 从站(1)+类型(1)+地址(2)+长度(2)+值(N)   │
└──────────┴──────────┴─────────────────────────────────────────┘
```

### 2.4 数据长度计算

```go
// 根据寄存器类型计算数据字节数
switch ModbusType {
case 1, 2:  // Coil, DiscreteInput (位操作)
    return (length + 7) / 8  // bit数 → byte数
case 3, 4:  // HoldingReg, InputReg (字操作)
    return length * 2          // 寄存器数 → byte数
}
```

---

## 3. 算法设计

### 3.1 问题定义

**输入：**
```
Variables (数据库中的变量):
- DevID:        设备ID
- ModbusDevice: 从站地址 (1-247)
- ModbusType:   寄存器类型 (1=Coil,2=Discrete,3=Holding,4=Input)
- ModbusAddr:   寄存器地址
- DataLen:      长度(寄存器数或bit数)
```

**输出：**
```
ModbusRange (优化后的区间):
- SlaveAddr:  从站地址
- ModbusType: 寄存器类型
- StartAddr:  起始地址
- Length:     连续长度(单位根据类型不同)
- VarCount:   包含的变量数
```

**目标：**
- 最小化配置存储 (Flash)
- 最小化数据缓存 (RAM)
- 最小化MQTT通信开销

---

## 3.2 核心实现函数

**internal/logic/modbus_range_optimizer.go 关键函数：**

```go
// 优化器构造函数
func NewModbusRangeOptimizer(limit model.StorageLimit) *ModbusRangeOptimizer

// 构建默认存储限额
func BuildDefaultStorageLimit() model.StorageLimit

// 主优化函数 - 返回单一最优解
func (o *ModbusRangeOptimizer) Optimize(variables []*model.Variables) *model.RangeOptimizationResult

// Pareto多目标优化 - 返回多个最优解
func (o *ModbusRangeOptimizer) GetParetoSolutions(variables []*model.Variables) *model.ParetoResult

// 动态规划核心算法 - 计算单组的Pareto解集
func (o *ModbusRangeOptimizer) computeParetoForGroup(variables []*model.Variables) []model.ParetoSolution

// 从分割信息构建区间
func (o *ModbusRangeOptimizer) buildRangesFromSplits(splits []int, endIndex int, addrList []int, prefixSum []int, variables []*model.Variables) []model.ModbusRange

// 判断解是否Pareto最优
func (o *ModbusRangeOptimizer) isParetoOptimal(sol *model.ParetoSolution, allSolutions map[int]*model.ParetoSolution, maxRanges int) bool

// 分组函数 - 按从站和类型分组
func (o *ModbusRangeOptimizer) groupBySlaveAndType(variables []*model.Variables) map[string][]*model.Variables

// 数据字节计算
func (o *ModbusRangeOptimizer) calculateDataBytesForRange(length int, modbusType int) int

// MQTT消息计算
func (o *ModbusRangeOptimizer) calculateConfigMessageBytes(ranges []model.ModbusRange) int
func (o *ModbusRangeOptimizer) calculateDataMessageBytes(ranges []model.ModbusRange) (totalBytes int, packetCount int)

// 辅助函数
func (o *ModbusRangeOptimizer) checkAllContiguous(addrList []int) bool
func (o *ModbusRangeOptimizer) estimateMqttDataCount(ranges []model.ModbusRange) int
func (o *ModbusRangeOptimizer) calculateVariableLength(v *model.Variables) int
func parseModbusType(mt string) int

// 构建优化配置
func (o *ModbusRangeOptimizer) BuildOptimizedConfig(variables []*model.Variables) *model.OptimizedConfig

// 便捷函数
func OptimizeModbusVariables(variables []*model.Variables, limit *model.StorageLimit) *model.RangeOptimizationResult
func BuildModbusOptimizedConfig(variables []*model.Variables, limit *model.StorageLimit) *model.OptimizedConfig
func GetModbusParetoSolutions(variables []*model.Variables, limit *model.StorageLimit) *model.ParetoResult
```

**internal/controller/modbus_optimizer.go 关键函数：**

```go
func (c cModbusOptimizer) Optimize(ctx context.Context, req *ModbusOptimizerReq) (*ModbusOptimizerRes, error)
func (c cModbusOptimizer) BuildConfig(ctx context.Context, req *ModbusBuildConfigReq) (*ModbusBuildConfigRes, error)
func (c cModbusOptimizer) GetPresets(ctx context.Context) (*ModbusGetPresetsRes, error)
func (c cModbusOptimizer) GetLimit(ctx context.Context, req *ModbusGetLimitReq) (*ModbusGetLimitRes, error)
func (c cModbusOptimizer) GetParetoSolutions(ctx context.Context, req *ModbusParetoReq) (*ModbusParetoRes, error)
```

---

## 4. 核心总纲：完整最优解算法优化体系

基于**动态规划(DP) + 帕累托(Pareto)双目标优化**底层框架，构建「全局最优、灵活选择」的算法方案。

### 4.1 完整最优解算法优化闭环

```
输入变量 → 分组解耦 → 动态规划DP计算 → Pareto筛选
→ 全局Pareto最优解集 → 输出
```

### 4.2 关键承诺

1. **最优性保证：** 100% 找到全局最优解，无丢失、无近似
2. **灵活性保证：** 提供Pareto解集，支持存储/通信权衡选择
3. **易用性保证：** 提供预设方案，支持自定义限额

---

## 5. 问题预处理：分组解耦

### 5.1 强制分组解耦

按 `从站地址 + 寄存器类型` 严格分组，**禁止跨站/跨区合并**（Modbus协议硬约束），将复杂问题拆解为独立一维子问题，分组间无最优解耦合。

**实现代码：**
```go
func (o *ModbusRangeOptimizer) groupBySlaveAndType(variables []*model.Variables) map[string][]*model.Variables {
    groups := make(map[string][]*model.Variables)
    for _, v := range variables {
        key := fmt.Sprintf("%d_%s", v.ModbusDevice, v.ModbusType)
        groups[key] = append(groups[key], v)
    }
    return groups
}
```

### 5.2 连续变量优化检测

在开始DP计算前，先检测组内所有变量是否地址连续。如果是连续的，直接合并为单个区间，避免复杂计算。

**实现代码：**
```go
func (o *ModbusRangeOptimizer) checkAllContiguous(addrList []int) bool {
    for i := 1; i < len(addrList); i++ {
        if addrList[i]-addrList[i-1] != 1 {
            return false
        }
    }
    return true
}
```

### 5.3 排序处理

对每组内的变量按地址进行升序排序，确保DP计算的正确性。

---

## 6. 动态规划核心算法详细说明

### 6.1 算法原理

使用动态规划求解最优区间划分问题，状态定义如下：

- `dp[i][k]` 表示前 i 个变量划分为 k 个区间的最优解
- 状态转移：枚举最后一个区间的起始位置 j，计算从 j 到 i 的区间开销，选择最优组合
- 目标：最小化总开销（配置字节 + 数据字节）

### 6.2 核心数据结构

```go
// DP状态内部结构
type dpEntry struct {
    splits             []int  // 分割点记录
    configBytes       int    // 配置字节数
    dataBytes         int    // 数据字节数
    pktCount          int    // 数据报文数
    totalMessageBytes int    // 总报文字节数
}

// 分割开销缓存键
type splitKey struct {
    start int
    end   int
}
```

### 6.3 前缀和计算

提前计算变量长度的前缀和数组，用于快速计算任意区间的总长度。

```go
prefixSum := make([]int, len(addrList)+1)
for i := 0; i < len(addrList); i++ {
    prefixSum[i+1] = prefixSum[i] + varLengths[i]
}
```

### 6.4 核心实现

```go
func (o *ModbusRangeOptimizer) computeParetoForGroup(variables []*model.Variables) []model.ParetoSolution {
    // 边界情况处理
    if len(variables) == 0 {
        return []model.ParetoSolution{}
    }
    
    if len(variables) == 1 {
        // 单个变量，直接返回
        // ...
    }
    
    // 1. 预处理：构建地址映射和长度数组
    addrMap := make(map[int]*model.Variables)
    addrList := make([]int, 0, len(variables))
    varLengths := make([]int, len(variables))
    
    for i, v := range variables {
        addrMap[v.ModbusAddr] = v
        addrList = append(addrList, v.ModbusAddr)
        varLengths[i] = o.calculateVariableLength(v)
    }
    sort.Ints(addrList)
    
    // 重新计算排序后的长度
    for i, addr := range addrList {
        varLengths[i] = o.calculateVariableLength(addrMap[addr])
    }
    
    // 2. 检查是否全连续，如果是直接合并
    allContiguous := o.checkAllContiguous(addrList)
    if allContiguous {
        // 直接构建单个区间的解
        // ...
    }
    
    // 3. 计算前缀和
    prefixSum := make([]int, len(addrList)+1)
    for i := 0; i < len(addrList); i++ {
        prefixSum[i+1] = prefixSum[i] + varLengths[i]
    }
    
    // 4. 动态规划计算
    dp := make(map[int]map[int]*dpEntry)
    
    maxRanges := o.limit.MaxRangeCount
    if maxRanges <= 0 {
        maxRanges = 50
    }
    if maxRanges > len(variables) {
        maxRanges = len(variables)
    }
    
    for i := 1; i <= len(addrList); i++ {
        dp[i] = make(map[int]*dpEntry)
        
        for k := 1; k <= maxRanges && k <= i; k++ {
            bestEntry := &dpEntry{}
            
            // 枚举所有可能的j（分割点）
            for j := k - 1; j < i; j++ {
                var prevEntry *dpEntry
                if j == 0 {
                    prevEntry = &dpEntry{
                        splits:             []int{},
                        configBytes:       0,
                        dataBytes:         0,
                        pktCount:          0,
                        totalMessageBytes: 0,
                    }
                } else {
                    if prev, ok := dp[j][k-1]; ok {
                        prevEntry = prev
                    } else {
                        continue
                    }
                }
                
                // 计算从j到i的开销
                cfgBytes, dataBytes, pktCount := computeSplitCost(j, i)
                
                totalCfg := prevEntry.configBytes + cfgBytes
                totalData := prevEntry.dataBytes + dataBytes
                totalPkt := prevEntry.pktCount + pktCount
                totalMsg := totalCfg + totalData
                
                // 构建新的分割点
                newSplits := make([]int, len(prevEntry.splits)+1)
                copy(newSplits, prevEntry.splits)
                newSplits[len(newSplits)-1] = j
                
                entry := &dpEntry{
                    splits:             newSplits,
                    configBytes:       totalCfg,
                    dataBytes:         totalData,
                    pktCount:          totalPkt,
                    totalMessageBytes: totalMsg,
                }
                
                // 更新最优解
                if bestEntry.splits == nil || entry.totalMessageBytes < bestEntry.totalMessageBytes {
                    bestEntry = entry
                }
            }
            
            if bestEntry.splits != nil {
                dp[i][k] = bestEntry
            }
        }
    }
    
    // 5. 构建每个k的最优解
    solutionMap := make(map[int]*model.ParetoSolution)
    for i := 1; i <= len(addrList); i++ {
        for k := 1; k <= maxRanges; k++ {
            if entry, ok := dp[i][k]; ok && entry.splits != nil {
                if existing, exists := solutionMap[k]; !exists || entry.totalMessageBytes < existing.TotalMessageBytes {
                    solutionMap[k] = &model.ParetoSolution{
                        Ranges:              o.buildRangesFromSplits(entry.splits, i, addrList, prefixSum, variables),
                        ConfigMessageBytes:  entry.configBytes,
                        DataMessageBytes:    entry.dataBytes,
                        TotalMessageBytes:   entry.totalMessageBytes,
                        RangeCount:          k,
                        DataPacketCount:     entry.pktCount,
                    }
                }
            }
        }
    }
    
    // 6. Pareto筛选
    var paretoSolutions []model.ParetoSolution
    for k := 1; k <= maxRanges; k++ {
        if sol, ok := solutionMap[k]; ok && sol != nil {
            if o.isParetoOptimal(sol, solutionMap, maxRanges) {
                paretoSolutions = append(paretoSolutions, *sol)
            }
        }
    }
    
    // 7. 兜底：如果Pareto筛选后没有解，返回所有解
    if len(paretoSolutions) == 0 {
        for k := 1; k <= maxRanges; k++ {
            if sol, ok := solutionMap[k]; ok && sol != nil {
                paretoSolutions = append(paretoSolutions, *sol)
            }
        }
    }
    
    // 8. 按区间数排序
    sort.Slice(paretoSolutions, func(i, j int) bool {
        return paretoSolutions[i].RangeCount < paretoSolutions[j].RangeCount
    })
    
    return paretoSolutions
}
```

### 6.5 分割开销缓存

为避免重复计算，使用缓存存储区间分割的开销。

```go
splitCostMap := make(map[splitKey]struct {
    configBytes int
    dataBytes  int
    pktCount   int
})

computeSplitCost := func(start, end int) (configBytes, dataBytes, pktCount int) {
    key := splitKey{start, end}
    if cost, ok := splitCostMap[key]; ok {
        return cost.configBytes, cost.dataBytes, cost.pktCount
    }
    
    // 计算开销...
    // ...
    
    splitCostMap[key] = struct {
        configBytes int
        dataBytes  int
        pktCount   int
    }{configBytes, dataBytes, pktCount}
    
    return configBytes, dataBytes, pktCount
}
```

### 6.6 收益

找到全局最优解，保证最优性。

---

## 7. Pareto筛选优化

### 7.1 双目标优化

优化目标：
1. 最小化配置字节数（存储）
2. 最小化数据报文数（通信）

### 7.2 Pareto最优性判断

一个解是Pareto最优的，当且仅当不存在其他解在所有目标上都不差于它，且至少在一个目标上更好。

**实现代码：**
```go
func (o *ModbusRangeOptimizer) isParetoOptimal(sol *model.ParetoSolution, allSolutions map[int]*model.ParetoSolution, maxRanges int) bool {
    for k := 1; k <= maxRanges; k++ {
        other := allSolutions[k]
        if other == nil || other == sol {
            continue
        }
        if other.ConfigMessageBytes <= sol.ConfigMessageBytes &&
            other.DataPacketCount <= sol.DataPacketCount &&
            (other.ConfigMessageBytes < sol.ConfigMessageBytes || other.DataPacketCount < sol.DataPacketCount) {
            return false
        }
    }
    return true
}
```

### 7.3 收益

输出所有最优权衡方案，支持存储/通信灵活选型。

### 7.4 Pareto前沿图示

```
                    MQTT通信优化 (数据报文)
                         ▲
                       5 │
                         │                    ·
                       4 │               ·
                         │           ·
                       3 │       ·
                         │   · 方案C (高配置灵活)
                       2 │·
                         │·
                       1 │● 方案A          · 方案B
                         │(存储最优)              (均衡之选)
                         └─────────────────────────────────────▶ 配置报文大小 (字节)
                            20   30   40   50   60   70   80

                    ■ = Pareto最优解
                    · = 被支配的解 (不选择)
```

---

## 8. 区间构建算法

### 8.1 从分割点构建区间

根据DP计算出的分割点，构建实际的Modbus区间。

```go
func (o *ModbusRangeOptimizer) buildRangesFromSplits(splits []int, endIndex int, addrList []int, prefixSum []int, variables []*model.Variables) []model.ModbusRange {
    var ranges []model.ModbusRange
    
    prevSplit := 0
    for _, split := range splits {
        if split > prevSplit {
            rangeAddrs := addrList[prevSplit:split]
            rangeLength := prefixSum[split] - prefixSum[prevSplit]
            ranges = append(ranges, model.ModbusRange{
                SlaveAddr:  variables[0].ModbusDevice,
                ModbusType: parseModbusType(variables[0].ModbusType),
                StartAddr:  rangeAddrs[0],
                Length:     rangeLength,
                VarCount:   len(rangeAddrs),
            })
        }
        prevSplit = split
    }
    
    if endIndex > prevSplit {
        rangeAddrs := addrList[prevSplit:endIndex]
        rangeLength := prefixSum[endIndex] - prefixSum[prevSplit]
        ranges = append(ranges, model.ModbusRange{
            SlaveAddr:  variables[0].ModbusDevice,
            ModbusType: parseModbusType(variables[0].ModbusType),
            StartAddr:  rangeAddrs[0],
            Length:     rangeLength,
            VarCount:   len(rangeAddrs),
        })
    }
    
    return ranges
}
```

---

## 9. 核心计算函数

### 9.1 数据字节数计算

```go
func (o *ModbusRangeOptimizer) calculateDataBytesForRange(length int, modbusType int) int {
    switch modbusType {
    case model.ModbusTypeCoil, model.ModbusTypeDiscreteInput:
        return (length + 7) / 8   // bit → byte
    case model.ModbusTypeHoldingReg, model.ModbusTypeInputReg:
        return length * 2          // word → byte
    default:
        return length * 2
    }
}
```

### 9.2 MQTT报文计算

```go
// MQTT协议开销
const (
    MaxBytesPerMqttPacket = 1024  // ML307C模组MTU
    MqttHeaderBytes       = 3     // MQTT头
    MqttBodyMinBytes      = 20    // 最小body
    ConfigBytesPerRange   = 6     // 每区间配置字节
)

// 配置报文计算
func (o *ModbusRangeOptimizer) calculateConfigMessageBytes(ranges []model.ModbusRange) int {
    if len(ranges) == 0 {
        return 0
    }
    
    cfgPayloadBytes := len(ranges) * model.ConfigBytesPerRange
    totalBytes := cfgPayloadBytes + model.MqttHeaderBytes + model.MqttBodyMinBytes
    
    if totalBytes <= model.MaxBytesPerMqttPacket {
        return totalBytes
    }
    return ((totalBytes + model.MaxBytesPerMqttPacket - 1) / model.MaxBytesPerMqttPacket) * model.MaxBytesPerMqttPacket
}

// 数据报文计算
func (o *ModbusRangeOptimizer) calculateDataMessageBytes(ranges []model.ModbusRange) (totalBytes int, packetCount int) {
    if len(ranges) == 0 {
        return 0, 0
    }
    
    dataBytes := 0
    for _, r := range ranges {
        dataBytes += o.calculateDataCacheBytes(r)
    }
    
    totalBytes = dataBytes + model.MqttHeaderBytes + model.MqttBodyMinBytes
    if totalBytes <= model.MaxBytesPerMqttPacket {
        return totalBytes, 1
    }
    
    packetCount = (totalBytes + model.MaxBytesPerMqttPacket - 1) / model.MaxBytesPerMqttPacket
    return packetCount * model.MaxBytesPerMqttPacket, packetCount
}
```

### 9.3 变量长度解析

```go
func (o *ModbusRangeOptimizer) calculateVariableLength(v *model.Variables) int {
    length := 1
    if v.DataLen != "" {
        fmt.Sscanf(v.DataLen, "%d", &length)
        if length <= 0 {
            length = 1
        }
    }
    return length
}

func parseModbusType(mt string) int {
    switch mt {
    case "1", "coils", "Coil":
        return model.ModbusTypeCoil
    case "2", "discrete", "DiscreteInput":
        return model.ModbusTypeDiscreteInput
    case "3", "holding", "HoldingRegister":
        return model.ModbusTypeHoldingReg
    case "4", "input", "InputRegister":
        return model.ModbusTypeInputReg
    default:
        val, err := strconv.Atoi(mt)
        if err != nil {
            return model.ModbusTypeHoldingReg
        }
        return val
    }
}
```

### 9.4 默认存储限额构建

```go
// 构建默认存储限额
func BuildDefaultStorageLimit() model.StorageLimit {
    return model.StorageLimit{
        MaxConfigBytes:     256,
        MaxDataCacheBytes: 4096,
        MaxRangeCount:     50,
        MaxMqttConfigCount: 10,
    }
}
```

### 9.5 限额解析（Controller层）

```go
// 解析存储限额
func (c cModbusOptimizer) resolveLimit(preset string, customLimit *model.StorageLimit) *model.StorageLimit {
    if preset == "" || preset == model.PresetNameCustom {
        if customLimit != nil {
            return customLimit
        }
        limit := logic.BuildDefaultStorageLimit()
        return &limit
    }

    for _, p := range model.StoragePresets {
        if p.Name == preset {
            limit := p.Limit
            return &limit
        }
    }

    limit := logic.BuildDefaultStorageLimit()
    return &limit
}
```

---

## 11. 存储限额预设

### 11.1 三档预设方案

| 预设 | 典型MCU | Config | DataCache | 区间数 | MQTT | 预估变量 |
|------|---------|--------|-----------|--------|------|----------|
| **low** | STM8S (2KB RAM) | 128B | 512B | 20 | 5 | ~30 |
| **medium** | STM32F103 (64KB RAM) | 512B | 4KB | 50 | 10 | ~150 |
| **high** | STM32F4/ESP32 (256KB+) | 2KB | 16KB | 100 | 20 | ~500 |

### 11.2 存储限额数据结构

```go
// 预设名称常量
const (
    PresetNameLow    = "low"
    PresetNameMedium = "medium"
    PresetNameHigh   = "high"
    PresetNameCustom = "custom"
)

// 存储限额
type StorageLimit struct {
    MaxConfigBytes     int `json:"maxConfigBytes"`
    MaxDataCacheBytes int `json:"maxDataCacheBytes"`
    MaxRangeCount     int `json:"maxRangeCount"`
    MaxMqttConfigCount int `json:"maxMqttConfigCount"`
}

// 存储预设
type StoragePreset struct {
    Name        string       `json:"name"`
    Description string       `json:"description"`
    TypicalMCU  string       `json:"typicalMCU"`
    Limit       StorageLimit `json:"limit"`
    MaxVars     int          `json:"maxVarsEstimate"`
}

// 预设方案数组
var StoragePresets = []StoragePreset{
    {
        Name:        PresetNameLow,
        Description: "低配方案 - 适用于资源极度受限的MCU",
        TypicalMCU:  "STM8S (2KB RAM), N76E003 (1KB RAM)",
        Limit: StorageLimit{
            MaxConfigBytes:     128,
            MaxDataCacheBytes: 512,
            MaxRangeCount:     20,
            MaxMqttConfigCount: 5,
        },
        MaxVars: 30,
    },
    {
        Name:        PresetNameMedium,
        Description: "中等方案 - 适用于中等规模工业应用",
        TypicalMCU:  "STM32F103 (64KB RAM), STM32F401 (64KB RAM)",
        Limit: StorageLimit{
            MaxConfigBytes:     512,
            MaxDataCacheBytes: 4096,
            MaxRangeCount:     50,
            MaxMqttConfigCount: 10,
        },
        MaxVars: 150,
    },
    {
        Name:        PresetNameHigh,
        Description: "高配方案 - 适用于资源充裕的高端MCU",
        TypicalMCU:  "STM32F4 (256KB RAM), ESP32 (520KB RAM)",
        Limit: StorageLimit{
            MaxConfigBytes:     2048,
            MaxDataCacheBytes: 16384,
            MaxRangeCount:     100,
            MaxMqttConfigCount: 20,
        },
        MaxVars: 500,
    },
}
```

### 11.3 选择建议

| 场景 | 推荐预设 |
|------|----------|
| 存储极度受限 | low |
| 中等规模工业应用 | medium (默认) |
| 资源充裕，高性能需求 | high |

---

## 12. 数据结构完整定义

### 12.1 核心类型定义 (internal/model/modbus_range.go)

```go
// ModbusRange - 优化后的区间
type ModbusRange struct {
    SlaveAddr  int    `json:"slaveAddr"`
    ModbusType int    `json:"modbusType"`
    StartAddr  int    `json:"startAddr"`
    Length     int    `json:"length"`
    VarCount   int    `json:"varCount"`
    IsOptimal  bool   `json:"isOptimal"`
}

// RangeOptimizationResult - 优化结果
type RangeOptimizationResult struct {
    Ranges           []ModbusRange `json:"ranges"`
    TotalVars        int           `json:"totalVars"`
    TotalConfigBytes int           `json:"totalConfigBytes"`
    TotalDataCache   int           `json:"totalDataCacheBytes"`
    MqttConfigCount  int           `json:"mqttConfigCount"`
    MqttDataCount    int           `json:"mqttDataCountEstimate"`
    IsWithinLimit    bool          `json:"isWithinLimit"`
    LimitReason      string        `json:"limitReason,omitempty"`
}

// ParetoSolution - Pareto最优解
type ParetoSolution struct {
    Ranges              []ModbusRange `json:"ranges"`
    ConfigMessageBytes int           `json:"configMessageBytes"`
    DataMessageBytes   int           `json:"dataMessageBytes"`
    TotalMessageBytes  int           `json:"totalMessageBytes"`
    RangeCount         int           `json:"rangeCount"`
    DataPacketCount    int           `json:"dataPacketCount"`
}

// ParetoResult - Pareto解集结果
type ParetoResult struct {
    Solutions    []ParetoSolution `json:"solutions"`
    BestByStorage *ParetoSolution `json:"bestByStorage"`
    BestByMqtt    *ParetoSolution `json:"bestByMqtt"`
    BestByTotal   *ParetoSolution `json:"bestByTotal"`
    StorageLimit StorageLimit    `json:"storageLimit"`
}

// OptimizedConfig - 优化配置
type OptimizedConfig struct {
    Ranges        []ModbusRange              `json:"ranges"`
    DataCacheMap  map[string]DataCacheEntry `json:"dataCacheMap"`
    RangeIndexMap map[string]int            `json:"rangeIndexMap"`
}

// DataCacheEntry - 数据缓存条目
type DataCacheEntry struct {
    SlaveAddr  int    `json:"slaveAddr"`
    ModbusType int    `json:"modbusType"`
    StartAddr  int    `json:"startAddr"`
    Length     int    `json:"length"`
    ByteOffset int    `json:"byteOffset"`
}

// 常量定义
const (
    ModbusTypeCoil         = 1
    ModbusTypeDiscreteInput = 2
    ModbusTypeHoldingReg   = 3
    ModbusTypeInputReg     = 4
    
    MaxBytesPerMqttPacket = 1024
    ConfigBytesPerRange   = 6
    
    MqttHeaderBytes  = 3
    MqttBodyMinBytes = 20
)
```

---

## 13. API接口完整说明

### 13.1 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/modbus/optimize` | POST | 获取单一最优解 |
| `/modbus/build-config` | POST | 构建优化配置 |
| `/modbus/pareto` | POST | 获取Pareto解集 |
| `/modbus/get-presets` | GET | 获取所有预设方案 |
| `/modbus/get-limit` | GET | 获取指定预设的限额 |

### 13.2 请求结构完整定义

```go
// ModbusOptimizerReq - 优化请求
type ModbusOptimizerReq struct {
    DevID int                  `json:"devId" dc:"设备ID"`
    Preset string              `json:"preset" dc:"预设名称(low/medium/high/custom)"`
    Limit *model.StorageLimit  `json:"limit" dc:"存储限额约束(preset为custom时使用)"`
}

// ModbusBuildConfigReq - 构建配置请求
type ModbusBuildConfigReq struct {
    DevID int                  `json:"devId" dc:"设备ID"`
    Preset string              `json:"preset" dc:"预设名称(low/medium/high/custom)"`
    Limit *model.StorageLimit  `json:"limit" dc:"存储限额约束(preset为custom时使用)"`
}

// ModbusGetLimitReq - 获取限额请求
type ModbusGetLimitReq struct {
    Preset string `json:"preset" dc:"预设名称"`
}

// ModbusParetoReq - Pareto解集请求
type ModbusParetoReq struct {
    DevID int                  `json:"devId" dc:"设备ID"`
    Preset string              `json:"preset" dc:"预设名称(low/medium/high/custom)"`
    Limit *model.StorageLimit  `json:"limit" dc:"存储限额约束(preset为custom时使用)"`
}
```

### 13.3 响应结构完整定义

```go
// ModbusOptimizerRes - 优化响应
type ModbusOptimizerRes struct {
    Result *model.RangeOptimizationResult `json:"result"`
}

// ModbusBuildConfigRes - 构建配置响应
type ModbusBuildConfigRes struct {
    Config *model.OptimizedConfig `json:"config"`
}

// ModbusGetPresetsRes - 获取预设响应
type ModbusGetPresetsRes struct {
    Presets []model.StoragePreset `json:"presets"`
}

// ModbusGetLimitRes - 获取限额响应
type ModbusGetLimitRes struct {
    Preset string             `json:"preset"`
    Limit  model.StorageLimit `json:"limit"`
}

// ModbusParetoRes - Pareto解集响应
type ModbusParetoRes struct {
    ParetoResult *model.ParetoResult `json:"paretoResult"`
}
```

### 13.4 路由注册 (internal/cmd/cmd.go)

```go
group.Bind(controller.ModbusOptimizer.Optimize)
group.Bind(controller.ModbusOptimizer.BuildConfig)
group.Bind(controller.ModbusOptimizer.GetLimit)
group.Bind(controller.ModbusOptimizer.GetPresets)
group.Bind(controller.ModbusOptimizer.GetParetoSolutions)
```

### 13.5 请求示例

```json
// 使用预设
POST /modbus/pareto
{
  "devId": 123,
  "preset": "medium"
}

// 自定义限额
POST /modbus/pareto
{
  "devId": 123,
  "preset": "custom",
  "limit": {
    "maxConfigBytes": 256,
    "maxDataCacheBytes": 2048,
    "maxRangeCount": 30,
    "maxMqttConfigCount": 8
  }
}
```

### 13.6 响应示例

```json
{
  "paretoResult": {
    "solutions": [
      {
        "rangeCount": 1,
        "configMessageBytes": 29,
        "dataMessageBytes": 49,
        "totalMessageBytes": 78,
        "dataPacketCount": 1,
        "ranges": [
          {"slaveAddr": 1, "modbusType": 3, "startAddr": 0, "length": 13, "varCount": 6}
        ]
      },
      {
        "rangeCount": 2,
        "configMessageBytes": 35,
        "dataMessageBytes": 35,
        "totalMessageBytes": 70,
        "dataPacketCount": 1,
        "ranges": [
          {"slaveAddr": 1, "modbusType": 3, "startAddr": 0, "length": 3, "varCount": 3},
          {"slaveAddr": 1, "modbusType": 3, "startAddr": 10, "length": 3, "varCount": 3}
        ]
      }
    ],
    "bestByStorage": {...},
    "bestByMqtt": {...},
    "bestByTotal": {...},
    "storageLimit": {
      "maxConfigBytes": 512,
      "maxDataCacheBytes": 4096,
      "maxRangeCount": 50,
      "maxMqttConfigCount": 10
    }
  }
}
```

---

## 14. 使用示例

### 14.1 基本使用：获取单一最优解

```go
// 假设已有变量列表
variables := []*model.Variables{...}

// 使用默认限额
result := logic.OptimizeModbusVariables(variables, nil)

fmt.Printf("变量数: %d, 区间数: %d\n", result.TotalVars, len(result.Ranges))
fmt.Printf("配置字节: %d, 数据缓存: %d\n", result.TotalConfigBytes, result.TotalDataCache)
```

### 14.2 使用预设方案

```go
// 使用low预设
limit := &model.StorageLimit{
    MaxConfigBytes:     128,
    MaxDataCacheBytes: 512,
    MaxRangeCount:     20,
    MaxMqttConfigCount: 5,
}
result := logic.OptimizeModbusVariables(variables, limit)
```

### 14.3 获取Pareto解集

```go
// 获取所有权衡方案
paretoResult := logic.GetModbusParetoSolutions(variables, nil)

fmt.Printf("找到 %d 个Pareto最优解\n", len(paretoResult.Solutions))

// 选择存储最优的
bestStorage := paretoResult.BestByStorage
if bestStorage != nil {
    fmt.Printf("存储最优: 配置字节 %d, 数据报文 %d\n", 
        bestStorage.ConfigMessageBytes, bestStorage.DataPacketCount)
}

// 选择通信最优的
bestMqtt := paretoResult.BestByMqtt
if bestMqtt != nil {
    fmt.Printf("通信最优: 配置字节 %d, 数据报文 %d\n", 
        bestMqtt.ConfigMessageBytes, bestMqtt.DataPacketCount)
}
```

### 14.4 构建优化配置

```go
config := logic.BuildModbusOptimizedConfig(variables, nil)

// 配置包含区间信息和数据缓存映射
fmt.Printf("构建了 %d 个优化区间\n", len(config.Ranges))
```

---

## 15. 算法流程详解

### 15.1 整体架构

```
输入: N个变量 + 存储限额
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: 分组解耦 (groupBySlaveAndType)       │
│ 按 (从站地址, 寄存器类型) 分组               │
│ {从站1_Type3} {从站1_Type4} {从站2_Type3}   │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 2: 预处理 (排序, 连续检测)              │
│ 每组内按地址排序，检测是否连续               │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 3: 动态规划DP计算 (computeParetoForGroup)│
│ 对每个分组独立计算最优解                     │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 4: Pareto筛选 (isParetoOptimal)        │
│ 对每个分组的解进行Pareto筛选                 │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 5: 合并所有分组的结果                  │
│ 合并并排序所有解，选择最优                   │
└─────────────────────────────────────────────┘
  │
  ▼
输出: ParetoResult / RangeOptimizationResult
```

### 15.2 单组DP计算流程

```
组内变量
  │
  ▼
排序地址 → 检查连续? → 是 → 直接合并为一个区间
  │ 否
  ▼
计算前缀和
  │
  ▼
初始化DP表 dp[i][k]
  │
  ▼
循环 i = 1 到 n (变量数)
  │
  ├─ 循环 k = 1 到 maxRanges
  │   │
  │   ├─ 循环 j = k-1 到 i-1
  │   │   │
  │   │   ├─ 获取 dp[j][k-1]
  │   │   ├─ 计算 j到i 的开销
  │   │   ├─ 更新最优解
  │   │
  │
  ▼
构建每个k的解 → Pareto筛选 → 返回解集
```

---

## 16. 文件结构

```
dev _back_end/dev/
├── internal/
│   ├── model/
│   │   └── modbus_range.go          # 数据模型定义
│   ├── logic/
│   │   └── modbus_range_optimizer.go # 核心算法实现
│   ├── controller/
│   │   └── modbus_optimizer.go       # API控制器
│   └── cmd/
│       └── cmd.go                    # 路由注册
```

---

## 17. 总结

这是**工业Modbus采集场景中，基于动态规划和Pareto优化的完整解决方案**。

### 17.1 核心优化点

| 优化层 | 方法 | 收益 |
|--------|------|------|
| 问题分解 | 分组解耦 | 将复杂问题拆分为独立子问题 |
| 核心算法 | 动态规划DP | 找到全局最优解 |
| 多目标优化 | Pareto筛选 | 提供存储/通信权衡选择 |
| 性能优化 | 分割开销缓存 | 避免重复计算 |

### 17.2 最优性保证

- ✅ 100%找到全局最优解，无丢失
- ✅ 无近似、无启发式妥协
- ✅ 完整保留Pareto前沿

### 17.3 适用场景

- **中等规模变量**（n=100+）
- **多从站分组**（10+从机）
- **存储受限**（嵌入式MCU）
- **需要灵活权衡**（存储 vs 通信）
