# DTU+Modbus 模拟器

基于需求文档全新设计的 DTU+Modbus 模拟器，用于模拟工业物联网场景中的 4G DTU 设备和 Modbus 从站设备。

## 功能特性

- **MQTT 通信**: 支持与远程平台的双向通信
  - 心跳上报 (0x00): 每30秒自动发送
  - 模组配置 (0x02): 接收并应用配置
  - 数据配置 (0x04): 配置数据采集点
  - 数据上发 (0x05): 定时上报 Modbus 数据
  - 远程置数 (0x06): 写入 Modbus 寄存器

- **Modbus TCP 服务器**: 内置虚拟从站
  - 支持四类寄存器: 线圈(0)、离散输入(1)、输入寄存器(3)、保持寄存器(4)
  - 默认测试从站 (slave ID=1)
  - 预置温度、湿度、功率、开关等测试数据

- **数据模拟**:
  - 温度 (40001): 25.0°C, 随机波动±10
  - 湿度 (40002): 60.0%, 随机波动±20
  - 开关 (00001): 布尔值，每30秒翻转
  - 功率 (40010): 150.0W, 随机波动±50

## 项目结构

```
simulator_v3/
├── __init__.py
├── config.py                 # 配置文件
├── main.py                   # 主入口
├── requirements.txt          # 依赖
├── core/                     # 核心引擎层
│   ├── __init__.py
│   ├── mqtt_client.py       # MQTT 客户端管理器
│   ├── modbus_master.py      # Modbus 主站管理器
│   └── config_manager.py     # 配置管理器
├── protocol/                 # 协议处理层
│   ├── __init__.py
│   ├── handler.py           # 处理器基类
│   ├── heartbeat_handler.py  # 心跳处理器
│   ├── module_config_handler.py
│   ├── data_config_handler.py
│   └── remote_write_handler.py
├── data/                     # 数据层
│   ├── __init__.py
│   ├── virtual_device.py     # 虚拟从站
│   ├── device_pool.py        # 从站池
│   ├── data_scheduler.py     # 数据调度器
│   └── data_registry.py      # 数据注册表
├── modbus/                   # Modbus TCP 服务层
│   ├── __init__.py
│   ├── areas.py             # 寄存器区定义
│   ├── tcp_server.py         # TCP 服务器
│   ├── request_handler.py    # 请求处理器
│   └── response_builder.py   # 响应构建器
└── tests/                    # 测试
    ├── __init__.py
    ├── test_virtual_device.py
    ├── test_protocol.py
    ├── test_modbus.py
    └── test_integration.py
```

## 快速开始

### 1. 安装依赖

```bash
cd simulator_v3
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py` 或设置环境变量:

```python
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
DEVICE_SERIAL = "A1B2C3D4"
MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 502
```

或使用环境变量:

```bash
export MQTT_BROKER=127.0.0.1
export MQTT_PORT=1883
export DEVICE_SERIAL=A1B2C3D4
```

### 3. 运行

```bash
python -m simulator_v3.main
```

或直接运行:

```bash
python main.py
```

### 4. 运行测试

```bash
python -m pytest tests/ -v
```

## MQTT 协议

### 主题定义

| 主题 | 方向 | QoS | 说明 |
|------|------|-----|------|
| `/dtu/{serial}/up` | 上行 | 2 | 模拟器 → 平台 |
| `/dtu/{serial}/down` | 下行 | 0 | 平台 → 模拟器 |

### 功能码

| 功能码 | 方向 | 名称 | 说明 |
|-------|------|------|------|
| 0x00 | 上行 | 心跳包 | 无内容，30秒发送一次 |
| 0x01 | 下行 | 模组配置查询 | 查询 DTU 当前配置 |
| 0x01 | 上行 | 模组配置上发 | 上发 DTU 当前配置 |
| 0x02 | 下行 | 下发模组配置 | 下发 DTU 配置（发送间隔等） |
| 0x02 | 上行 | 模组配置结果 | 配置执行结果 |
| 0x03 | 下行 | 数据配置查询 | 查询 DTU 已配置的数据点 |
| 0x03 | 上行 | 数据配置上发 | 上发已配置的数据点 |
| 0x04 | 下行 | 下发数据配置 | 下发要采集的数据点配置 |
| 0x04 | 上行 | 配置结果 | 配置执行结果 |
| 0x05 | 上行 | 数据上发 | DTU 定期上传采集的数据 |
| 0x06 | 下行 | 远程置数 | 写入 Modbus 寄存器 |

### 协议格式示例

#### 04 下发数据配置（下行）

```
04 00 02                          # 功能码 0x04, 2组数据
01 03 00 00 00 02                # 从站1, 类型3, 地址0, 数量2
01 04 00 00 00 01                # 从站1, 类型4, 地址0, 数量1
```

#### 05 数据上发（上行）

```
05 00 02                          # 功能码 0x05, 2组数据
01 03 00 00 00 02 04 00FA 0258   # 从站1, 类型3, 地址0, 数量2, 数据4字节
01 04 00 00 00 01 02 03E8        # 从站1, 类型4, 地址0, 数量1, 数据2字节
```

## API 参考

### MQTTClientManager

```python
from simulator_v3.core import MQTTClientManager

mqtt = MQTTClientManager()
mqtt.connect()
mqtt.publish(topic, payload, qos=2)
mqtt.subscribe(topic, qos=2)
mqtt.set_on_message_callback(callback)
```

### ModbusTCPServer

```python
from simulator_v3.modbus import ModbusTCPServer, ModbusRequestHandler

server = ModbusTCPServer(host='127.0.0.1', port=502)
server.set_device_handler(slave_id, handler)
server.start()
server.stop()
```

### VirtualDevice

```python
from simulator_v3.data import VirtualDevice

device = VirtualDevice(slave_id=1)
device.write_single_coil(0, True)
device.write_single_register(0, 250)
data = device.read_holding_registers(0, 2)
```

### ProtocolHandler

```python
from simulator_v3.protocol import HandlerRegistry, HeartbeatHandler, DataConfigHandler

registry = HandlerRegistry()
registry.register(HeartbeatHandler())
registry.register(DataConfigHandler(config_manager))
response = registry.handle(payload)
```

## 默认测试数据

| 地址 | 变量名 | 类型 | 初始值 | 说明 |
|------|--------|------|--------|------|
| 40001 (0) | 温度 | uint16 | 250 (25.0°C) | 随机波动±10 |
| 40002 (1) | 湿度 | uint16 | 600 (60.0%) | 随机波动±20 |
| 00001 (0) | 开关状态 | bool | 1 | 每30秒翻转 |
| 40010 (9) | 功率 | uint16 | 1500 (150.0W) | 随机波动±50 |

## 依赖

- Python 3.11+
- paho-mqtt >= 1.6.1

## 许可证

MIT License