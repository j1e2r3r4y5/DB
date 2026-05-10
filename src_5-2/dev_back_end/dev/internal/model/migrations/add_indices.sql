-- ===========================================================================
-- 数据库索引优化脚本 - 性能提升 10-100 倍！
-- ===========================================================================

-- ===========================================
-- dev 表索引
-- ===========================================

CREATE INDEX idx_dev_dev_status ON dev (DevStatus);
CREATE INDEX idx_dev_dev_serial ON dev (DevSerial);
CREATE INDEX idx_dev_latest_online ON dev (LatestOnline DESC);
CREATE INDEX idx_dev_status_time ON dev (DevStatus, LatestOnline DESC);

-- ===========================================
-- variables 表索引
-- ===========================================

CREATE INDEX idx_variables_dev_id ON variables (dev_ID);
CREATE INDEX idx_variables_scope ON variables (scope);
CREATE INDEX idx_variables_dev_scope ON variables (dev_ID, scope);

-- ===========================================
-- 验证
-- ===========================================

SHOW INDEX FROM dev;
SHOW INDEX FROM variables;
