# DTU+Modbus 模拟器 全新设计与实现方案

> 本文档基于核心需求，从零开始设计全新的 DTU+Modbus 模拟器系统。

***

## 一、需求分析

### 1.1 核心目标

用纯软件模拟一整套工业物联网现场的硬件系统：
- **远程平台** ←→ **4G DTU 传输设备** ←→ **Modbus 接口的传感器/从站设备**
- 全程不需要真实硬件，所有通信、数据在本地软件中模拟完成

### 1.2 系统角色

| 角色 | 说明 |
|------|------|
| 远程平台 | 您的物联网平台（后端+前端+MQTT Broker+InfluxDB） |
| 4G DTU | 数据传输单元，接收平台指令，采集 Modbus 设备数据上报 |
| Modbus 从站 | 虚拟传感器设备，提供温度、湿度、功率、开关等数据 |

### 1.3 功能需求

#### 1.3.1 MQTT 通信

| 功能 | 说明 |
|------|------|
| 心跳上报 | 每30秒发送一次心跳包 (0x00) |
| 模组配置 | 接收并处理平台下发的模组配置 (0x02) |
| 数据配置 | 接收并处理平台下发的数据采集配置 (0x04) |
| 数据上发 | 根据配置定时轮询 Modbus 并上报数据 (0x05) |
| 远程置数 | 接收平台指令写入 Modbus 寄存器 (0x06) |

#### 1.3.2 Modbus 通信

| 功能 | 说明 |
|------|------|
| TCP 服务 | 在 127.0.0.1:502 提供 Modbus TCP 服务 |
| 多从站支持 | 支持挂载多个独立从站（slave ID 1-247） |
| 四类寄存器 | 支持线圈(0)、离散输入(1)、输入寄存器(3)、保持寄存器(4) |
| 默认测试从站 | 默认提供测试用从站(slave ID=1) |

#### 1.3.3 默认测试数据

| 地址 | 变量名 | 类型 | 初始值 | 变化规则 |
|------|--------|------|--------|----------|
| 40001 (0) | 温度 | uint16 | 250 (25.0℃) | 随机波动±10，存储值÷10 |
| 40002 (1) | 湿度 | uint16 | 600 (60.0%) | 随机波动±20，存储值÷10 |
| 00001 (0) | 开关状态 | bool | 1 | 每30秒翻转 0↔1 |
| 40010 (9) | 功率 | uint16 | 15000 (1500.0W) | 随机波动±500，存储值÷10 |

### 1.4 非功能需求

| 需求 | 说明 |
|------|------|
| 稳定性 | MQTT 连接自动重连，Modbus 连接池复用 |
| 可调试性 | 完整日志输出，支持 DEBUG/INFO/WARNING/ERROR 级别 |
| 可扩展性 | 模块化设计，支持添加新从站和新功能 |
| 可测试性 | 提供测试脚本验证全链路 |

***

## 二、系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DTU+Modbus 模拟器系统                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          核心引擎层                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ MQTT Client  │  │ Modbus Master│  │   Config     │              │   │
│  │  │   Manager    │  │   Manager    │  │   Manager    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│  ┌───────────────────────────────────┼───────────────────────────────────┐  │
│  │                                   ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                      Protocol Handler Layer                      │ │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │ │  │
│  │  │  │Heartbeat │ │ModuleCfg │ │DataCfg   │ │RemoteWr  │          │ │  │
│  │  │  │ Handler  │ │ Handler  │ │ Handler  │ │ Handler  │          │ │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│  ┌───────────────────────────────────┼───────────────────────────────────┐  │
│  │                                   ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                       Data Layer                                 │ │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │ │  │
│  │  │  │Virtual Device│  │ Data Scheduler│  │ Data Registry│          │ │  │
│  │  │  │   Pool      │  │              │  │              │          │ │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘          │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│  ┌───────────────────────────────────┼───────────────────────────────────┐  │
│  │                                   ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                    Modbus TCP Server Layer                       │ │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │ │  │
│  │  │  │ TCP Listener │  │ Request      │  │ Response     │          │ │  │
│  │  │  │              │  │ Dispatcher   │  │ Builder      │          │ │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘          │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 关键接口 |
|------|------|----------|
| MQTT Client Manager | 管理 MQTT 连接、订阅、收发消息 | `connect()`, `disconnect()`, `publish()`, `subscribe()` |
| Modbus Master Manager | 管理 Modbus 连接池、读写请求 | `read()`, `write()`, `get_connection()` |
| Config Manager | 管理模组配置和数据配置 | `get_module_config()`, `update_data_config()` |
| Protocol Handler Layer | 协议解析和分发 | `_handle_downlink()`, `Handler` 接口 |
| Virtual Device Pool | 管理虚拟从站设备 | `get_device(slave_id)`, `add_device()`, `remove_device()` |
| Data Scheduler | 定时调度数据采集 | `start()`, `stop()`, `add_job()`, `remove_job()` |
| Modbus TCP Server | 提供 Modbus TCP 服务 | `start()`, `stop()`, `handle_request()` |

