package service

import (
	"context"
	"dev/internal/model"
)

type (
	IDevice interface {
		//新建单个设备
		AddDevice(ctx context.Context, device *model.AddDevice) (out *model.Failed, ok bool, err error)
		Chenckdev(ctx context.Context, dev *model.AddDevice) (bool, string)
		CreateDevice(ctx context.Context, device *model.DeviceCreateListInput) (out *model.FailedList, err error)
		ModifyDevice(ctx context.Context, input *model.ModifyDeviceInput) (err error)
		RemoveDevice(ctx context.Context, id model.RemoveDeviceInput) (err error)
		GetDevicelist(ctx context.Context) (list []*model.Device, err error)
	}
)

var (
	localDevice IDevice
)

func Device() IDevice {
	if localDevice == nil {
		panic("implement not found for interface IDevice, forgot register?")
	}
	return localDevice
}

func RegisterDevice(i IDevice) {
	localDevice = i
}
