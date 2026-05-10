package logic

import (
	"context"
	"encoding/json"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/util/gconv"
)

// 缓存键前缀
const (
	cachePrefixDevice       = "device:"
	cachePrefixDeviceSerial = "device:serial:"
	cachePrefixVariables    = "variables:device:"
	cacheTTL                = 5 * time.Minute
)

// CacheStats 缓存统计
type CacheStats struct {
	Hits   int64
	Misses int64
	Errors int64
}

var cacheStats = &CacheStats{}

// GetCacheStats 获取缓存统计
func GetCacheStats() *CacheStats {
	return cacheStats
}

// getFromCache 从缓存获取数据
func getFromCache(ctx context.Context, key string, target interface{}) bool {
	cached, err := g.Redis().Get(ctx, key)
	if err != nil {
		cacheStats.Errors++
		g.Log().Debug(ctx, "从缓存获取失败", key, err)
		return false
	}
	if cached.IsEmpty() {
		cacheStats.Misses++
		return false
	}
	err = json.Unmarshal(cached.Bytes(), target)
	if err != nil {
		cacheStats.Errors++
		g.Log().Debug(ctx, "缓存反序列化失败", key, err)
		return false
	}
	cacheStats.Hits++
	g.Log().Debug(ctx, "缓存命中", key)
	return true
}

// setToCache 设置缓存
func setToCache(ctx context.Context, key string, data interface{}, ttl time.Duration) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		cacheStats.Errors++
		g.Log().Debug(ctx, "缓存序列化失败", key, err)
		return
	}
	err = g.Redis().SetEX(ctx, key, jsonData, int64(ttl.Seconds()))
	if err != nil {
		cacheStats.Errors++
		g.Log().Debug(ctx, "设置缓存失败", key, err)
	}
}

// invalidateCache 清除缓存
func invalidateCache(ctx context.Context, pattern string) {
	keys, err := g.Redis().Keys(ctx, pattern)
	if err != nil {
		g.Log().Debug(ctx, "清除缓存失败", pattern, err)
		return
	}
	if len(keys) > 0 {
		_, err = g.Redis().Del(ctx, keys...)
		if err != nil {
			g.Log().Debug(ctx, "删除缓存键失败", err)
		}
	}
}

// DeviceCacheKey 获取设备缓存键
func DeviceCacheKey(deviceID int64) string {
	return cachePrefixDevice + gconv.String(deviceID)
}

// DeviceSerialCacheKey 获取设备序列号缓存键
func DeviceSerialCacheKey(serial string) string {
	return cachePrefixDeviceSerial + serial
}

// VariablesCacheKey 获取变量缓存键
func VariablesCacheKey(deviceID int64) string {
	return cachePrefixVariables + gconv.String(deviceID)
}

// InvalidateDeviceCache 清除设备相关缓存
func InvalidateDeviceCache(ctx context.Context, deviceID int64, serial string) {
	invalidateCache(ctx, DeviceCacheKey(deviceID))
	if serial != "" {
		invalidateCache(ctx, DeviceSerialCacheKey(serial))
	}
	invalidateCache(ctx, VariablesCacheKey(deviceID))
}
