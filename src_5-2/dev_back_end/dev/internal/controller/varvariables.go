package controller

import (
	"context"
	v1 "dev/api/dev/v1"
	"dev/internal/service"
	"fmt"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

var Variable = cVariable{}

type cVariable struct{}

// 获取所有变量列表
func (c cVariable) GetVariables(ctx context.Context, req *v1.VariableListReq) (res *v1.VariableListRes, err error) {
	variables, err := service.Variables().GetVariables(ctx)
	if err != nil {
		g.Log().Error(ctx, "获取变量列表失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "获取变量列表失败")
	}
	res = &v1.VariableListRes{
		Variables: variables,
	}
	return
}

// 根据设备id获取变量列表
func (c cVariable) GetVarByDeviceId(ctx context.Context, req *v1.GetVarByDeviceIdReq) (res *v1.VariableListRes, err error) {
	variables, err := service.Variables().GetVarByDeviceId(ctx, req.DeviceId)
	if err != nil {
		g.Log().Error(ctx, "根据设备ID获取变量列表失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "根据设备ID获取变量列表失败")
	}
	res = &v1.VariableListRes{
		Variables: variables,
	}
	return
}

// 新建变量记录
func (c cVariable) AddVariable(ctx context.Context, req *v1.AddVariableReq) (res *v1.AddVariableRes, err error) {
	if err := service.Variables().AddVariable(ctx, req.Variable); err != nil {
		fmt.Println("测试数据", req.Variable)
		g.Log().Error(ctx, "新建变量记录失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "新建变量记录失败")
	}
	res = &v1.AddVariableRes{
		Message: "新建变量记录成功",
	}
	return
}

// 修改变量记录
func (c cVariable) UpdateVariable(ctx context.Context, req *v1.UpdateVariableReq) (res *v1.UpdateVariableRes, err error) {
	if err := service.Variables().UpdateVariable(ctx, req.Variable); err != nil {
		g.Log().Error(ctx, "修改变量记录失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "修改变量记录失败")
	}
	res = &v1.UpdateVariableRes{
		Message: "修改变量记录成功",
	}
	return
}
func (c cVariable) DeleteVariable(ctx context.Context, req *v1.DeleteVariableReq) (res *v1.DeleteVariableRes, err error) {
	// g.Log().Info(ctx, "删除变量记录", req.In)
	if err := service.Variables().DeleteVariable(ctx, req.In); err != nil {
		g.Log().Error(ctx, "删除变量记录失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "删除变量记录失败")
	}
	res = &v1.DeleteVariableRes{
		Message: "删除变量记录成功",
	}
	return
}

// 撤回之前操作
func (c cVariable) RecoveryVariable(ctx context.Context, req *v1.RecoveryVariableReq) (res *v1.RecoveryVariableRes, err error) {
	if err := service.Recove().RecoveryVariable(ctx, req.DevID); err != nil {
		g.Log().Error(ctx, "回溯变量失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "回溯变量失败")
	}
	return
}

// 数据类型迁移
func (c cVariable) MigrateDataTypes(ctx context.Context, req *v1.MigrateDataTypesReq) (res *v1.MigrateDataTypesRes, err error) {
	g.Log().Info(ctx, "数据类型迁移开始")
	
	totalMigrated, err := service.Variables().MigrateDataTypes(ctx)
	if err != nil {
		g.Log().Error(ctx, "数据类型迁移失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "数据类型迁移失败")
	}
	
	res = &v1.MigrateDataTypesRes{
		Message: fmt.Sprintf("数据类型迁移成功，共迁移 %d 个变量", totalMigrated),
		TotalMigrated: totalMigrated,
	}
	
	g.Log().Info(ctx, "数据类型迁移完成", res.Message)
	return
}

// 批量新建变量记录
func (c cVariable) BatchAddVariable(ctx context.Context, req *v1.BatchAddVariableReq) (res *v1.BatchAddVariableRes, err error) {
	g.Log().Info(ctx, "批量新建变量记录", "count", len(req.Variables))
	if len(req.Variables) == 0 {
		return &v1.BatchAddVariableRes{
			SuccessCount: 0,
			TotalCount:   0,
			Message:      "没有需要导入的变量",
		}, nil
	}
	successCount, err := service.Variables().BatchAddVariable(ctx, req.Variables)
	if err != nil {
		g.Log().Error(ctx, "批量新建变量记录失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "批量新建变量记录失败")
	}
	res = &v1.BatchAddVariableRes{
		SuccessCount: successCount,
		TotalCount:   len(req.Variables),
		Message:      fmt.Sprintf("成功导入 %d / %d 个变量", successCount, len(req.Variables)),
	}
	return
}
