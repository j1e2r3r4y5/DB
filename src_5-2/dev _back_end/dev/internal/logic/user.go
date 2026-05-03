package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/model/do"
	"dev/internal/model/entity"
	"dev/internal/service"
	"errors"
	"fmt"
	"time"

	"github.com/gogf/gf/v2/crypto/gmd5"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

type sUser struct{}

func init() {
	service.Registeruser(NewUser())
}

func NewUser() *sUser {
	return &sUser{}
}
func (s *sUser) Registeruser(ctx context.Context, req *model.RegisterReq) error {
	// 这里可以添加用户注册的逻辑
	dao.User.Ctx(ctx).Where("username", req.Username).Count()
	if err := s.checkUsername(ctx, req.Username); err != nil {
		return err
	}
	// 比如验证用户名是否已存在，密码加密等
	_, err := dao.User.Ctx(ctx).Data(do.User{
		Username: req.Username,
		Password: s.MD5Password(req.Password),
		Nickname: req.Nickname,
		Type:     req.Type, // 默认普通用户
	}).Insert()
	if err != nil {
		return err

	}
	return nil
}

func (s *sUser) AdminLogin(ctx context.Context, in model.User) (ok bool, out *model.UserLoginOutput, err error) {
	var one *model.User
	err = dao.User.Ctx(ctx).Where("username", in.Username).Scan(&one)
	if err != nil || one == nil || one.Password != s.MD5Password(in.Password) {
		return false, out, gerror.New("账号或密码错误1")
	}
	err = service.Token().RepeatLogin(ctx, in.Username)
	if err != nil {
		return false, nil, err
	}
	tokenString, err := service.Token().GenToken(ctx, in.Username, time.Hour*24) // 生成token，设置有效期为30秒
	if err != nil {
		g.Log().Error(ctx, "创建token失败", err)
		return false, nil, gerror.New("创建token失败")
	}
	if tokenString != "" {
		out = &model.UserLoginOutput{
			Type:        one.Type,
			TokenString: tokenString,
		}
	}
	return true, out, nil
}
func (s *sUser) UserLogin(ctx context.Context, in model.User) (ok bool, out *model.UserLoginOutput, err error) {
	var one *model.User
	err = dao.User.Ctx(ctx).Where("username", in.Username).Scan(&one)
	if err != nil || one == nil || one.Password != s.MD5Password(in.Password) {
		return false, out, gerror.New("账号或密码错误2")
	}

	tokenString, err := service.Token().NoRepeatLogin(ctx, in.Username)
	if err != nil {
		return false, nil, gerror.New("repeat check error")
	}
	if tokenString != "" {
		out = &model.UserLoginOutput{
			Type:        one.Type,
			TokenString: tokenString,
		}
	}
	tokenString, err = service.Token().GenToken(ctx, in.Username, time.Hour*24) // 单位：小时
	if err != nil {
		g.Log().Info(ctx, "no token")
		return false, nil, gerror.New("token generate error")
	}
	g.Log().Info(ctx, "this is the tokenString: %s", tokenString)
	// 前端可以获得用户类型
	out = &model.UserLoginOutput{
		Type:        one.Type,
		TokenString: tokenString,
	}
	return true, out, nil
}

