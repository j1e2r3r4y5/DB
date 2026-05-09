package dao

import (
	"dev/internal/dao/internal"
)

type internalRedisDao = *internal.RedisDao

type redisDao struct {
	internalRedisDao
}

var (
	Redis = redisDao{
		internal.NewRedisDao(),
	}
)
