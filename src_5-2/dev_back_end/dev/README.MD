# 后端服务 (GoFrame)

## 项目概述
基于 GoFrame 框架的工业物联网平台后端服务，支持：
- Modbus + MQTT 设备通信（远程 Broker: 112.6.224.25:20042）
- 数据采集与存储 (MySQL + InfluxDB 2.x)
- 设备管理与配置
- 离线检测机制（3分钟超时自动离线）

## 项目结构
```
dev/
├── api/                  # API 接口定义
│   └── dev/v1/          # v1 版本接口
│       ├── device.go
│       ├── payload.go
│       ├── sendcod.go   # 方案2 接口
│       ├── user.go
│       └── variables.go
├── internal/
│   ├── logic/           # 核心业务逻辑
│   │   ├── payload.go   # 协议解析（上行）
│   │   ├── sendcod.go   # 协议编码（下行，方案2）+ PayloadOptimizer
│   │   ├── mqtt.go      # MQTT 连接管理
│   │   └── ...
│   ├── controller/      # HTTP 控制器
│   ├── dao/             # 数据访问
│   ├── model/           # 数据模型
│   ├── service/         # 服务层
│   └── cmd/cmd.go       # 启动入口 + 离线检测定时任务
├── utility/             # 工具类
│   ├── scanner.go       # 字节流读取器
│   └── datatype_codec.go # 数据类型编解码器（6种类型支持）
├── main.go              # 入口文件
└── config.yaml          # 配置文件
```

## 核心文件说明
| 文件 | 功能 |
|------|------|
| internal/logic/payload.go | 上行协议解析（0x00心跳、0x01/0x03查询、0x05数据上报 + 增强写入 InfluxDB） |
| internal/logic/sendcod.go | 下行协议编码（0x02模组配置、0x04数据配置、0x06远程置数）、PayloadOptimizer 优化器 |
| internal/logic/mqtt.go | MQTT 连接、订阅、发布 |
| internal/controller/payload.go | HTTP 接口实现（方案1 /payload、方案2 /sendcod/*、InfluxDB 查询） |
| internal/cmd/cmd.go | 启动入口 + 离线检测定时任务（每60秒检查，3分钟超时） |
| utility/scanner.go | 字节流读取器 |
| utility/datatype_codec.go | 数据类型编解码器（bool/int16/int32/float32/float64/string） |

## 离线检测机制
后端启动后会在后台 goroutine 中运行定时任务：
- 每 **60 秒** 检查一次
- 设备 **3 分钟** 没有更新 `latest_online` 则自动设为离线
- 实现位置：`internal/cmd/cmd.go` → `startOfflineDetection()`

## 快速启动
```bash
go run main.go
# 默认端口 8000
```

## 配置说明
编辑 `config.yaml` 修改：
- 数据库连接
- MQTT Broker 地址
- HTTP 端口

## 依赖
- Go 1.20+
- GoFrame v2
- MySQL 8.0
- InfluxDB 2.x
- Redis
