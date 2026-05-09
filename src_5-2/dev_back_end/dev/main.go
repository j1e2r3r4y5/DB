package main

import (
	"context"
	"dev/internal/cmd"
	"dev/internal/dao"
	_ "dev/internal/packed"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gtime"
	_ "github.com/influxdata/influxdb-client-go/v2/api/write"

	_ "dev/internal/logic"

	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"
)

func main() {
	go func() {
		ticker := time.NewTicker(time.Minute / 2)
		defer ticker.Stop()
		for {
			<-ticker.C
			ctx := context.Background()
			g.Log().Info(ctx, "开始执行定时离线检查")
			rowsAffected, err := dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().LatestOnline + " < ?", gtime.Now().Add(-5 * time.Minute)).Data(g.Map{dao.Dev.Columns().DevStatus: 0}).Update()
			g.Log().Info(ctx, "批量设备离线执行完成", "影响行数", rowsAffected, "错误", err)
			if err != nil {
				g.Log().Error(ctx, "批量设备离线失败", err)
			}
		}
	}()
	// token := os.Getenv("INFLUXDB_TOKEN")
	// url := "http://172.12.0.219:8086"
	// client := influxdb2.NewClient(url, token)
	// defer client.Close()
	// service.Device().GetDevicelist(gctx.GetInitCtx())
	// service.Data().GetData(gctx.GetInitCtx())
	cmd.Main.Run(gctx.GetInitCtx())
}
