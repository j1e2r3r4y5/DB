package v1

import (
	"dev/internal/model"

	"github.com/gogf/gf/v2/frame/g"
)

type FunctionCode struct {
	g.Meta `json:"/sendcod" method:"post" summary:"发送指令" tags:"设备管理"`
	Code   *model.ModbusRequest `json:"code"`
}
