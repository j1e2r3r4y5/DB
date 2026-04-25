package service

import (
	"context"
	"dev/internal/model"
	"dev/internal/model/entity"
)

type Iuser interface {
	AdminLogin(ctx context.Context, in model.User) (ok bool, out *model.UserLoginOutput, err error)
	UserLogin(ctx context.Context, in model.User) (ok bool, out *model.UserLoginOutput, err error)
	Registeruser(ctx context.Context, req *model.RegisterReq) error
	GetUserlist(ctx context.Context) (list []*model.User, err error)
	Modifyuser(ctx context.Context, ID int, oldpawssord string, newpawssord string) error
	Permuser(ctx context.Context, ID int, Type int, currentUserType int) error
	RemoveUser(ctx context.Context, ID model.RemoveList) error
	ChangeUserInfo(ctx context.Context, user *model.ChangeUserInfo) error
	GetUserInfo(ctx context.Context, tokenString string) (out *entity.User, err error)
	Logout(ctx context.Context, in model.UserLogoutInput) error
}

var logicuser Iuser

func User() Iuser {
	if logicuser == nil {
		panic("implement not found for interface Iuser, forgot register?")
	}
	return logicuser
}
func Registeruser(i Iuser) {
	logicuser = i
}
