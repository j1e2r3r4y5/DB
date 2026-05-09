// ================================================================================
// Code generated and maintained by GoFrame CLI tool. DO NOT EDIT.
// You can delete these comments if you wish manually maintain this interface file.
// ================================================================================

package service

import "github.com/gogf/gf/v2/net/ghttp"

type (
	IMiddleware interface {
		// 流量控制
		RateLimitMiddleware(r *ghttp.Request)
		// 前台系统权限控制，用户必须登录才能访问
		Auth(r *ghttp.Request)
		// 自定义上下文对象
		Ctx(r *ghttp.Request)
		// 跨域中间件
		MiddlewareCORS(r *ghttp.Request)
		// 管理权限检查
		AdminMiddleware(r *ghttp.Request)
		// 0, 3, 6, 8类用户权限检查
		// CheckerAndCertificaterMiddleware(r *ghttp.Request)
		// 0, 1, 2, 3, 6, 7, 8类型用户权限检查
		// DeviceUserMiddleware(r *ghttp.Request)
		// gf一般中间件，不设置则无法正确响应
		ResponseHandler(r *ghttp.Request)
		// 打印请求原文
		PrintRequest(r *ghttp.Request)
		// 检验外部接口开关是否开启
		// ExternalInterfaceSwitch(r *ghttp.Request)
	}
)

var (
	localMiddleware IMiddleware
)

func Middleware() IMiddleware {
	if localMiddleware == nil {
		panic("implement not found for interface IMiddleware, forgot register?")
	}
	return localMiddleware
}

func RegisterMiddleware(i IMiddleware) {
	localMiddleware = i
}
