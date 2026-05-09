package service

import mqtt "github.com/eclipse/paho.mqtt.golang"

type IMqtt interface {
	Init() // Init initializes the MQTT client
	SendMessage(client mqtt.Client, msg mqtt.Message, topic string)
	PublishBytes(topic string, payload []byte) error // 便捷方法：直接发送字节数组
}

var logicMqtt IMqtt

func Mqtt() IMqtt {
	if logicMqtt == nil {
		panic("implement not found for interface IMqtt, forgot register?")
	}
	return logicMqtt
}
func RegisterMqtt(i IMqtt) {
	logicMqtt = i
}
