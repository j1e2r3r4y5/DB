package cmd

import (
	"context"
	"dev/internal/controller"
	"dev/internal/dao"
	"dev/internal/logic/monitor"
	"dev/internal/model/entity"
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

			// 注册监控端点（不需要认证）
			s.BindHandler("GET:/health", controller.Monitor.Health)
			s.BindHandler("GET:/metrics", controller.Monitor.Metrics)
			s.BindHandler("GET:/stats", controller.Monitor.Stats)

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
			go updateDeviceMetrics() // 启动设备指标更新定时任务
			s.Run()
			return nil
		},
	}
)

// updateDeviceMetrics 更新设备在线指标
func updateDeviceMetrics() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		ctx := context.Background()

		onlineCount, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevStatus, "1").Count()
		if err != nil {
			g.Log().Warning(ctx, "Failed to count online devices", err)
			continue
		}
		offlineCount, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevStatus, "0").Count()
		if err != nil {
			g.Log().Warning(ctx, "Failed to count offline devices", err)
			continue
		}

		monitor.GetMetrics().SetDeviceStatus(int64(onlineCount), int64(offlineCount))
	}
}

func startOfflineDetection() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		ctx := context.Background()
		threshold := gtime.Now().Add(-3 * time.Minute)

		var devices []*entity.Dev
		err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevStatus+" = 1 AND "+dao.Dev.Columns().LatestOnline+" < ?", threshold).Scan(&devices)
		if err != nil {
			g.Log().Error(ctx, "查询离线设备失败", err)
			continue
		}

		for _, dev := range devices {
			monitor.AlertDeviceOffline(
				ctx,
				dev.DevSerial,
				dev.Devname,
				dev.DevLocation,
				dev.LatestOnline,
			)
		}

		if len(devices) > 0 {
			_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().DevStatus+" = 1 AND "+dao.Dev.Columns().LatestOnline+" < ?", threshold).Data(g.Map{dao.Dev.Columns().DevStatus: "0"}).Update()
			if err != nil {
				g.Log().Error(ctx, "更新离线设备状态失败", err)
			} else {
				g.Log().Info(ctx, "设备离线检测完成", "count", len(devices))
			}
		}
	}
}
