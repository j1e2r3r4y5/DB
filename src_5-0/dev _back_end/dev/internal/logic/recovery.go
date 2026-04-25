package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/frame/g"
)

type srecove struct {
}

func init() {
	service.Registerecove(Newre())
}

func Newre() *srecove {
	return &srecove{}
}

// 下发成功后用新保存的数据插入缓存表
func (s *srecove) InsertRecord(ctx context.Context, in *model.Variables) (err error) {
	g.Log().Info(ctx, "下发成功备份变量变量表", in)
	_, err = dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, in.DevID).Data(in).Delete()
	if err != nil {
		g.Log().Error(ctx, "删除缓存表成功", err)
	}
	_, err = dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, in.DevID).Data(in).Update()
	if err != nil {
		g.Log().Error(ctx, "下发成功备份变量表失败", err)
		return err
	}
	return
}

// 回溯功能
func (s *srecove) RecoveryVariable(ctx context.Context, devID int) error {
	// 1. 删除变量表中该设备的所有变量
	_, err := dao.Variables.Ctx(ctx).Where(dao.Variables.Columns().DevID, devID).Delete()
	if err != nil {
		g.Log().Error(ctx, "删除变量表失败", err)
		return err
	}

	// 2. 查询缓存表中该设备的所有变量
	var cacheVars []*model.Variables
	err = dao.Caching.Ctx(ctx).Where(dao.Caching.Columns().DevID, devID).Scan(&cacheVars)
	if err != nil {
		g.Log().Error(ctx, "查询缓存表失败", err)
		return err
	}
	if len(cacheVars) == 0 {
		g.Log().Warning(ctx, "缓存表无此设备变量，无法回溯", devID)
		return nil
	}

	// 3. 批量插入到变量表
	_, err = dao.Variables.Ctx(ctx).Data(cacheVars).Insert()
	if err != nil {
		g.Log().Error(ctx, "插入变量表失败", err)
		return err
	}
	g.Log().Info(ctx, "变量表已用缓存表内容回溯", devID)
	_, err = dao.Dev.Ctx(ctx).Where(dao.Dev.Columns().Id, devID).Data(g.Map{
		"Changeflag": 0,
	}).Update()
	if err != nil {
		g.Log().Error(ctx, "更新设备标志失败", err)
	}
	return nil
}
