package test

import (
	"context"
	"fmt"
	"testing"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

const (
	MQTTBroker   = "tcp://127.0.0.1:1883"
	TestDeviceSN  = "1234567890"
	UplinkTopic   = "/dtu/" + TestDeviceSN + "/up"
	DownlinkTopic = "/dtu/" + TestDeviceSN + "/down"
)

var mqttClient mqtt.Client
var ctx = context.Background()

func SetupMQTTClient(t *testing.T) {
	opts := mqtt.NewClientOptions()
	opts.AddBroker(MQTTBroker)
	opts.SetClientID("test-client-" + fmt.Sprintf("%d", time.Now().UnixNano()))
	opts.SetUsername("")
	opts.SetPassword("")
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)

	client := mqtt.NewClient(opts)
	token := client.Connect()
	if token.Wait() && token.Error() != nil {
		t.Fatalf("MQTT连接失败: %v", token.Error())
	}
	mqttClient = client
	t.Logf("MQTT客户端已连接: %s", MQTTBroker)
}

func DisconnectMQTT() {
	if mqttClient != nil && mqttClient.IsConnected() {
		mqttClient.Disconnect(250)
	}
}

func TestMain(m *testing.M) {
	m.Run()
}

type TestCase struct {
	Name           string
	ProtocolCode   byte
	Description    string
	Payload        []byte
	ExpectedResult bool
}

func (tc *TestCase) Run(t *testing.T, handler func([]byte) error) {
	t.Run(tc.Name, func(t *testing.T) {
		t.Logf("测试: %s", tc.Name)
		t.Logf("描述: %s", tc.Description)
		t.Logf("Payload (HEX): %X", tc.Payload)

		err := handler(tc.Payload)
		if tc.ExpectedResult && err != nil {
			t.Errorf("期望成功，实际失败: %v", err)
		} else if !tc.ExpectedResult && err == nil {
			t.Errorf("期望失败，实际成功")
		} else {
			t.Logf("结果: 通过 ✓")
		}
	})
}