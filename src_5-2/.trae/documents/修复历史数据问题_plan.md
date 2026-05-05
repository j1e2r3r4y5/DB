
# 修复历史数据问题计划

## 问题分析

### 当前问题
1. **时间顺序不正确**：`QueryallData` 函数使用 map 存储时间记录，map 遍历是无序的
2. **数据数量过多**：当前 limit 设置为 500 条，用户只需要 60 条

### 问题代码位置
`c:\Users\JERRY\Desktop\gp\src_5-2\dev _back_end\dev\internal\controller\payload.go` 中的 `QueryallData` 函数

## 修改方案

### 修改内容
1. **调整数据数量**：将 InfluxDB 查询的 `limit(n:500)` 改为 `limit(n:60)`
2. **修复时间排序**：
   - 收集所有时间记录的原始 time.Time 对象
   - 按时间升序排序（从旧到新）
   - 按排序后的时间顺序构建结果数组

## 文件修改

| 文件名 | 操作 |
| --- | --- |
| `c:\Users\JERRY\Desktop\gp\src_5-2\dev _back_end\dev\internal\controller\payload.go` | 修改 `QueryallData` 函数 |

## 验证步骤
1. 修改后重新编译并启动后端
2. 打开前端页面，点击任意变量的历史数据
3. 检查：
   - 是否只显示60条数据
   - 时间顺序是否正确（从旧到新）
