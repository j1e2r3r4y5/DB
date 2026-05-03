package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/frame/g"
)

type sData struct {
}

func init() {
	service.RegisterData(NewData())
}

func NewData() *sData {
	return &sData{}
}

// 获取整个数据视图
func (s *sData) GetData(ctx context.Context) (res []*model.Data, err error) {
	g.Log().Info(ctx, "获取数据视图")
	err = dao.Data.Ctx(ctx).Scan(&res)
	if err != nil {
		g.Log().Info(ctx, "获取数据视图失败", err)
		return nil, err
	}
	g.Log().Info(ctx, "获取数据视图成功", res)
	return res, nil
}
