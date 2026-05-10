# 变更日志 (Changelog)

所有重要的项目变更都将记录在此文件中。

## [1.10.0] - 2026-05-10

### 优化前基准数据对齐与测试完善

#### 优化前基准统一（前后端对齐
1. **统一优化前基准为 DefaultOptimizer 合并后结果
   - 问题：前端显示合并后05上报长度，但后端返回原始未合并长度，导致显示不一致
   - 修复：后端将 DefaultOptimizer 合并后的结果作为优化前基准
   - 修改文件：`dev_back_end/dev/internal/logic/sendcod.go`
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

2. **前端同步显示优化前基线
   - 移除 rawUploadLength 相关计算
   - 直接使用合并后的 uploadLength 作为优化前基线
   - 显示文字改为"合并后05上报数据包长度（优化前基线）"
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

#### PayloadOptimizer 单元测试完善
3. **完善 Go 后端单元测试
   - 修复 gtest API 使用错误（t.Assert → t.AssertEQ，t.AssertNotNil → t.AssertNE）
   - 新增 11 个测试用例，覆盖：
     - 基础功能测试
     - 边界条件测试
     - 性能基准测试
   - 测试覆盖率从 20.2% 提升至 20.7%
   - 修改文件：`dev_back_end/dev/internal/logic/sendcod_test.go`

#### Python 模拟器修复
4. **修复 address_segment.py 中 unit 与 init_value 字段混淆
   - 问题：unit 字段内容（如"°C"、"%RH"）被错误地解析为 init_value
   - 修复：正确分离 unit（第7列）与 init_value（第8列）的解析
   - 修改文件：`simulator_v1536/data/address_segment.py`

5. **修复 Python 单元测试导入路径
   - 问题：测试文件中错误引用 simulator_v3 模块，导致导入失败
   - 修复：移除所有测试文件中的 simulator_v3 前缀，使用相对导入
   - 修改文件：`simulator_v1536/tests/test_*.py`（共10个测试文件）
   - 所有113个测试用例全部通过

#### 测试执行与验证
6. **执行完整测试套件
   - Go 后端单元测试：所有测试通过
   - Python 模拟器单元测试：113个测试用例全部通过
   - 端到端测试：正常执行
   - 测试覆盖率报告生成

### 优化建议
7. **P0 级别优化已完成
   - PayloadOptimizer 单元测试完善
   - 优化前基准前后端对齐
   - Python 测试修复
   - address_segment.py 字段解析修复

---

## [1.9.0] - 2026-05-09

### 沙箱功能（完整隔离环境）
沙箱是一个独立的测试环境，导入的变量自动标记为沙箱，走独立 MQTT 通道，模拟器生成模拟数据上报，与生产数据完全隔离互不干扰。

#### 后端新增
1. **新增沙箱独立 MQTT 主题订阅**
   - 上行：`/dtu/{serial}/sandbox/up`
   - 下行：`/dtu/{serial}/sandbox/down`
   - MQTT 重连后自动恢复沙箱主题订阅
   - 修改文件：`dev_back_end/dev/internal/logic/mqtt.go`

2. **新增沙箱数据查询 API**
   - `POST /sandbox/dataquery` — 查询沙箱数据（按 scope=sandbox 过滤）
   - 修改文件：`dev_back_end/dev/api/dev/v1/payload.go`、`controller/payload.go`

3. **InfluxDB 写入加 scope 标签**
   - `WritdataToInflux` 和 `WriteEnhancedDataToInflux` 写入时加 `scope` tag
   - 生产数据：`scope=production`（兼容旧数据 `not exists(scope)`）
   - 沙箱数据：`scope=sandbox`
   - 修改文件：`dev_back_end/dev/internal/logic/payload.go`

4. **SendDataConfig 支持 scope 参数**
   - 根据 `scope` 决定下发到生产 topic 或沙箱 topic
   - 修改文件：`dev_back_end/dev/internal/logic/sendcod.go`

5. **变量表加 scope 字段**
   - `model.Variables` 新增 `Scope string` 字段
   - `model.Func04Request` 新增 `Scope string` 字段
   - 数据库：`variables` 表 + `caching` 表加 `scope VARCHAR(20) DEFAULT 'production'`
   - 修改文件：`dev_back_end/dev/internal/model/variables.go`、`sendcod.go`

