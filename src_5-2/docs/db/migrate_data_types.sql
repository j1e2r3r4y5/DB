-- 数据类型迁移脚本
-- 将旧数据类型迁移为新格式
-- 旧 -> 新映射:
-- 1 (整数) -> 1 (int16)
-- 2 (浮点数) -> 3 (float32)
-- 3 (定点数) -> 3 (float32)
-- 4 (字符串) -> 5 (string)

-- 1. 查询当前的数据类型分布
SELECT 
    data_type,
    COUNT(*) as count
FROM variables
GROUP BY data_type
ORDER BY data_type;

-- 2. 执行数据迁移
UPDATE variables 
SET data_type = CASE
    WHEN data_type = '1' THEN '1'  -- 整数 -> int16 (保持不变，但为了一致性)
    WHEN data_type = '2' THEN '3'  -- 浮点数 -> float32
    WHEN data_type = '3' THEN '3'  -- 定点数 -> float32
    WHEN data_type = '4' THEN '5'  -- 字符串 -> string
    ELSE data_type  -- 不改变其他值
END
WHERE data_type IN ('1', '2', '3', '4');

-- 3. 同步更新缓存表（如果有）
UPDATE caching 
SET data_type = CASE
    WHEN data_type = '1' THEN '1'  -- 整数 -> int16
    WHEN data_type = '2' THEN '3'  -- 浮点数 -> float32
    WHEN data_type = '3' THEN '3'  -- 定点数 -> float32
    WHEN data_type = '4' THEN '5'  -- 字符串 -> string
    ELSE data_type
END
WHERE data_type IN ('1', '2', '3', '4');

-- 4. 验证迁移结果
SELECT 
    data_type,
    COUNT(*) as count
FROM variables
GROUP BY data_type
ORDER BY data_type;

-- 5. 更新设备变更标志，触发重新下发
UPDATE dev SET chengeFlag = 1 WHERE id IN (
    SELECT DISTINCT dev_id FROM variables
);
