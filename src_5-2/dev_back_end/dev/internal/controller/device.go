package controller

import (
	"context"
	v1 "dev/api/dev/v1"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

var Dvice = cDvice{}

type cDvice struct{}

// 新建设备
func (c cDvice) AddDevice(ctx context.Context, req *v1.DeviceList) (res *v1.DeviceListres, err error) {
	if len(req.Device) == 0 {
		g.Log().Error(ctx, "设备列表不能为空")
	}
	result, err := service.Device().CreateDevice(ctx, &model.DeviceCreateListInput{Devices: req.Device})
	g.Log().Info(ctx, "创建设备结果", result)
	if err != nil {
		return res, gerror.NewCode(gcode.CodeInternalError, "内部错误 ")
	}
	res = &v1.DeviceListres{
		FailureList: result.FailureList,
		Total:       len(result.FailureList),
	}
	return
}

// 修改设备信息
func (c cDvice) ModifyDevice(ctx context.Context, req *v1.Modeifdevice) (res *v1.Modeifdevice, err error) {
	if req.ID <= 0 {
		g.Log().Error(ctx, "设备ID不能为空")
	}
	input := &model.ModifyDeviceInput{
		ID:          req.ID,
		Devname:     req.Devname,
		DevSerial:   req.DevSerial,
		DevLocation: req.DevLocation,
		Sendmodel:   req.Sendmodel,
		Baud:        req.Baud,
		Configdata:  req.Configdata,
	}
	g.Log().Info(ctx, "修改设备信息为", input)
	err = service.Device().ModifyDevice(ctx, input)
	if err != nil {
		g.Log().Error(ctx, "修改设备信息失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "修改设备信息失败")
	}
	return
}

// 删除设备
func (c cDvice) RemoveDevice(ctx context.Context, req *v1.RemoveDeviceInput) (res *v1.RemoveDeviceRes, err error) {
	if len(req.Idlist) == 0 {
		g.Log().Error(ctx, "设备ID列表不能为空")
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "设备ID列表不能为空")
	}
	err = service.Device().RemoveDevice(ctx, model.RemoveDeviceInput{Idlist: req.Idlist})
	if err != nil {
		g.Log().Error(ctx, "删除设备失败", err)
	}
	return
}

// 获取所有设备列表
func (c cDvice) GetDevice(ctx context.Context, req *v1.Device) (res *v1.Deviceres, err error) {
	list, err := service.Device().GetDevicelist(ctx)
	if err != nil {
		g.Log().Error(ctx, "获取设备列表失败", err)
		return nil, gerror.NewCode(gcode.CodeInternalError, "获取设备列表失败")
	}
	res = &v1.Deviceres{
		Devicelist: list,
		Total:      len(list),
	}
	return res, nil
}
