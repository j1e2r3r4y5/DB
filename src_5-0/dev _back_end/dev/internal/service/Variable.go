package service

import (
	"context"
	"dev/internal/model"
)

type (
	variables interface {
		GetVariables(ctx context.Context) ([]*model.Variables, error)
		GetVarByDeviceId(ctx context.Context, deviceId int) ([]*model.Variables, error)
		AddVariable(ctx context.Context, variable *model.Variables) error
		UpdateVariable(ctx context.Context, variable *model.Variables) error
		DeleteVariable(ctx context.Context, in *model.Variables) error
	}
)

var (
	localvar variables
)

func Variables() variables {
	if localvar == nil {
		panic("implement not found for interface IToken, forgot register?")
	}
	return localvar
}

func RegisterVar(i variables) {
	localvar = i
}
