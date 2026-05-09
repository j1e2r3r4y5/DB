package model

type User struct {
	ID       int `json:"id" gorm:"primaryKey;autoIncrement;comment:用户ID"`
	Username string
	Password string
	Nickname string
	Type     int // 用户类型0:管理员 1:普通用户2:访客
}
type RegisterReq struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Nickname string `json:"nickname"`
	Type     int    `json:"type"` // 用户类型0:管理员 1:普通用户2:访客
}
type LoginUser struct {
	Username string `json:"username"`
	Password string `json:"password"`
}
type RemoveList struct {
	Idlist []int `json:"idlist"` //用户ID列表
}
type ChangeUserInfo struct {
	ID       int    `json:"id"`       // 用户ID
	Username string `json:"username"` // 用户名
	Nickname string `json:"nickname"` // 用户昵称
	Password string `json:"password"` // 用户密码
}
type TokenInfo struct {
	SigningKey []byte
	Username   string // 平台登录用户名
}
type UserLoginOutput struct {
	Type        int    `json:"userType" dc:"0管理员1普通用户"`
	TokenString string `json:"token" dc:"jwt token"`
}
type UserLogoutInput struct {
	TokenString string `json:"tokon" dc:"jwt token"`
}
