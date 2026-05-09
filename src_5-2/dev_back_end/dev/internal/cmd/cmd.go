package cmd

import (
	"context"
	"dev/internal/controller"
	"dev/internal/dao"
	"dev/internal/service"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/gcmd"
	"github.com/gogf/gf/v2/os/gtime"
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
				group.Bind(controller.Variable)
			group.Bind(controller.Payload) // 绑定整个 Payload 控制器，包含所有接口！
				group.Middleware(service.Middleware().AdminMiddleware)
				group.Bind(controller.Dvice.AddDevice)
				group.Bind(controller.Dvice.ModifyDevice)
				group.Bind(controller.Dvice.RemoveDevice)
				group.Bind(controller.Admin.GetUserList)
				group.Bind(controller.Admin.ModifyUser)
				group.Bind(controller.Admin.ChangeUserInfo)
				group.Bind(controller.Admin.RemoveUser)
				group.Bind(controller.Admin.Permuser)
				group.Bind(controller.Admin.Register)
			})
			service.Mqtt().Init() // 初始化 MQTT 客户端
			go startOfflineDetection() // 启动离线检测定时任务
			s.Run()
			return nil
		},
	}
)

func startOfflineDetection() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		ctx := context.Background()
		threshold := gtime.Now().Add(-3 * time.Minute)

		_, err := dao.Dev.Ctx(ctx).Where("dev_status = 1 AND latest_online < ?", threshold).Data(g.Map{"dev_status": 0}).Update()
		if err != nil {
			g.Log().Error(ctx, "离线检测更新失败", err)
		}
	}
}
