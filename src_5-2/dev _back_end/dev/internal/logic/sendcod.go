package logic

import (
	"dev/internal/service"
)

type sSend struct {
}

func init() {
	service.RegisterSendCod(NewSend())

}
func NewSend() *sSend {
	return &sSend{}
}

// // 接收前端发过来的json格式指令
// func (s *sSend) GetsendCod(ctx context.Context, po *model.ModbusRequest) error {
// 	// 这里可以处理 po 中的指令
// 	if po == nil {
// 		g.Log().Error(ctx, "指令包是空的")
// 		return gerror.New("指令包为空")
// 	}
// 	g.Log().Info(ctx, "接收到指令", po)
// 	topic := fmt.Sprintf("/dtu/%s/up", po.DevSerial) // 设备序列号
// 	payload := []byte("01")
// 	// 处理指令逻辑先判断首位功能码
// 	switch po.FunctionCode {
// 	case 1:
// 		g.Log().Info(ctx, "处理功能码 1")
// 		//根据传过来的设备序列号下发消息
// 		service.Mqtt().SendMessage(mqttClient, payload, topic)
// 	case 2:
// 		g.Log().Info(ctx, "处理功能码 2")

// 	}

// 	return nil
// }
