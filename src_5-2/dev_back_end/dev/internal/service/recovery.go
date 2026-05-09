package service

import (
	"context"
	"dev/internal/model"
)

type Irecove interface {
	RecoveryVariable(ctx context.Context, devID int) error
	InsertRecord(ctx context.Context, in *model.Variables) (err error)
}

var logicrecove Irecove

func Recove() Irecove {
	if logicrecove == nil {
		panic("implement not found for interface IMqtt, forgot register?")
	}
	return logicrecove
}
func Registerecove(i Irecove) {
	logicrecove = i
}
