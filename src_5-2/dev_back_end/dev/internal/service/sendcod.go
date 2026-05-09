package service

import (
	"context"
	"dev/internal/model"
)

type IsendCod interface {
	// SendModuleConfig 下发模组配置（功能码02）
	SendModuleConfig(ctx context.Context, req *model.ModbusRequest) error
	// SendDataConfig 下发数据配置（功能码04）
	SendDataConfig(ctx context.Context, req *model.ModbusRequest) (*model.OptimizationResult, string, error)
	// QueryDataConfig 查询数据配置（功能码03）
	QueryDataConfig(ctx context.Context, devSerial string) error
	// RemoteWrite 远程置数（功能码06）
	RemoteWrite(ctx context.Context, req *model.ModbusRequest) error
}

var logicSendCod IsendCod

func SendCod() IsendCod {
	if logicSendCod == nil {
		panic("implement not found for interface IsendCod, forgot register?")
	}
	return logicSendCod
}
func RegisterSendCod(i IsendCod) {
	logicSendCod = i
}
