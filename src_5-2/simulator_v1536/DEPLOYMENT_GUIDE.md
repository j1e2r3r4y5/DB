# 完整部署指南

## 项目概述

本项目包含两个部分：
1. **后端模拟器**：DTU + Modbus 设备模拟器
2. **前端管理界面**：Vue 3 + Element Plus 管理平台

---

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| Node.js | 16+ |
| npm | 8+ |

---

## 部署步骤

### 第一步：启动后端模拟器

#### 方式一：使用地址段配置（推荐）

```bash
cd simulator_v1536
python main.py --config address_segments_final.txt
```

#### 方式二：使用默认配置

```bash
cd simulator_v1536
python main.py
```

**服务信息：**
- Modbus TCP Server: 127.0.0.1:502
- MQTT Broker: 127.0.0.1:1883 (需要本地 MQTT Broker)
- DTU 序列号: A1B2C3D4 (可在 config.py 中配置)

---

### 第二步：启动前端开发服务器

```bash
cd ../4G_dev_front/4G_dev
npm run dev
```

**默认访问地址：**
http://localhost:5173

---

## 地址段配置说明

当前配置文件 `address_segments_final.txt`：

```plaintext
# 变量名（段序号） | 分区 | 起始地址 | 长度 | 变量名 | 类型 | 初始值
1  0  0    8    1    bool  1
2  0  8    8    2    bool  1
3  0  16   8    3    bool  1
4  0  24   8    4    bool  1
5  1  0    8    5    bool  1
6  1  8    8    6    bool  1
7  1  16   8    7    bool  1
8  1  32   8    8    bool  1
9  3  0    13   9    string  ABCDEFGHIJKLM
10 3  13   13   10   string  ABCDEFGHIJKLM
11 4  0    13   11   string  ABCDEFGHIJKLM
12 4  13   13   12   string  ABCDEFGHIJKLM
```

### 前端配置对应表

| 变量名 | 数据类型 | 分区 | Modbus 站号 | 数据地址 | 寄存器数量 | 字符串长度 |
|--------|---------|------|------------|----------|----------|----------|
| 1 | 布尔值 | 0区 | 1 | 0 | 1 | - |
| 2 | 布尔值 | 0区 | 1 | 8 | 1 | - |
| 3 | 布尔值 | 0区 | 1 | 16 | 1 | - |
| 4 | 布尔值 | 0区 | 1 | 24 | 1 | - |
| 5 | 布尔值 | 1区 | 1 | 0 | 1 | - |
| 6 | 布尔值 | 1区 | 1 | 8 | 1 | - |
| 7 | 布尔值 | 1区 | 1 | 16 | 1 | - |
| 8 | 布尔值 | 1区 | 1 | 32 | 1 | - |
| 9 | 字符串 | 3区 | 1 | 0 | 7 | 13 |
| 10 | 字符串 | 3区 | 1 | 13 | 7 | 13 |
| 11 | 字符串 | 4区 | 1 | 0 | 7 | 13 |
| 12 | 字符串 | 4区 | 1 | 13 | 7 | 13 |

---

## 前端使用流程

1. **启动项目**：访问 http://localhost:5173
2. **登录/选择设备**：进入设备管理
3. **添加变量**：
   - 点击「新建变量」
   - 按照上面的配置表逐个添加
4. **下发配置**：
   - 全选 12 个变量
   - 点击「下发」按钮
5. **查看数据**：在数据管理页面查看实时数据

---

## 项目文件说明

### 后端

| 文件 | 说明 |
|------|------|
| main.py | 主入口 |
| address_segments_final.txt | 地址段配置 |
| data/address_segment.py | 地址段管理模块 |
| data/virtual_device.py | 虚拟设备 |

### 前端

| 文件 | 说明 |
|------|------|
| src/components/variables/variables.vue | 变量管理页 |
| src/components/variables/addvariables.vue | 添加变量弹窗 |
| src/utils/datatype.js | 数据类型定义 |

---

## 常见问题

### 1. 后端无法连接 MQTT

确保本地已启动 MQTT Broker，或修改 `config.py` 中的 MQTT 地址：

```python
MQTT_BROKER = "127.0.0.1"  # 修改为实际 Broker 地址
```

### 2. 端口占用

如果 502 或 5173 端口被占用，可以修改配置或释放端口。

### 3. 前端 API 请求

确保后端 API 地址配置正确，查看 `src/utils/request.js`。
