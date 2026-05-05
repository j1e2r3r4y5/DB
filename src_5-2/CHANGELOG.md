# 变更日志 (Changelog)

所有重要的项目变更都将记录在此文件中。

## [1.5.0] - 2026-05-04

### 发送模式UI修复与文档更新

#### 前端修复

1. **修复DeviceDownDialog.vue发送模式选项**
   - 移除未实现的"线圈置位"和"寄存器变化"选项
   - 仅保留已实现的"定时发送"选项
   - 将发送模式选择框设为禁用状态，防止误操作
   - 统一标签固定显示"发送间隔(秒)"
   - 修改文件: `4G_dev_front/4G_dev/src/components/DeviceDownDialog.vue`

#### 文档更新

2. **更新PROJECT_README.md**
   - 添加发送模式说明部分
   - 明确记录当前仅支持定时发送模式
   - 更新前端组件说明中的配置项描述

## [1.4.0] - 2026-05-04

### 目录重命名与项目结构最终优化

#### 目录重命名

1. **重命名后端目录**
   - `dev _back_end/` → `dev_back_end/`
   - 解决目录名含空格导致的命令行不便问题
   - 所有相关文档和脚本已同步更新

2. **更新所有引用**
   - `PROJECT_README.md`：更新所有目录引用
   - `tools/deploy/*.ps1`：更新所有启动脚本中的路径
   - `CHANGELOG.md`：更新历史记录中的目录名

#### 旧日志归档

3. **归档历史日志**
   - 将 `tools/debug/` 中的历史日志移至 `tools/debug/archive/` 目录
   - 保持主目录整洁

---

## [1.3.0] - 2026-05-04

### 项目完整性与整洁性全面优化

#### 项目结构整理

1. **整理根目录临时文件**
   - 归档测试脚本：将根目录所有测试脚本移至 `tests/` 目录（9个文件）
   - 归档调试工具：将根目录所有调试工具移至 `tools/debug/` 目录（19个文件）
   - 归档部署工具：将根目录部署脚本移至 `tools/deploy/` 目录（4个文件）
   - 根目录现在只保留核心文档与项目目录

2. **清理临时文件**
   - 清理 `dev_back_end/dev/` 临时可执行文件
   - 清理 `simulator_v3/` 所有 `__pycache__` 目录和 `.pyc` 缓存文件（40+个文件）
   - 添加根目录 `.gitignore`，防止临时文件误提交

#### 文档体系完善

3. **补充所有子目录 README 文档**
   - `dev_back_end/dev/README.MD`：后端服务项目结构、核心文件说明
   - `tests/README.md`：测试脚本清单与使用说明
   - `tools/debug/README.md`：调试工具清单与使用说明
   - `tools/deploy/README.md`：部署工具清单与使用说明
   - `4G_dev_front/4G_dev/README.md`：前端界面项目结构、核心组件说明

4. **更新根目录文档**
   - `PROJECT_README.md`：优化项目结构快速索引
   - `MD/README.md`：完善导航文档
   - 新增 `.trae/specs/project-completeness-verification/`：项目完整性验证文档

5. **创建验证检查清单**
   - 完成项目完整性验证
   - 验证所有核心服务正常运行
   - 所有测试通过

#### 技术优化

6. **MQTT连接问题修复**
   - 确保MQTT Broker正常运行
   - 确保后端成功订阅设备主题
   - 确保设备状态正确更新

---

## [1.2.0] - 2026-05-03

### 决策传导链条分析与系统性修复

#### 文档新增

1. **新增决策传导机制分析固化文档** (`MD/决策传导机制分析固化文档.md`)
   - 完整分析L0→L1→L2→L3→L4决策传导路径
   - 包含决策传导时间节点、责任主体、关键控制点
   - 建立决策环节关联矩阵
   - 提供决策链条关系图（ASCII格式）

2. **新增决策要素台账** (`MD/决策要素台账.md`)
   - 记录每个决策环节的决策依据、主体、方法、输出
   - 建立62个决策要素的完整追溯索引
   - 包含决策变更记录

3. **新增决策合理性与风险评估报告** (`MD/决策合理性与风险评估报告.md`)
   - 综合评分89.3/100（良好）
   - 识别7项风险，制定应对策略
   - 提出短中长期优化建议

4. **新增问题筛查与优先级排序报告** (`MD/问题筛查与优先级排序报告.md`)
   - 系统性筛查识别20个问题
   - 高严重程度(P0)问题3个
   - 中严重程度(P1)问题8个

