package service

import mqtt "github.com/eclipse/paho.mqtt.golang"

type IMqtt interface {
	Init() // Init initializes the MQTT client
	SendMessage(client mqtt.Client, msg mqtt.Message, topic string)
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
