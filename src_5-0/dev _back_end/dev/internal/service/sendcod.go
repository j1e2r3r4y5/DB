package service

type IsendCod interface {
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
