package model

import "github.com/gogf/gf/v2/frame/g"

// Context 请求上下文结构
type Context struct {
	User *ContextUser // 上下文用户信息
	Data g.Map        // 自定KV变量，业务模块根据需要设置，不固定
}

// ContextUser 请求上下文中的用户信息
type ContextUser struct {
	Id   int // 用户Id
	Type int // 0-管理员，1-记录查看员，2-设备管理员，3-检测员，4-报告审核员，5-报告批准员
}