### 2.3 数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流                                          │
└─────────────────────────────────────────────────────────────────────────────┘

下行数据流 (平台 → DTU → Modbus):
──────────────────────────────────────────────────────────────────────────────
Platform ──MQTT──▶ MQTTClient ──▶ ProtocolHandler ──▶ ModbusMaster
                                                            │
                                                            ▼
                                                    ModbusTCPSlave

上行数据流 (Modbus → DTU → 平台):
──────────────────────────────────────────────────────────────────────────────
ModbusTCPSlave ◀──Modbus──┤
                           │
                    DataScheduler (定时触发)
                           │
                           ▼
ModbusMaster ──read()──▶ ModbusTCPSlave
                           │
                           ▼
                    ProtocolHandler ──MQTT──▶ Platform

配置更新流:
──────────────────────────────────────────────────────────────────────────────
Platform ──MQTT──▶ MQTTClient ──▶ ProtocolHandler
                                              │
                                              ▼
                                       ConfigManager
                                              │
                                              ▼
                                        DataScheduler
```

***

## 三、技术方案

### 3.1 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 编程语言 | Python 3.11+ | 简洁高效，适合快速开发 |
| MQTT 客户端 | paho-mqtt 1.6.1+ | 标准 MQTT 客户端库 |
| 日志框架 | Python logging | 标准库，完整日志支持 |
| 网络编程 | asyncio + socket | 异步 I/O，高并发支持 |
| 并发模型 | threading + asyncio | 定时任务用 threading，网络用 asyncio |
| 配置管理 | dataclasses + dict | 轻量级配置管理 |

### 3.2 项目结构

```
simulator/
├── __init__.py                    # 包初始化
├── config.py                      # 配置文件
├── main.py                        # 主入口
├── requirements.txt                # 依赖
│
├── core/                          # 核心引擎层
│   ├── __init__.py
│   ├── mqtt_client.py            # MQTT 客户端管理器
│   ├── modbus_master.py           # Modbus 主站管理器
│   └── config_manager.py          # 配置管理器
│
├── protocol/                      # 协议处理层
│   ├── __init__.py
│   ├── handler.py                 # 处理器基类
│   ├── heartbeat_handler.py       # 心跳处理器
│   ├── module_config_handler.py   # 模组配置处理器
│   ├── data_config_handler.py     # 数据配置处理器
│   └── remote_write_handler.py    # 远程置数处理器
│
├── data/                          # 数据层
│   ├── __init__.py
│   ├── virtual_device.py          # 虚拟从站
│   ├── device_pool.py             # 从站池
│   ├── data_scheduler.py          # 数据调度器
│   └── data_registry.py            # 数据注册表
│
├── modbus/                        # Modbus TCP 服务层
│   ├── __init__.py
│   ├── tcp_server.py              # TCP 服务器
│   ├── request_dispatcher.py      # 请求分发器
│   ├── response_builder.py        # 响应构建器
│   └── areas.py                   # 寄存器区定义
│
└── tests/                         # 测试
    ├── __init__.py
    ├── test_mqtt.py               # MQTT 测试
    ├── test_modbus.py             # Modbus 测试
    ├── test_protocol.py           # 协议测试
    └── test_integration.py        # 集成测试
