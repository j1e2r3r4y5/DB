package cmd

import (
	"context"
	"dev/internal/controller"
	"dev/internal/service"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/gcmd"
)

var (
	Main = gcmd.Command{
		Name:  "main",
		Usage: "main",
		Brief: "start http server",
		Func: func(ctx context.Context, parser *gcmd.Parser) (err error) {
			s := g.Server()
			s.Use(func(r *ghttp.Request) {
				r.Response.CORSDefault()
				r.Middleware.Next()
			})
			s.Group("/", func(group *ghttp.RouterGroup) {
				group.Middleware(service.Middleware().MiddlewareCORS)
				group.Middleware(service.Middleware().ResponseHandler)
				group.Bind(controller.Admin.Login)
				group.Bind(controller.Admin.Logout)
				group.Middleware(service.Middleware().Auth)
				group.Middleware(service.Middleware().Ctx)
				group.Bind(controller.Dvice.GetDevice)
				group.Bind(controller.Data.GetData)
				group.Bind(controller.Payload.QueryallData)
				group.Bind(controller.Variable)
				group.Middleware(service.Middleware().AdminMiddleware)
				group.Bind(controller.Dvice.AddDevice)
				group.Bind(controller.Dvice.ModifyDevice)
				group.Bind(controller.Dvice.RemoveDevice)
				group.Bind(controller.Payload.DownPayload)
				group.Bind(controller.Payload.QueryBatchDataItemFromInflux)
				group.Bind(controller.Payload.QueryDevStatusFromInflux)
				group.Bind(controller.Admin.GetUserList)
				group.Bind(controller.Admin.ModifyUser)
				group.Bind(controller.Admin.ChangeUserInfo)
				group.Bind(controller.Admin.RemoveUser)
				group.Bind(controller.Admin.Permuser)
				group.Bind(controller.Admin.Register)
			})
			service.Mqtt().Init() // 初始化 MQTT 客户端
			s.Run()
			return nil
		},
	}
)
