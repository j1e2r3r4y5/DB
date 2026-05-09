package service

import (
	"context"
	"dev/internal/model"
)

type (
	IData interface {
		GetData(ctx context.Context) (res []*model.Data, err error)
	}
)

var (
	localData IData
)

func Data() IData {
	if localData == nil {
		panic("implement not found for interface IDevice, forgot register?")
	}
	return localData
}

func RegisterData(i IData) {
	localData = i
}
