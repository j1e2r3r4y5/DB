package service

import (
	"context"
	"dev/internal/model"
)

type IPayload interface {
	PayloadHandler(ctx context.Context, devSerial string, payload []byte) (isRepeat bool, Featurescode byte, DevUpdate *model.DevUpdateItem, LogUpdate *model.LogUpdateItem, err error)
	HexStringToBytes(hexStr string) ([]byte, error)
	DownPayloadHandler(ctx context.Context, topic string, code []byte) (err error)
	// QueryDevStatusFromInflux(ctx context.Context, org string, bucket string, devUpdate *model.DevUpdateItem, featuresCode byte)
	// QueryLastDataItemFromInflux(ctx context.Context, org, bucket string, DataItem *model.DataItem) error
}

var (
	localPayload IPayload
)

func Payload() IPayload {
	if localPayload == nil {
		panic("implement not found for interface IPayload, forgot register?")
	}
	return localPayload
}

func RegisterPayload(i IPayload) {
	localPayload = i
}