5. **新增代码质量与安全筛查报告** (`MD/代码质量与安全筛查报告.md`)
   - 全面系统性代码质量与安全筛查
   - 识别31个问题（Critical 1个, High 3个, Medium 10个, Low 17个）
   - 涵盖安全漏洞、逻辑缺陷、资源管理、代码规范等领域
   - 提供修复建议和优先级排序
   - 低严重程度(P2)问题9个

#### 文档更新 (v1.2.1)

根据用户纠正的决策传导层级关系，更新以下文档：

1. **更新决策传导机制分析固化文档** (`MD/决策传导机制分析固化文档.md`)
   - 版本更新至v2.0
   - 修正决策传导路径：
     - L0决定L1
     - L2适配L1（L2需求设计需适配L1的扩展要求）
     - L2决定L3
     - L0和L1共同决定L4
   - 新增2.4节：L0/L1→L4传导链路分析
   - 更新风险矩阵，增加L1→L2适配偏差和L0/L1→L4不一致风险

2. **更新决策要素台账** (`MD/决策要素台账.md`)
   - 版本更新至v2.0
   - 明确决策传导关系：
     - L0决定L1
     - L2适配L1
     - L2决定L3
     - L0和L1共同决定L4
   - 新增L4层决策传导关系说明
   - 更新决策要素追溯索引

3. **更新决策合理性与风险评估报告** (`MD/决策合理性与风险评估报告.md`)
   - 版本更新至v2.0
   - 新增决策传导关系说明
   - 增加L1→L2适配评估和L0/L1→L4共同决定评估
   - 新增高风险项详细分析

#### 高优先级缺陷修复

1. **修复06远程置数协议格式解析错误** (`simulator_v3/protocol/remote_write_handler.py`)
   - 修正value字节位置：线圈类型从`payload[7]`改为`payload[6]`
   - 修正长度检查：从8字节改为7字节
   - 确保符合agreement.md协议定义

2. **修复P0-02: 数据上传间隔控制问题** (`simulator_v3/main.py`)
   - 添加`last_upload_time`追踪上次上传时间
   - 添加`current_time`计算实现精确间隔控制
   - 确保数据上发严格按照配置的`send_interval`间隔进行

3. **修复P0-03: 变量地址初始化不一致** (`simulator_v3/config.py`, `simulator_v3/data/virtual_device.py`, `simulator_v3/main.py`)
   - 新增常量定义：
     - `SLAVE_1_HOLDING_REG_TEMPERATURE = 0`
     - `SLAVE_1_HOLDING_REG_HUMIDITY = 1`
     - `SLAVE_1_HOLDING_REG_POWER = 9`
     - `SLAVE_1_COIL_SWITCH = 0`
   - 统一使用常量替代硬编码地址
   - 消除多处初始化不一致风险

4. **修复P0-04: _on_data_collected空实现问题** (`simulator_v3/main.py`, `simulator_v3/data/data_scheduler.py`)
   - 扩展回调函数签名：`_on_data_collected(job_id, slave_id, func_code, start_addr, quantity, data)`
   - 在回调中收集待发送数据到`_pending_data`列表
   - 更新DataScheduler的回调签名以传递完整的采集信息

#### 功能增强修复

5. **新增_simulate_data_changes方法** (`simulator_v3/main.py`)
   - 在数据上传前调用模拟方法
   - 启用温度、湿度、功率、开关的动态模拟
   - 解决数据静态不变的问题

6. **修复P1-01: 数据模拟功能未启用** (`simulator_v3/main.py`)
   - 在`_start_data_upload_loop`中调用`_simulate_data_changes()`
   - 每次上传前自动更新模拟数据

7. **修复P1-06: 线圈翻转未实现** (`simulator_v3/main.py`)
   - 在`_simulate_data_changes`中添加`device.toggle_switch()`调用
   - 实现开关状态的自动翻转功能

8. **修复P1-10: upload_interval变量未使用** (`simulator_v3/main.py`)
   - 删除未使用的`upload_interval`变量
   - 清理代码冗余

9. **修复P1-03: Modbus连接池心跳检测问题** (`simulator_v3/core/modbus_master.py`)
   - 在`_create_connection`中添加`SO_KEEPALIVE`选项
   - 使用`recv(7, MSG_PEEK)`替代空字节发送进行连接验证
   - 避免在某些Modbus设备上导致协议错误

