// ================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// You can delete these comments if you wish manually maintain this interface file.
// ================================================================================

package service

import (
	"context"
	"dev/internal/model"
	"time"
)

type (
	IToken interface {
		// GenToken 生成并返回token
		GenToken(ctx context.Context, username string, expire time.Duration) (string, error)
		// ValidateToken 验证token
		ValidateToken(ctx context.Context, tokenString string) (bool, error)
		// AddToken 将生成的tokenStirng加入redis
		AddToken(tokenString string, in *model.TokenInfo, expire time.Duration) error
		// GetSigningKey 获取token对应的签发密钥
		GetSigningKey(tokenString string) ([]byte, error)
		// DelToken 删除缓存中的token
		DelToken(tokenString string) error
		// GetUser 获取token中的用户名
		GetUser(tokenString string) (username string, err error)
		// RepeatLogin 处理重复登录
		RepeatLogin(ctx context.Context, username string) error
		// NoRepeatLogin 不处理重复登录
		NoRepeatLogin(ctx context.Context, username string) (string, error)
	}
)

var (
	localToken IToken
)

func Token() IToken {
	if localToken == nil {
		panic("implement not found for interface IToken, forgot register?")
	}
	return localToken
}

func RegisterToken(i IToken) {
	localToken = i
}