6. **沙箱变量不触发生产设备 Changeflag**
   - 沙箱变量的新增/删除不会修改生产设备的配置变更标志
   - 修改文件：`dev_back_end/dev/internal/logic/variables.go`

7. **沙箱消息不更新设备在线状态**
   - 沙箱 MQTT 消息不会错误地更新生产设备的在线状态
   - 修改文件：`dev_back_end/dev/internal/logic/mqtt.go`

8. **新增批量导入变量 API**
   - `POST /batch-addvariable` — 一次请求导入全部变量，大幅提升导入速度
   - 新增文件：`dev_back_end/dev/api/dev/v1/variables.go`
   - 新增文件：`dev_back_end/dev/internal/controller/varvariables.go`
   - 新增文件：`dev_back_end/dev/internal/logic/variables.go` → `BatchAddVariable()`
   - 接口定义：`dev_back_end/dev/internal/service/Variable.go`

#### 模拟器新增
9. **新建沙箱虚拟设备**
   - `SandboxVirtualDevice` — 不依赖真实 Modbus，生成模拟数据
   - 支持三种策略：random（随机）、increment（递增）、constant（固定值）
   - 新建文件：`simulator_v1536/data/sandbox_device.py`

10. **沙箱独立上报循环**
    - 订阅 `/dtu/{serial}/sandbox/down` 接收沙箱配置
    - 按生产设备相同的上报间隔生成模拟数据并上报到 `/dtu/{serial}/sandbox/up`
    - 修改文件：`simulator_v1536/main.py`

11. **MQTT 重连自动订阅沙箱主题**
    - `MQTTClientManager` 构造函数新增 `sandbox_down_topic` 参数
    - `_on_connect` 中自动重新订阅沙箱下行主题
    - 修改文件：`simulator_v1536/core/mqtt_client.py`

12. **沙箱配置**
    - 新增 `SANDBOX_UP_TOPIC`、`SANDBOX_DOWN_TOPIC`、`SANDBOX_STRATEGY`
    - 修改文件：`simulator_v1536/config.py`

#### 前端新增
13. **导入变量默认标记为沙箱**
    - `ImportVariablesDialog` 导入时 `scope='sandbox'`
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/ImportVariablesDialog.vue`

14. **变量列表加黄色「沙箱」标签**
    - scope 映射修复（解决标签不显示 bug）
    - 正常变量排前面，沙箱变量排后面
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

15. **下发弹窗沙箱检测**
    - 检测包含沙箱变量时提示"将下发到沙箱通道"
    - 混合选择（沙箱+真实）时禁止下发并提示分开操作
    - scope 参数传入 `sendDataConfig` API
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

16. **数据管理页新增「沙箱数据」Tab**
    - 独立 Tab 展示沙箱变量数据
    - 调用 `/sandbox/dataquery` 查询沙箱数据
    - 沙箱数据带 🧪 标签
    - 修改文件：`4G_dev_front/4G_dev/src/components/data/data.vue`

17. **前端 API 新增**
    - `sandboxDataQuery()` — 沙箱数据查询
    - `batchAddvariable()` — 批量导入变量
    - 修改文件：`4G_dev_front/4G_dev/src/api/index.js`

### 优化与修复

18. **修复 InfluxDB 查询 limit 限制导致变量不显示数据**
    - 问题：`|> limit(n:1000)` 导致 936 个之后的变量查不到最新数据
    - 修复：改为 `|> last()` 只返回每个地址的最新一条数据
    - 修改文件：`dev_back_end/dev/internal/controller/payload.go`

19. **导入变量加并发 + 进度条**
    - 优先调用批量 API（1 次请求），失败回退到并发 5 条逐条导入
    - 带进度条和百分比显示
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/ImportVariablesDialog.vue`

20. **变量管理页加分页**
    - 每页默认 50 条，可选 50/100/200/500
    - 跨页保持选中状态（`reserve-selection`）
    - 翻页后勾选框自动恢复
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