```

### 3.3 核心类设计

#### 3.3.1 MQTTClientManager

```python
class MQTTClientManager:
    """MQTT 客户端管理器"""

    def __init__(
        self,
        broker: str,
        port: int,
        client_id: str,
        up_topic: str,
        down_topic: str,
        qos: int = 2
    ):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.up_topic = up_topic
        self.down_topic = down_topic
        self.qos = qos

        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._on_message_callback: Optional[Callable] = None
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60

    def connect(self) -> bool:
        """连接到 MQTT Broker"""
        pass

    def disconnect(self):
        """断开连接"""
        pass

    def publish(self, topic: str, payload: bytes) -> bool:
        """发布消息"""
        pass

    def subscribe(self, topic: str, qos: int = 2) -> bool:
        """订阅主题"""
        pass

    def set_on_message_callback(self, callback: Callable[[bytes], None]):
        """设置消息回调"""
        pass

    def is_connected(self) -> bool:
        """检查连接状态"""
        pass

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        pass

    def _on_disconnect(self, client, userdata, rc):
        """断开回调"""
        pass

    def _on_message(self, client, userdata, msg):
        """消息回调"""
        pass
```

#### 3.3.2 ModbusMaster

```python
class ModbusMaster:
    """Modbus 主站管理器"""

    def __init__(self, host: str, port: int, pool_size: int = 3, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool: List[socket.socket] = []
        self._lock = threading.Lock()

    def read(self, slave_id: int, func_code: int, start_addr: int, quantity: int) -> Optional[bytes]:
        """读取 Modbus 数据"""
        pass

    def write_single(self, slave_id: int, func_code: int, addr: int, value: int) -> bool:
        """写入单个寄存器"""
        pass

    def _get_connection(self) -> Optional[socket.socket]:
        """获取连接"""
        pass

    def _create_connection(self) -> Optional[socket.socket]:
        """创建新连接"""
        pass

    def _close_all(self):
        """关闭所有连接"""
        pass
```

#### 3.3.3 DataScheduler

```python
class DataScheduler:
    """数据调度器"""

    def __init__(self, modbus_master: ModbusMaster):
        self.modbus_master = modbus_master
        self._jobs: Dict[str, DataCollectionJob] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_job(self, job_id: str, config: DataConfig, callback: Callable[[str, bytes], None]):
        """添加采集任务"""
        pass

    def remove_job(self, job_id: str):
        """移除采集任务"""
        pass

    def start(self):
        """启动调度器"""
        pass

    def stop(self):
        """停止调度器"""
        pass

    def _run_loop(self):
        """运行循环"""
        pass

    def _execute_job(self, job: DataCollectionJob):
        """执行采集任务"""
        pass
```

#### 3.3.4 ModbusTCPServer

```python
class ModbusTCPServer:
    """Modbus TCP 服务器"""

    def __init__(self, host: str = "127.0.0.1", port: int = 502):
        self.host = host
        self.port = port
        self._server_socket: Optional[socket.socket] = None
        self._running = False
        self._device_pool: Optional[DevicePool] = None
        self._thread: Optional[threading.Thread] = None

    def set_device_pool(self, pool: DevicePool):
        """设置设备池"""
        pass

    def start(self):
        """启动服务器"""
        pass

    def stop(self):
        """停止服务器"""
        pass

    def _accept_loop(self):
        """接受连接循环"""
        pass

    def _handle_client(self, client_socket: socket.socket, addr: tuple):
        """处理客户端请求"""
        pass
```

#### 3.3.5 VirtualDevice

```python
@dataclass
class VirtualDevice:
    """虚拟从站设备"""

    slave_id: int
    coils: Dict[int, bool] = field(default_factory=dict)
    discrete_inputs: Dict[int, bool] = field(default_factory=dict)
    holding_registers: Dict[int, int] = field(default_factory=dict)
    input_registers: Dict[int, int] = field(default_factory=dict)

    def read_coils(self, start_addr: int, quantity: int) -> bytes:
        """读取线圈"""
        pass

    def read_discrete_inputs(self, start_addr: int, quantity: int) -> bytes:
        """读取离散输入"""
        pass

    def read_holding_registers(self, start_addr: int, quantity: int) -> bytes:
        """读取保持寄存器"""
        pass

    def read_input_registers(self, start_addr: int, quantity: int) -> bytes:
        """读取输入寄存器"""
        pass

    def write_single_coil(self, addr: int, value: bool) -> bool:
        """写入单个线圈"""
        pass

    def write_single_register(self, addr: int, value: int) -> bool:
        """写入单个寄存器"""
        pass

    def update_data(self, addr: int, value: Any, data_type: str):
        """更新数据"""
        pass
```

### 3.4 协议处理器设计

```python
from abc import ABC, abstractmethod

class ProtocolHandler(ABC):
    """协议处理器基类"""

    def __init__(self, config_manager: ConfigManager, mqtt_manager: MQTTClientManager):
        self.config_manager = config_manager
        self.mqtt_manager = mqtt_manager

    @abstractmethod
    def handle(self, payload: bytes) -> Optional[bytes]:
        """处理协议 payload，返回响应（如果有）"""
        pass

    @property
    @abstractmethod
    def function_code(self) -> int:
        """返回处理的功能码"""
        pass


class DataConfigHandler(ProtocolHandler):
    """数据配置处理器 (0x04)"""

    @property
    def function_code(self) -> int:
        return 0x04

    def handle(self, payload: bytes) -> Optional[bytes]:
        """处理数据配置"""
        # 1. 解析数据组数
        # 2. 解析每组配置
        # 3. 更新配置管理器
        # 4. 返回确认响应
        pass
```

***

## 四、协议格式

### 4.1 MQTT 协议

#### 4.1.1 主题定义

| 主题 | 方向 | QoS | 说明 |
|------|------|-----|------|
| `/dtu/{serial}/up` | 上行 | 2 | 模拟器 → 平台 |
| `/dtu/{serial}/down` | 下行 | 0 | 平台 → 模拟器 |

#### 4.1.2 设备序列号

`A1B2C3D4`

### 4.2 功能码

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

### 4.3 协议格式详解

#### 04 下发数据配置（下行）

```
┌─────────┬─────────┬─────────────────────────────────────────────────┐
│ 1字节   │ 2字节   │ n×6字节 (每组数据)                              │
│ 功能码   │ 数据组数 │ 从站(1) + 类型(1) + 地址(2) + 数量(2)          │
│  0x04   │ 大端    │                                                │
└─────────┴─────────┴─────────────────────────────────────────────────┘
```

#### 05 数据上发（上行）

```
┌─────────┬─────────┬─────────────────────────────────────────────────────────┐
│ 1字节   │ 2字节   │ n组数据                                               │
│ 功能码   │ 数据组数 │ 每组: 从站(1)+类型(1)+地址(2)+长度(2)+数据(n)         │
│  0x05   │ 大端    │                                                       │
└─────────┴─────────┴─────────────────────────────────────────────────────────┘
```

| 字段 | 字节数 | 说明 |
|------|--------|------|
| 数据长度 | 2 | **实际字节数**，大端 |

**数据长度计算**：
- 寄存器区域(3,4)：长度 = 寄存器数 × 2
- 线圈/离散输入区域(0,1)：长度 = ceil(数量/8)

***

## 五、开发计划

### 5.1 里程碑

| 阶段 | 里程碑 | 交付物 | 预计工时 |
|------|--------|--------|----------|
| M1 | 项目初始化 | 项目结构、配置文件、依赖 | 1小时 |
| M2 | 核心引擎层 | MQTTManager、ModbusMaster、ConfigManager | 4小时 |
| M3 | Modbus TCP 服务器 | TCPServer、VirtualDevice、DevicePool | 4小时 |
| M4 | 协议处理层 | 所有 Handler 实现 | 4小时 |
| M5 | 数据调度层 | DataScheduler、DataRegistry | 3小时 |
| M6 | 集成测试 | 全链路测试脚本 | 2小时 |
| M7 | 文档与交付 | 完整文档、用户手册 | 2小时 |

**总工期**：约 20 小时

### 5.2 开发任务分解

#### Phase 1: 项目初始化 (M1)

| 任务 | 说明 | 产出 |
|------|------|------|
| T1.1 | 创建项目目录结构 | 完整目录 |
| T1.2 | 创建 config.py | 配置文件 |
| T1.3 | 创建 requirements.txt | 依赖清单 |
| T1.4 | 创建 __init__.py 文件 | Python 包 |

#### Phase 2: 核心引擎层 (M2)

| 任务 | 说明 | 产出 |
|------|------|------|
| T2.1 | 实现 MQTTClientManager | mqtt_client.py |
| T2.2 | 实现 ModbusMaster | modbus_master.py |
| T2.3 | 实现 ConfigManager | config_manager.py |

#### Phase 3: Modbus TCP 服务器 (M3)

| 任务 | 说明 | 产出 |
|------|------|------|
| T3.1 | 实现 VirtualDevice | virtual_device.py |
| T3.2 | 实现 DevicePool | device_pool.py |
| T3.3 | 实现 ModbusTCPServer | tcp_server.py |
| T3.4 | 实现 RequestDispatcher | request_dispatcher.py |
| T3.5 | 实现 ResponseBuilder | response_builder.py |

#### Phase 4: 协议处理层 (M4)

| 任务 | 说明 | 产出 |
|------|------|------|
| T4.1 | 实现 Handler 基类 | handler.py |
| T4.2 | 实现 HeartbeatHandler | heartbeat_handler.py |
| T4.3 | 实现 ModuleConfigHandler | module_config_handler.py |
| T4.4 | 实现 DataConfigHandler | data_config_handler.py |
| T4.5 | 实现 RemoteWriteHandler | remote_write_handler.py |
| T4.6 | 实现 ProtocolRouter | router.py |

#### Phase 5: 数据调度层 (M5)

| 任务 | 说明 | 产出 |
|------|------|------|
| T5.1 | 实现 DataScheduler | data_scheduler.py |
| T5.2 | 实现 DataRegistry | data_registry.py |
| T5.3 | 集成调度与采集 | 完整数据流 |

#### Phase 6: 集成测试 (M6)

| 任务 | 说明 | 产出 |
|------|------|------|
| T6.1 | 单元测试 | 各模块测试 |
| T6.2 | 集成测试 | 全链路测试 |
| T6.3 | 手动测试脚本 | test_04_send.py |

#### Phase 7: 文档与交付 (M7)

| 任务 | 说明 | 产出 |
|------|------|------|
| T7.1 | API 文档 | 代码注释 |
| T7.2 | 用户手册 | README.md |
| T7.3 | 部署指南 | DEPLOYMENT.md |

### 5.3 每日开发计划

| Day | 目标 | 完成里程碑 |
|-----|------|-----------|
| Day 1 | M1 + M2 | 完成核心引擎层 |
| Day 2 | M3 | 完成 Modbus TCP 服务器 |
| Day 3 | M4 | 完成协议处理层 |
| Day 4 | M5 + M6 | 完成数据调度和集成测试 |
| Day 5 | M7 | 完成文档和交付 |

***

## 六、测试策略

### 6.1 测试金字塔

```
                    ▲
                   /│\
                  / │ \
                 /  │  \
                /   │   \
               /    │    \
              /     │     \
             /      │      \
            /       │       \
           /────────┴─────────\
          /                     \
         /                       \
        /                         \
       /───────────────────────────\
      │         UI/Manual          │
      │─────────────────────────────│
      │        E2E / Integration    │
      │─────────────────────────────│
      │         Unit Tests          │
      │─────────────────────────────│
```

### 6.2 单元测试 (Unit Tests)

| 模块 | 测试用例 | 验证点 |
|------|----------|--------|
| MQTTClientManager | test_connect_success | 连接成功 |
| MQTTClientManager | test_connect_failure | 连接失败处理 |
| MQTTClientManager | test_publish | 发布消息 |
| MQTTClientManager | test_subscribe | 订阅主题 |
| ModbusMaster | test_read_success | 读取成功 |
| ModbusMaster | test_read_timeout | 读取超时 |
| ModbusMaster | test_write_success | 写入成功 |
| VirtualDevice | test_read_coils | 读取线圈 |
| VirtualDevice | test_read_registers | 读取寄存器 |
| VirtualDevice | test_write_coil | 写入线圈 |
| VirtualDevice | test_write_register | 写入寄存器 |
| DataConfigHandler | test_parse_config | 解析配置 |
| DataScheduler | test_add_job | 添加任务 |
| DataScheduler | test_remove_job | 移除任务 |

### 6.3 集成测试 (Integration Tests)

| 测试用例 | 验证点 |
|----------|--------|
| test_mqtt_to_handler | MQTT 消息 → Handler → 响应 |
| test_handler_to_modbus | Handler → ModbusMaster → TCPServer |
| test_data_upload_flow | 配置 → 采集 → 上发 |
| test_full链路 | 平台 → MQTT → Handler → Modbus → 上发 → 平台 |

### 6.4 性能测试

| 指标 | 目标 | 说明 |
|------|------|------|
| MQTT 延迟 | < 100ms | 消息发送延迟 |
| Modbus 读取延迟 | < 50ms | 读取响应时间 |
| 并发连接数 | ≥ 10 | 同时连接数 |
| 内存占用 | < 100MB | 正常运行内存 |

### 6.5 用户验收测试 (UAT)

| 场景 | 操作 | 预期结果 |
|------|------|----------|
| 启动测试 | 运行模拟器 | 成功连接 MQTT 和 Modbus TCP |
| 心跳测试 | 等待 30 秒 | 收到心跳包 (0x00) |
| 下发配置测试 | 发送 04 配置 | 模拟器解析并返回确认 |
| 数据上发测试 | 发送 04 配置后等待 | 收到 05 数据上发 |
| 远程置数测试 | 发送 06 指令 | Modbus 寄存器值更新 |

### 6.6 测试脚本

```python
#!/usr/bin/env python3
"""
测试脚本：验证全链路
"""

def test_heartbeat():
    """测试心跳"""
    # 1. 启动模拟器
    # 2. 等待 30 秒
    # 3. 验证收到心跳

def test_data_config():
    """测试数据配置"""
    # 1. 发送 04 配置
    # 2. 验证收到确认响应

def test_data_upload():
    """测试数据上发"""
    # 1. 发送 04 配置
    # 2. 等待发送间隔
    # 3. 验证收到 05 数据上发

def test_remote_write():
    """测试远程置数"""
    # 1. 发送 06 远程置数
    # 2. 验证 Modbus 值更新
```

***

## 七、部署指南

### 7.1 环境要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| pip | 22.0+ | 包管理器 |

### 7.2 安装步骤

```bash
# 1. 克隆项目
cd simulator

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行测试
python -m pytest tests/

# 5. 启动模拟器
python main.py
```

### 7.3 配置

编辑 `config.py`：

```python
# MQTT 配置
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

# 设备配置
DEVICE_SERIAL = "A1B2C3D4"
UP_TOPIC = f"/dtu/{DEVICE_SERIAL}/up"
DOWN_TOPIC = f"/dtu/{DEVICE_SERIAL}/down"

# Modbus 配置
MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 502

# 行为配置
HEARTBEAT_INTERVAL = 30  # 秒
DATA_UPLOAD_INTERVAL = 30  # 秒
```

***

## 八、风险管理

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| MQTT 连接不稳定 | 高 | 中 | 实现自动重连机制 |
| Modbus 连接池耗尽 | 中 | 低 | 限制连接数，超时回收 |
| 数据解析错误 | 高 | 中 | 添加协议验证，错误处理 |
| 并发问题 | 中 | 低 | 使用线程锁保护共享资源 |
| 内存泄漏 | 中 | 低 | 定期清理连接池 |

***

## 九、后续扩展

### 9.1 潜在功能

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 多从站支持 | 支持动态添加/移除从站 | P1 |
| 数据模拟规则 | 自定义数据变化规则 | P2 |
| Web 管理界面 | 可视化配置和管理 | P3 |
| REST API | 提供 HTTP 管理接口 | P3 |
| 性能监控 | 监控连接数、消息数等 | P4 |

### 9.2 优化方向

| 方向 | 说明 |
|------|------|
| 异步 I/O | 使用 asyncio 重构网络层 |
| 连接池优化 | 智能连接复用和回收 |
| 数据压缩 | 减少 MQTT 消息大小 |
| TLS 安全 | MQTT TLS 连接支持 |

***

**文档版本**：v3.0 (全新设计)
**更新日期**：2026-05-02
**状态**：待开发
