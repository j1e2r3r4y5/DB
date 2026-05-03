package main

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"fmt"

	"github.com/gogf/gf/v2/frame/g"
	_ "github.com/gogf/gf/v2/os/gctx"
)

func main() {
	ctx := context.Background()
	
	devId := 28 // 设备A1B2C3D4的ID
	
	_, err := dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devId).Delete()
	if err != nil {
		g.Log().Error(ctx, "清空旧缓存失败", err)
	}
	
	var variableList []*model.Variables
	err = dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, devId).Scan(&variableList)
	if err != nil {
		g.Log().Error(ctx, "获取变量列表失败", err)
		return
	}
	
	savedCount := 0
	for _, v := range variableList {
		_, err := dao.Caching.Ctx(ctx).Data(v).Save()
		if err != nil {
			g.Log().Error(ctx, "写入缓存表失败", "varName", v.VarName, err)
		} else {
			savedCount++
		}
	}
	
	g.Log().Info(ctx, "变量配置同步到缓存成功", "totalVars", len(variableList), "savedVars", savedCount)
	fmt.Println("完成！")
}