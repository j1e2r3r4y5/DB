package logic

import (
	"context"
	"crypto/rand"
	"errors"
	"fmt"
	"time"

	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/glog"
	jwt "github.com/golang-jwt/jwt/v5"

	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"
)

type sToken struct {
}

func init() {
	// dao.Redis.Clear(context.TODO()) // 定期清理redis
	service.RegisterToken(Newtoken())
}

func Newtoken() *sToken {
	return &sToken{}
}

// GenToken 生成并返回token
func (s *sToken) GenToken(ctx context.Context, username string, expire time.Duration) (string, error) {
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.RegisteredClaims{
		Issuer:    "gdtzSLMDP",
		Subject:   username,
		IssuedAt:  jwt.NewNumericDate(time.Now()),
		NotBefore: jwt.NewNumericDate(time.Now()),
	})
	signingKey, err := s.generateRandomKey(32)
	if err != nil {
		g.Log().Error(ctx, "siginingKey gen error")
		return "", err
	}

	g.Log().Info(ctx, "token fine here")
	tokenString, err := token.SignedString(signingKey)
	s.AddToken(tokenString, &model.TokenInfo{
		SigningKey: signingKey,
		Username:   username,
	}, expire)
	if err != nil {
		glog.Error(ctx, "token generate error")
	}
	return tokenString, err
}

// generateRandomKey 随机生成密钥
func (s *sToken) generateRandomKey(length int) ([]byte, error) {
	key := make([]byte, length)
	_, err := rand.Read(key)
	if err != nil {
		return nil, err
	}
	return key, nil
}

// ValidateToken 验证token
func (s *sToken) ValidateToken(ctx context.Context, tokenString string) (bool, error) {
	// g.Log().Debug(ctx, "validating token", tokenString)
	ok := false
	signKey, err := s.GetSigningKey(tokenString)
	// g.Log().Debug(ctx, "got signing key", signKey)
	if err != nil {
		return false, err
	}
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		if token.Method.Alg() != "HS256" {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return signKey, nil
	})
	if err != nil {
		g.Log().Error(ctx, "token parse error")
		return false, err
	}
	if token.Valid {
		ok = true
	} else if errors.Is(err, jwt.ErrTokenExpired) {
		err = s.DelToken(tokenString)
		if err != nil {
			g.Log().Debug(ctx, "token清理失败")
		}
		ok = false
	}
	g.Log().Debug(ctx, "validation over")
	return ok, err
}

// AddToken 将生成的tokenStirng加入redis
func (s *sToken) AddToken(tokenString string, in *model.TokenInfo, expire time.Duration) error {
	err := dao.Redis.Set(context.Background(), in.Username, tokenString, expire)
	if err != nil {
		return err
	}
	err = dao.Redis.Set(context.Background(), tokenString, in.SigningKey, expire)
	if err != nil {
		return err
	}
	return nil
}

// GetSigningKey 获取token对应的签发密钥
func (s *sToken) GetSigningKey(tokenString string) ([]byte, error) {
	g.Log().Debug(context.Background(), "enter GetSigningKey")
	exist, err := dao.Redis.IsExist(context.Background(), tokenString)
	if err != nil {
		return nil, err
	}
	if !exist {
		return nil, gerror.New("token does not exist")
	}

	siginingKey, err := dao.Redis.Get(context.Background(), tokenString)

	if err != nil {
		return nil, err
	}
	return []byte(siginingKey.(string)), nil
}

// DelToken 删除缓存中的token
func (s *sToken) DelToken(tokenString string) error {
	username, err := s.GetUser(tokenString)
	if err != nil {
		return err
	}
	err = dao.Redis.Del(context.Background(), username, tokenString)
	if err != nil {
		return err
	}
	return nil
}

// GetUser 获取token中的用户名
func (s *sToken) GetUser(tokenString string) (username string, err error) {
	g.Log().Debug(context.Background(), "enter GetUser")
	signKey, err := s.GetSigningKey(tokenString)
	if err != nil {
		return "", err
	}

	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		if token.Method.Alg() != "HS256" {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return signKey, nil
	})
	if err != nil {
		return "", err
	}
	username, err = token.Claims.GetSubject()
	if err != nil {
		return "", err
	}
	return username, err
}

// RepeatLogin 处理重复登录
func (s *sToken) RepeatLogin(ctx context.Context, username string) error {
	g.Log().Debug(ctx, "enter CheckLogin")
	exist, err := dao.Redis.IsExist(context.Background(), username)
	if err != nil {
		return err
	}
	if !exist {
		return nil
	}
	oldTokenString, err := dao.Redis.Get(context.Background(), username)
	g.Log().Debug(ctx, "oldTokenString: ", oldTokenString)
	if err != nil {
		return err
	}
	err = dao.Redis.Del(context.Background(), username, oldTokenString)
	g.Log().Debug(ctx, "Del error?")
	if err != nil {
		return err
	}
	return nil
}

// NoRepeatLogin 不处理重复登录
func (s *sToken) NoRepeatLogin(ctx context.Context, username string) (string, error) {
	g.Log().Debug(ctx, "enter CheckLogin")
	exist, err := dao.Redis.IsExist(context.Background(), username)
	if err != nil {
		return "", err
	}
	if !exist {
		return "", nil
	}
	tokenString, err := dao.Redis.Get(context.Background(), username)
	g.Log().Debug(ctx, "TokenString: ", tokenString)
	if err != nil {
		return "", err
	}
	return tokenString.(string), nil
}
