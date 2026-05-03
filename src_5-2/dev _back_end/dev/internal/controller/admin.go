package controller

import (
	"context"
	v1 "dev/api/dev/v1"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"
	"strings"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

var Admin = cAdmin{}

type cAdmin struct{}

func (c cAdmin) Login(ctx context.Context, req *v1.LoginReq) (res *v1.LoginRes, err error) {
	var user *model.User
	if req.Username == "" || req.Password == "" {
		g.Log().Error(ctx, "用户名或密码不能为空")
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "用户名或密码不能为空")
	}
	err = dao.User.Ctx(ctx).Where("username", req.Username).Scan(&user)
	if err != nil {
		g.Log().Error(ctx, "查询用户失败", err)
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "查询用户失败")
	}
	if user.Type == 0 {
		ok, out, err := service.User().AdminLogin(ctx, model.User{
			Username: req.Username,
			Password: req.Password,
		})
		if err != nil || !ok {
			return nil, gerror.NewCode(gcode.CodeInvalidParameter, "账号或密码错误3")
		}
		// 登录成功，组装返回
		res = &v1.LoginRes{
			Id:    user.ID,
			Type:  out.Type,
			Token: out.TokenString,
		}
	} else if user.Type != 0 {
		ok, out, err := service.User().UserLogin(ctx, model.User{
			Username: req.Username,
			Password: req.Password,
		})
		if err != nil || !ok {
			return nil, gerror.NewCode(gcode.CodeInvalidParameter, "账号或密码错误4")
		}
		// 登录成功，组装返回
		res = &v1.LoginRes{
			Id:    user.ID, // 新增
			Type:  out.Type,
			Token: out.TokenString,
		}
	}
	return res, nil
}
func (c cAdmin) Register(ctx context.Context, req *v1.RegisterReq) (res *v1.RegisterRes, err error) {
	if req.Username == "" || req.Password == "" {
		g.Log().Error(ctx, "用户名或密码不能为空")
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "用户名或密码不能为空")
	}
	err = service.User().Registeruser(ctx, &model.RegisterReq{
		Username: req.Username,
		Password: req.Password,
		Nickname: req.Nickname,
		Type:     req.Type, // 默认
	})
	g.Log().Info(ctx, "注册用户", req.Type, "成功", req.Username)
	if err != nil {
		g.Log().Error(ctx, "注册失败", err)
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "注册失败")
	}
	return
}
func (c cAdmin) GetUserList(ctx context.Context, req *v1.User) (res *v1.Userres, err error) {
	list, err := service.User().GetUserlist(ctx)
	if err != nil {
		g.Log().Error(ctx, "获取用户列表失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "获取用户列表失败")
	}
	res = &v1.Userres{
		Users: list,
		Total: len(list),
	}
	g.Log().Info(ctx, "获取用户列表成功", res.Users, "条记录")
	g.Log().Info(ctx, "获取用户列表成功", len(list), "条记录")
	return
}

func (c cAdmin) ModifyUser(ctx context.Context, req *v1.ModifyUserReq) (res *v1.ModifyUserRes, err error) {
	if req.ID <= 0 || req.OldPassword == "" || req.NewPassword == "" {
		g.Log().Error(ctx, "参数错误")
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "参数错误")
	}
	err = service.User().Modifyuser(ctx, req.ID, req.OldPassword, req.NewPassword)
	if err != nil {
		g.Log().Error(ctx, "修改用户密码失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "修改用户密码失败")
	}
	g.Log().Info(ctx, "修改用户密码成功", req.ID)
	return
}
func (c cAdmin) Permuser(ctx context.Context, req *v1.Permuser) (res *v1.ModifyUserRes, err error) {
	if req.ID <= 0 || req.Type < 0 {
		g.Log().Error(ctx, "参数错误")
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "参数错误")
	}
	err = service.User().Permuser(ctx, req.ID, req.Type, req.CurrentUserType)
	if err != nil {
		g.Log().Error(ctx, "修改用户权限失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "修改用户权限失败")
	}
	return nil, err
}
func (c cAdmin) RemoveUser(ctx context.Context, req *v1.RemoveUser) (res *v1.RemoveUserRes, err error) {
	if len(req.ID) == 0 {
		g.Log().Error(ctx, "用户ID列表不能为空", req.ID)
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "用户ID列表不能为空")
	}
	err = service.User().RemoveUser(ctx, model.RemoveList{Idlist: req.ID})
	if err != nil {
		g.Log().Error(ctx, "删除用户失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "删除用户失败")
	}
	g.Log().Info(ctx, "删除用户成功", req.ID)
	res = &v1.RemoveUserRes{}
	g.Log().Info(ctx, "删除用户成功", len(req.ID), "条记录")
	return
}
func (c cAdmin) ChangeUserInfo(ctx context.Context, req *v1.ChangeUserInfo) (res *v1.ChangeUserInfoRes, err error) {
	if req.ID <= 0 {
		g.Log().Error(ctx, "参数错误")
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "参数错误")
	}
	err = service.User().ChangeUserInfo(ctx, &model.ChangeUserInfo{
		ID:       req.ID,
		Username: req.Username,
		Nickname: req.Nickname,
		Password: req.Password,
	})
	if err != nil {
		g.Log().Error(ctx, "修改用户信息失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "修改用户信息失败")
	}
	g.Log().Info(ctx, "修改用户信息成功", req.ID)
	return
}

// 登出
func (c *cAdmin) Logout(ctx context.Context, req *v1.LogoutDoReq) (res *v1.LogoutDoRes, err error) {
	tokenString := g.RequestFromCtx(ctx).GetHeader("Authorization")
	tokenString = strings.TrimPrefix(tokenString, "Bearer ")
	err = service.User().Logout(ctx, model.UserLogoutInput{
		TokenString: tokenString,
	})
	if err != nil {
		return res, err
	}
	g.Log().Info(ctx, "logout success")
	return
}
