package controller

import (
	"context"
	v1 "dev/api/dev/v1"
	"dev/internal/service"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

var Data = cData{}

type cData struct{}

func (c cData) GetData(ctx context.Context, req *v1.Datareq) (res *v1.Datares, err error) {
	list, err := service.Data().GetData(ctx)
	if err != nil {
		g.Log().Error(ctx, "获取数据视图失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "获取数据视图失败")
	}
	g.Log().Info(ctx, "获取数据视图成功", list)
	res = &v1.Datares{
		Datalist: list,
		Total:    len(list),
	}
	return res, nil
}
