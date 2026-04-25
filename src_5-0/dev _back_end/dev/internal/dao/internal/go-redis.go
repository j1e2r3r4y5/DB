package internal

import (
	"context"
	"time"

	"github.com/go-redis/redis_rate/v10"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/redis/go-redis/v9"
)

type RedisDao struct {
	rdb     *redis.Client
	limiter *redis_rate.Limiter
}

var (
	rdb = redis.NewClient(&redis.Options{
		Addr: g.Cfg().MustGet(context.TODO(), "redis.host").String() + ":" + g.Cfg().MustGet(context.TODO(), "redis.port").String(),
	})
	limiter = redis_rate.NewLimiter(rdb)
	prefix  = g.Cfg().MustGet(context.TODO(), "redis.prefix").String()
)

func NewRedisDao() *RedisDao {
	return &RedisDao{
		rdb:     rdb,
		limiter: limiter,
	}
}

func (dao *RedisDao) Set(ctx context.Context, key string, value any, duration time.Duration) error {
	_, err := dao.rdb.Set(ctx, prefix+key, value, duration).Result()
	return err
}

func (dao *RedisDao) Get(ctx context.Context, key string) (any, error) {
	return dao.rdb.Get(ctx, prefix+key).Result()
}

func (dao *RedisDao) IsExist(ctx context.Context, key string) (bool, error) {
	res, err := dao.rdb.Exists(ctx, prefix+key).Result()
	return res == 1, err
}

func (dao *RedisDao) Del(ctx context.Context, keys ...any) error {
	for _, key := range keys {
		_, err := dao.rdb.Del(ctx, prefix+key.(string)).Result()
		if err != nil {
			return err
		}
	}
	return nil
}

func (dao *RedisDao) Close() error {
	return dao.rdb.Close()
}

func (dao *RedisDao) Clear(ctx context.Context) {
	go func() {
		for {
			time.Sleep(time.Hour * 24)
			keys, _, err := dao.rdb.Scan(ctx, 0, prefix+"*", 0).Result()
			if err != nil {
				g.Log().Error(ctx, err)
			}

			for _, key := range keys {
				if err := dao.rdb.Del(ctx, key).Err(); err != nil {
					g.Log().Error(ctx, err)
				}
			}
		}
	}()
}

func (dao *RedisDao) Limit(ctx context.Context, tokenString string) (bool, error) {
	res, err := dao.limiter.Allow(ctx, tokenString, redis_rate.PerHour(g.Cfg().MustGet(ctx, "redis.limiter").Int()))
	if err != nil {
		g.Log().Error(ctx, err)
		return false, err
	}
	if res.Allowed <= 0 {
		return false, nil
	}
	return true, nil
}