21. **变量管理页初始加载优化**
    - 按设备 ID 过滤查询，不再拉取所有设备的数据
    - 没选设备时不加载数据
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

22. **删除 simulator_v3 目录**
    - 保留增强版 simulator_v1536
    - 更新启动脚本引用路径
    - 修改文件：`tools/deploy/start-all.ps1`

---

## [1.8.0] - 2026-05-09

### 协议修正（03/04/05 "数据数量" → "报文总长度"）

#### 协议文档更新

1. **修正agreement.md和约束.md协议定义**
   - 问题：03/04/05功能码中"2字节数据数量"字段被误解为"数据项数量"，实际含义是"报文总长度"
   - 改动：03上发/04下发/05上发协议定义改为"2字节报文总长度（从功能码开始到报文结束的字节数）"
   - 改动：更新所有示例和解析规则
   - 修改文件：`dev_back_end/dev/resource/配置文件/agreement.md`、`约束.md`

#### 后端解析/编码修正

2. **修正功能码03解析逻辑**
   - 问题：原按"数据项数量"循环解析，实际应按报文总长度计算数据项数量
   - 修复：`dataCount = (totalLen - 3) / 6`
   - 修改文件：`dev_back_end/dev/internal/logic/payload.go`

3. **修正功能码04编码逻辑**
   - 问题：原写入"数据项数量"，实际应写入"报文总长度"
   - 修复：`totalLen = 3 + len(entries) * 6`
   - 修改文件：`dev_back_end/dev/internal/logic/sendcod.go`

4. **修正功能码05解析逻辑**
   - 问题：原按"数据项数量"循环，实际应根据剩余字节数变长循环
   - 修复：`for i := 0; remaining >= 6; i++`，每次循环减去已消耗字节
   - 修改文件：`dev_back_end/dev/internal/logic/payload.go`

5. **修正ParseAndWriteData数据范围计算**
   - 问题1：`readRegCount = len(data) / 2` 整数除法导致 `1/2=0`，`endAddr=-1`，跳过所有变量
   - 修复1：`readRegCount = len(data)`（字节为单位，不再除以2）
   - 问题2：`offset = (modbusAddr - baseAddr) * 2` 多乘了2，导致偏移量翻倍
   - 修复2：`offset = modbusAddr - baseAddr`
   - 修改文件：`dev_back_end/dev/internal/logic/payload.go`

6. **修正05数据降级写入路径**
   - 问题：降级路径中 `itemCount = dataLen / 2 = 0`，导致for循环不执行，无数据写入InfluxDB
   - 修复：改为直接以hex格式写入原始数据
   - 修改文件：`dev_back_end/dev/internal/logic/payload.go`

7. **清理死代码**
   - 移除 `Func04Request.DataCount` 字段（不再使用）
   - 修改文件：`dev_back_end/dev/internal/model/sendcod.go`、`controller/payload.go`

#### 前端修正

8. **修正Features.vue下发指令构建**
   - 问题：前端构建04指令时写入"数据组数"，实际应写入"报文总长度"
   - 修复：`totalLen = 3 + groups.length * 6`
   - 修复：清空配置从 `040000` 改为 `040003`（报文总长度=3）
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

### 功能新增

9. **新增离线检测机制**
   - 功能：后台每60秒检查所有设备，3分钟无更新自动设为离线
   - 新增文件：`dev_back_end/dev/internal/cmd/cmd.go` → `startOfflineDetection()`

## [1.7.0] - 2026-05-05

### 变量管理页面全面重构

#### 核心逻辑重构

1. **下发逻辑改为基于选中变量**
   - 改动：传 selectedRows（选中的变量）给 Features 组件，而不是所有变量
   - 影响：只有用户勾选的变量才会被下发
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

2. **实现 Payload Key 变化检测机制（方案B）**
   - 新增 getPayloadKey() 函数：计算选中变量的唯一标识（基于 id、站号、类型、地址、长度）
   - 新增 getLastPayloadKey() / savePayloadKey()：localStorage 读写
   - 新增 hasPayloadChanged 计算属性：比较当前 payload 与上次 payload
   - 新增 payloadRefreshTrigger 响应式变量：强制刷新 hasPayloadChanged
   - 优势：精确判断 payload 是否真的变化，不依赖后端 chengeFlag
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

