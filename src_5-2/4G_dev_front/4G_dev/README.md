# 前端界面 (Vue 3 + Vite)

## 项目概述
基于 Vue 3 + ElementPlus 的工业物联网平台前端界面，支持：
- 设备管理与配置
- 变量管理与数据配置
- 数据查询与可视化
- 远程置数操作

## 项目结构
```
4G_dev/
├── src/
│   ├── api/
│   │   └── index.js           # HTTP 接口封装（方案1 + 方案2）
│   ├── components/
│   │   ├── DeviceDownDialog.vue     # 设备配置弹窗（0x02）
│   │   ├── variables/
│   │   │   ├── Features.vue         # 变量管理（0x03/0x04）
│   │   │   └── RemoteWriteDialog.vue # 远程置数（0x06）
│   │   └── ...
│   ├── router/              # 路由配置
│   ├── view/                # 页面视图
│   └── main.js              # 入口文件
├── package.json
└── vite.config.js
```

## 核心组件说明
| 组件 | 功能 | 协议码 |
|------|------|--------|
| DeviceDownDialog.vue | 设备配置（发送模式、波特率） | 0x02 |
| variables/Features.vue | 变量管理（查询、配置） | 0x03 / 0x04 |
| - 空配置支持 | 下发空配置，清空所有数据采集，停止上报 | - |
| - 二次确认 | 空配置下发时弹窗确认，防止误操作 | - |
| variables/RemoteWriteDialog.vue | 远程置数（写入寄存器） | 0x06 |
| data/data.vue | 数据管理（显示、历史数据） | - |
| - 默认显示 | 只显示已下发配置的变量 | - |
| - 空配置提示 | 显示「暂无数据」 | - |
| - 显示所有变量 | 可勾选显示全部6个变量 | - |

## API 说明
所有接口封装在 `src/api/index.js`：
- 方案2（推荐）：`sendModuleConfig`、`sendDataConfig`、`queryDataConfig`、`remoteWrite`
- 方案1（保留）：`sendPayload`

## 快速启动
```bash
npm install
npm run dev
# 默认端口 4325
```

## 技术栈
- Vue 3 (Composition API)
- Vite (构建工具)
- ElementPlus (UI 框架)
- Axios (HTTP 请求)
