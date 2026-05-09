# 地址段配置使用说明

## 功能概述

现在模拟器支持通过地址段配置来自动生成变量和数据采集配置。

## 配置格式：**段序号 所属分区 起始地址 地址长度 [名称] [数据类型] [单位] [初始值] [最小值] [最大值] [模拟类型]**

## 快速开始

### 1. 使用默认配置运行

```bash
python main.py
```

### 2. 使用自定义配置文件运行

```bash
python main.py --config address_segments.txt
```

### 3. 使用旧版配置（不使用地址段）

```bash
python main.py --no-segments
```

## 配置文件格式

### 基本格式

```
段序号  分区  起始地址  长度  [名称]  [数据类型]  [单位]  [初始值]  [最小值]  [最大值]  [模拟类型]
```

### 字段说明：
- **段序号**: 连续编号的段号
- **所属分区**: Modbus 分区 (0=线圈, 1=离散输入, 3=输入寄存器, 4=保持寄存器)
- **起始地址**: 起始寄存器/线圈地址
- **长度**: 地址长度
- **名称** (可选): 变量名
- **数据类型** (可选): 数据类型
- **单位** (可选): 单位
- **初始值** (可选): 初始值
- **最小值** (可选): 最小值 (用 - 表示无)
- **最大值** (可选): 最大值 (用 - 表示无)
- **模拟类型** (可选): random/increment/constant

### 示例配置

```
# 示例配置
1  0  100  8   switch1  bool  ""  1  0  1  random
2  0  200  16  switch2  bool  ""  0  0  1  random
3  1  0    1   status   bool  ""  1  0  1  constant
4  3  0    2   temp     float32  °C  25.5  20  30  random
5  3  2    1   humidity  int16  %RH  60  40  80  random
6  4  0    2   temp_out float32  °C  25.5  20  30  random
7  4  2    1   humidity_out int16 %RH 60 40 80 random
8  4  3    4   power    float64  W  1500.75  1400  1600  random
9  4  7    2   energy   int32  Wh  12345678  0  -  increment
10 4  10   10  device_desc  string  ""  ML307-Test  -  -  constant
```

## 数据类型

支持的数据类型：

| 类型 | 说明 |
|------|------|
| bool | 布尔值 |
| int16 | 16位整数 |
| uint16 | 16位无符号整数 |
| int32 | 32位整数 |
| uint32 | 32位无符号整数 |
| float32 | 32位浮点数 |
| float64 | 64位浮点数 |
| string | 字符串 |

## 模拟类型

| 类型 | 说明 |
|------|------|
| random | 随机变化（在 min 和 max 之间） |
| increment | 持续递增 |
| constant | 保持不变 |

## 排序规则

地址段会按照以下规则自动排序：
1. 先按分区顺序：**0 → 1 → 3 → 4
2. 同一分区内按起始地址升序排序

## 编程接口

### 直接使用地址段管理器：

```python
from data.address_segment import AddressSegmentManager, create_default_segments

# 创建管理器
manager = AddressSegmentManager()

# 从列表添加
segments = [
    [1, 4, 0, 2, "temperature", "float32", "°C", 25.5, 20, 30, "random"],
    [2, 4, 2, 1, "humidity", "int16", "%RH", 60, 40, 80, "random"],
]
manager.add_segments_from_list(segments)

# 排序
manager.sort_segments()

# 生成变量
variables = manager.generate_variables()

# 加载到虚拟设备
device.load_address_segments(manager)
```

### 从文件加载配置：

```python
manager = AddressSegmentManager()
manager.load_from_file("my_config.txt")
```

## 文件结构

新增的文件：
- `data/address_segment.py` - 地址段管理核心模块
- `address_segments.txt` - 示例配置文件
- `test_address_segments.py` - 测试脚本
- `ADDRESS_SEGMENTS_GUIDE.md` - 本文档

修改的文件：
- `data/virtual_device.py` - 支持地址段加载和模拟
- `data/__init__.py` - 导出新模块
- `main.py` - 集成地址段配置