func (s *sUser) checkUsername(ctx context.Context, Username string) error {
	count, err := dao.User.Ctx(ctx).Where("Username", Username).Count()
	if err != nil {
		return err
	}
	if count > 0 {
		return errors.New("ID已存在")
	}
	return nil
}
func (s *sUser) MD5Password(password string) string {
	return gmd5.MustEncryptString(password)
}
func (s *sUser) GetUserlist(ctx context.Context) (list []*model.User, err error) {
	g.Log().Info(ctx, "获取用户列表")
	err = dao.User.Ctx(ctx).Scan(&list)
	if err != nil {
		g.Log().Error(ctx, "获取用户列表失败", err)
	}
	// return nil, gerror.New("获取用户列表功能未实现")
	return list, nil
}
func (s *sUser) Modifyuser(ctx context.Context, ID int, oldpawssord string, newpawssord string) error {
	var user *model.User
	err := dao.User.Ctx(ctx).Where("id", ID).Scan(&user)
	if err != nil {
		return gerror.New("用户不存在")
	}
	if s.MD5Password(oldpawssord) != user.Password {
		return gerror.New("旧密码错误")
	} else {
		// 更新密码
		_, err = dao.User.Ctx(ctx).Where("id", ID).Data(do.User{
			Password: s.MD5Password(newpawssord),
		}).Update()
		if err != nil {
			return gerror.New("修改密码失败")
		}
		g.Log().Info(ctx, "修改密码成功")
		return nil
	}
}
func (s *sUser) Permuser(ctx context.Context, ID int, Type int, currentUserType int) error {
	var user *model.User
	err := dao.User.Ctx(ctx).Where("id", ID).Scan(&user)
	if err != nil {
		return gerror.New("用户不存在")
	}
	if currentUserType != 0 && currentUserType != 1 { // 如果是管理员
		fmt.Println("当前用户权限", currentUserType)
		return gerror.New("非管理员不能修改权限")
	}
	// 更新权限
	_, err = dao.User.Ctx(ctx).Where("id", ID).Data(do.User{
		Type: Type, // 设置类型
	}).Update()
	if err != nil {
		return gerror.New("修改权限失败")
	}
	g.Log().Info(ctx, "修改权限成功")
	return nil
}

// Deldeteuser 删除多个用户
func (s *sUser) RemoveUser(ctx context.Context, ID model.RemoveList) error {
	if len(ID.Idlist) == 0 {
		g.Log().Error(ctx, "用户ID列表不能为空", ID.Idlist)
		return gerror.New("用户ID列表不能为空")
	}
	_, err := dao.User.Ctx(ctx).WhereIn(dao.User.Columns().Id, ID.Idlist).Delete()
	if err != nil {
		g.Log().Error(ctx, "删除设备失败")
	}
	g.Log().Info(ctx, "删除设备成功")
	return err
}

// 修改用户信息
func (s *sUser) ChangeUserInfo(ctx context.Context, user *model.ChangeUserInfo) error {
	if user.ID <= 0 {
		return gerror.New("用户ID不能为空")
	}
	updateData := g.Map{}
	if user.Username != "" {
		updateData["username"] = user.Username
	}
	if user.Password != "" {
		updateData["password"] = s.MD5Password(user.Password)
	}
	if user.Nickname != "" {
		updateData["nickname"] = user.Nickname
	}
	if len(updateData) == 0 {
		return gerror.New("没有需要修改的内容")
	}
	_, err := dao.User.Ctx(ctx).Where("id", user.ID).Data(updateData).Update()
	if err != nil {
		g.Log().Error(ctx, "修改用户信息失败", err)
		return gerror.New("修改用户信息失败")
	}
	g.Log().Info(ctx, "修改用户信息成功", user.ID)
	return nil
}

// GetUserInfo 获取用户信息
func (s *sUser) GetUserInfo(ctx context.Context, tokenString string) (out *entity.User, err error) {
	user, err := service.Token().GetUser(tokenString)
	g.Log().Info(ctx, "user get?", user)
	if err != nil {
		return nil, err
	}
	var userEntity *entity.User
	if err = dao.User.Ctx(ctx).Where(g.Map{
		dao.User.Columns().Username: user,
	}).Scan(&userEntity); err != nil {
		g.Log().Error(ctx, "Scan failed!!")
		return nil, err
	}
	if userEntity == nil {
		g.Log().Error(ctx, "no out? why?")
		return nil, gerror.New("不存在该用户")
	}
	return userEntity, nil
}

// Logout 注销登录
func (s *sUser) Logout(ctx context.Context, in model.UserLogoutInput) error {
	err := service.Token().DelToken(in.TokenString)
	if err != nil {
		g.Log().Error(ctx, "internal Logout error")
		return err
	}
	return nil
}