3. **移除对后端 chengeFlag 的依赖**
   - 改动："有修改操作"提示改用 hasPayloadChanged 判断
   - 影响：变量名变化不会触发提示，地址/类型/长度变化才会
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

#### 空配置下发支持

4. **允许下发空配置**
   - 改动：移除按钮禁用条件中的 `selectedRows.length === 0`
   - 改动：空配置时提示文字改为"将下发空配置"
   - 改动：移除 Features 组件中的空配置检查
   - 改动：添加空配置时的友好提示（"将下发空配置，设备将停止采集所有变量"）
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`、`Features.vue`

5. **修复 build04FunctionCode 空配置处理**
   - 问题：之前空配置时返回空数组，导致模拟器没收到清除指令
   - 修复：即使空配置也生成有效的功能码04（0组）
   - 格式：`04 00 00`（功能码 + 0组）
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

#### 05上报数据包长度计算增强

6. **分组计算考虑变量实际占用长度**
   - 修复：getGroupDetails 函数现在会计算每个变量的 endAddr = startAddr + data_len - 1
   - 影响：分组范围从"最小地址"到"最大结束地址"，而不是"最大起始地址"
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

7. **分组详情显示**
   - 新增：显示每个分组的详细信息（类型、站号、地址范围、寄存器数量、数据字节数）
   - 新增：详细的计算过程展示（基础长度、每组头部+数据、总计）
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

#### UI 优化

8. **变量表格增加寄存器数量列**
   - 新增列：显示每个变量占用的寄存器/线圈数量
   - 友好显示：线圈显示"X 个线圈"，寄存器显示"X 个寄存器"
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

9. **分区列显示友好文字**
   - 改动：0→"线圈"，1→"离散输入"，3→"输入寄存器"，4→"保持寄存器"
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/variables.vue`

10. **数量列使用合适的单位**
    - 线圈/离散输入：显示 "X 位"
    - 输入/保持寄存器：显示 "X 个寄存器"
    - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

---

## [1.6.0] - 2026-05-05

### 空配置功能与数据管理页面显示优化

#### 后端修复

1. **修复SendDataConfig API的空配置验证问题**
   - 问题：SendDataConfigReq中的Entries字段有`v:"required#数据项不能为空"`验证规则，导致空配置请求被拒绝
   - 修复：移除了required验证规则，允许发送空配置
   - 修改文件：`dev_back_end/dev/api/dev/v1/payload.go`

#### 前端修复与增强

2. **增强Features.vue的空配置处理**
   - 添加了空配置时的二次确认弹窗，提示用户"确定要清空所有数据配置吗？设备将停止采集和上报数据"
   - 添加了console.log调试信息，便于排查问题
   - 在下发成功后保存activeVariableIds到localStorage
   - 修改文件：`4G_dev_front/4G_dev/src/components/variables/Features.vue`

3. **优化data.vue的变量显示逻辑**
   - 新增功能：数据管理页面默认只显示已下发配置的变量
   - 新增功能：下发空配置时显示"暂无数据"
   - 新增功能：可以勾选"显示所有变量"查看全部6个变量
   - 添加了localStorage读取和保存activeVariableIds的功能
   - 修改文件：`4G_dev_front/4G_dev/src/components/data/data.vue`

#### 模拟器修复

4. **修复config_manager.py的空配置处理**
   - 问题：clear_data_configs清空配置后没有触发回调，导致数据调度器不知道配置已变更
   - 修复：clear_data_configs现在会调用_on_data_config_updated回调
   - 修改文件：`simulator_v3/core/config_manager.py`

5. **优化data_config_handler.py的配置更新逻辑**
   - 统一使用update_data_configs处理配置更新
   - 确保每次下发新配置时，先清除旧配置再添加新配置（防止配置叠加）
   - 修改文件：`simulator_v3/protocol/data_config_handler.py`

#### 测试工具新增

6. **新增空配置测试脚本**
   - `test_empty_config.py`：直接通过MQTT发送空配置测试
   - `test_backend_empty_config.py`：通过后端API发送空配置测试

---

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
