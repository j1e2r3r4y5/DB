package v1

import (
	"dev/internal/model"

	"github.com/gogf/gf/v2/frame/g"
)

type User struct {
	g.Meta   `path:"/user" method:"post" summary:"用户列表" tags:"用户管理"`
	ID       int    `json:"id"`
	Username string `json:"username"`
	Password string `json:"password"`
	Nickname string `json:"nickname"`
	Type     int    `json:"type"` // 用户类型0:管理员,1:系统管理员,2:设备管理员，3:普通用户
}
type Userres struct {
	Users []*model.User `json:"users" dc:"用户列表"`
	Total int           `json:"total" dc:"总数"`
}
type RegisterReq struct {
	g.Meta   `path:"/register" method:"post"`
	Username string `json:"username"`
	Password string `json:"password"`
	Nickname string `json:"nickname"` // 用户昵称
	Type     int    `json:"type"`     // 用户类型0:超级管理员 1:系统管理2:设备管理员 3:普通用户
}
type RegisterRes struct {
}

type LoginReq struct {
	g.Meta   `path:"/login" method:"post"`
	Username string `json:"username"`
	Password string `json:"password"`
}
type LoginRes struct {
	Id       int    `json:"id"`
	Username string `json:"username"`
	Password string `json:"password"`
	Type     int    `json:"type"`  // 用户类型0:管理员 1:普通用户2:系统管理员
	Token    string `json:"token"` // 登录
}
type ModifyUserReq struct {
	g.Meta      `path:"/modifyuser" method:"post"`
	ID          int    `json:"id"`           // 用户ID
	OldPassword string `json:"old_password"` // 旧密码
	NewPassword string `json:"new_password"` // 新密码
}
type ModifyUserRes struct {
}
type Permuser struct {
	g.Meta          `path:"/Permuser" method:"post" summary:"用户列表" tags:"用户管理"`
	ID              int    `json:"id"`
	Username        string `json:"username"`
	Password        string `json:"password"`
	Nickname        string `json:"nickname"`
	Type            int    `json:"type"`              // 用户类型0:管理员,1:系统管理员,2:设备管理员，3:普通用户
	CurrentUserType int    `json:"current_user_type"` // 当前用户类型
}
type RemoveUser struct {
	g.Meta `path:"/remove-user" method:"post" summary:"删除用户" tags:"用户管理"`
	ID     []int `json:"id"` // 用户ID列表
}
type RemoveUserRes struct {
}
type ChangeUserInfo struct {
	g.Meta   `path:"/change-user" method:"post" summary:"修改用户信息" tags:"用户管理"`
	ID       int    `json:"id"`       // 用户ID
	Username string `json:"username"` // 用户名
	Nickname string `json:"nickname"` // 用户昵称
	Password string `json:"password"` // 用户密码
}
type ChangeUserInfoRes struct {
}
type LogoutDoReq struct {
	g.Meta `path:"/logout" method:"post" summary:"退出登录"`
}
type LogoutDoRes struct {
}