10. **修复P1-07: 缺少重连次数限制** (`simulator_v3/core/mqtt_client.py`)
    - 添加`_max_reconnect_attempts = 10`最大重连次数
    - 添加`_reconnect_attempts`计数器
    - 超过最大次数后停止重连并记录错误日志

#### 新增单元测试

11. **新增test_mqtt_client.py** (`simulator_v3/tests/test_mqtt_client.py`)
    - 测试MQTT重连逻辑
    - 测试QoS配置一致性
    - 测试最大重连次数限制

12. **新增test_modbus_master.py** (`simulator_v3/tests/test_modbus_master.py`)
    - 测试连接池SO_KEEPALIVE选项
    - 测试连接验证使用recv替代send

13. **修复ModbusConnection初始化bug** (`simulator_v3/core/modbus_master.py`)
    - 修复`_create_connection`中`ModbusConnection(sock)`缺少`last_used`参数
    - 修改为`ModbusConnection(sock, time.time())`

14. **测试用例修复** (`simulator_v3/tests/test_modbus_master.py`)
    - 修复测试以匹配实际代码实现
    - 所有96个测试用例通过

## [1.1.4] - 2026-05-02

### 协议格式系统性修复（基于agreement.md）

#### 高优先级缺陷修复

1. **修复DataConfigHandler响应格式** (`data_config_handler.py`)
   - 协议定义：04响应 = `[04, 状态]` = **2字节**
   - `_handle_config_result()`: 长度检查改为2字节，移除多余的group_count解析
   - `_build_config_result()`: 返回格式改为2字节 `bytes([04, result])`

2. **修复RemoteWriteHandler下行解析** (`remote_write_handler.py`)
   - 协议定义：06下发 = `[06, 类型, 地址(2B), 数量(2B), 数值]` = **7-8字节**
   - `_handle_remote_write()`: 正确解析类型、地址、数量、值
   - 根据类型(data_type=0或4)正确提取value的起始位置

3. **修复RemoteWriteHandler响应格式** (`remote_write_handler.py`)
   - 协议定义：06响应 = `[06, 类型, 地址(2B), 数量(2B), 状态]` = **7字节**
   - 响应格式改为7字节

4. **修复RemoteWriteHandler创建方法** (`remote_write_handler.py`)
   - `create_remote_write()`: 根据data_type正确构建7-8字节数据
   - data_type=0(线圈): 7字节，最后1字节为值
   - data_type=4(寄存器): 8字节，最后2字节为值

#### 测试更新

5. **更新测试用例匹配协议格式** (`test_protocol.py`, `test_protocol_edge_cases.py`)
   - 修正所有响应长度检查
   - 修正所有字节索引验证

## [1.1.2] - 2026-05-02

### 系统性问题识别与修复

#### 高优先级缺陷修复

1. **修复DownPayloadHandler错误处理缺失** (`payload.go`)
   - 所有MQTT Publish操作现在都会检查错误并返回
   - 添加了topic格式验证 (`len(parts) < 3`)
   - 设备序列号提取增加了错误处理
   - 所有下发功能码(01/02/03/04/06)都有完整的错误处理

2. **修复ModuleConfigHandler常量命名混淆** (`module_config_handler.py`)
   - 重命名常量以消除歧义：
     - `MODULE_CONFIG_QUERY` → `QUERY_CONFIG_DOWN`
     - `MODULE_CONFIG_UPLOAD` → `UPLOAD_CONFIG_UP`
     - `DOWNLOAD_MODULE_CONFIG` → `DOWNLOAD_CONFIG_DOWN`
     - `MODULE_CONFIG_RESULT` → `CONFIG_RESULT_UP`
   - 方法名统一更新：
     - `_handle_module_config_query` → `_handle_query_config`
     - `_handle_module_config_upload` → `_handle_upload_config`
     - `_handle_download_module_config` → `_handle_download_config`
     - `_handle_module_config_result` → `_handle_config_result`
     - `create_module_config_upload` → `create_upload_config`
     - `create_module_config_query` → `create_query_config`
   - 修复响应格式：使用常量 `CONFIG_RESULT_UP` 替代硬编码 `0x02`

#### 中优先级优化

3. **修复RemoteWrite响应格式一致性** (`remote_write_handler.py`)
   - `create_remote_write()` 方法现在生成符合协议格式的完整数据：
     - `[0x06, slave_id, data_type, addr_high, addr_low, 0x00, 0x01, 0x01, value_high, value_low]`
   - 与协议文档定义的格式完全一致

#### 测试更新

4. **更新测试用例以匹配新的方法名** (`test_protocol.py`, `test_protocol_edge_cases.py`)
   - 所有对旧方法名的引用已更新为新名称

## [1.1.1] - 2026-05-02

### 位变量与字变量处理模块修复

#### 高优先级缺陷修复

1. **修复modbusType位变量判断逻辑** (`payload.go`)
   - 原：`modbusType == 1 || modbusType == 2`（错误的位变量判断）
   - 新：`modbusType == 0 || modbusType == 1`（0=线圈, 1=离散输入）

2. **修复字变量判断逻辑** (`payload.go`)
   - 原：使用 `else` 分支处理所有非位变量
   - 新：明确使用 `else if modbusType == 3 || modbusType == 4`（3=输入寄存器, 4=保持寄存器）

3. **添加未知ModbusType警告** (`payload.go`)
   - 当遇到未知的ModbusType值时记录警告日志并跳过解析

4. **添加float64字节序支持** (`payload.go`)
   - 扩展 `adjustByteOrder()` 函数支持8字节数据的字节序转换
   - 新增BADC/CDAB/DCBA三种8字节序模式

5. **规范化字节序字符串** (`payload.go`)
   - 添加 `strings.ToUpper(byteOrder)` 确保大小写不敏感

#### 中优先级优化

6. **添加奇数字节数警告** (`payload.go`)
   - 当数据块长度为奇数时记录警告日志
   - 最后一个字节将被正常忽略

## [1.1.0] - 2026-05-02

### 修复的问题

#### 高优先级问题

1. **重构后端Payload解析逻辑** (`dev_back_end/dev/internal/logic/payload.go`)
   - 清理了大量注释代码（从约2000行减少到约650行）
   - 统一了各功能码的解析逻辑
   - 简化了05功能码的数据解析（按数据块+变量映射两级模式）
   - 添加了完整的错误处理和日志记录

2. **统一模拟器与后端的数据解析逻辑** (`simulator_v3/main.py`)
   - 修复了05功能码数据上发时长度字段定义不一致的问题
   - 将 `quantity` 字段从按"数量"计算改为按"字节长度"计算
   - 确保模拟器发送的格式与后端解析的格式完全一致

3. **添加功能码响应验证机制**
   - 修复了 `module_config_handler.py` 的响应格式
     - 原：`[0x02, 0x00, send_mode, 0x00]`
     - 新：`[0x02, 0x00]`
   - 修复了 `data_config_handler.py` 的响应格式
     - 原：`[0x04, 0x00, group_count]` (3字节)
     - 新：`[0x04, 0x00] + uint16(group_count)` (4字节)
   - 修复了 `data_config_handler.py` 的解析逻辑，移除了多余的func_code读取

#### 中优先级问题

4. **优化前端刷新策略** (`4G_dev_front/4G_dev/src/view/home.vue`)
   - 添加了 Page Visibility API 支持，页面不可见时暂停刷新
   - 将刷新间隔从4秒调整为15秒
   - 大幅减少服务器压力

5. **增强DataScheduler调度** (`simulator_v3/data/data_scheduler.py`)
   - 添加了 `update_job_interval()` 方法，支持动态调整单个任务间隔
   - 添加了 `update_all_intervals()` 方法，支持批量更新任务间隔
   - 添加了 `get_statistics()` 方法，返回调度器统计信息
   - 任务间隔最小值限制为1秒

### 新增功能

6. **完善测试覆盖**
   - 新增 `tests/test_data_scheduler.py`：DataScheduler完整单元测试
     - 包含18个测试用例，覆盖调度器所有功能
     - 包含并发访问测试用例
   - 新增 `tests/test_protocol_edge_cases.py`：协议处理器边界测试
     - 包含38个测试用例，覆盖边界条件和错误处理
   - 总测试用例数从约48个增加到86个

### 技术改进

- 所有测试用例通过（86/86 passed）
- 代码质量提升，注释更清晰
- 错误处理更完善

---

## [1.0.0] - 2026-04-30

### 初始版本

- 完整的DTU+Modbus模拟器实现
- MQTT客户端与自动重连
- Modbus TCP服务器与多从站支持
- 7个功能码协议实现 (0x00-0x06)
- 完整的前后端系统架构
- 基础测试覆盖
