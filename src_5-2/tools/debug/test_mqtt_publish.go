package main

import (
	"fmt"
	"log"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

func main() {
	// 连接参数
	broker := "tcp://127.0.0.1:1883"
	clientID := "test_device"
	topic := "/dtu/A1B2C3D4/up"

	// 创建客户端选项
	opts := mqtt.NewClientOptions().AddBroker(broker)
	opts.SetClientID(clientID)
	opts.SetCleanSession(true)
	opts.SetConnectTimeout(10 * time.Second)

	// 创建客户端
	client := mqtt.NewClient(opts)

	// 连接
	fmt.Println("正在连接MQTT Broker...")
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalf("连接失败: %v", token.Error())
	}
	fmt.Println("连接成功！")
	defer client.Disconnect(250)

	// 构造模拟心跳包数据
	// 功能码 0x00 = 心跳包
	// 数据部分：当前时间戳（模拟）
	payload := []byte{0x00, 0x00, 0x00, 0x00, 0x00}

	fmt.Printf("正在发送消息到主题: %s\n", topic)
	fmt.Printf("消息内容: %X\n", payload)

	// 发布消息
	token := client.Publish(topic, 0, false, payload)
	if token.Wait() && token.Error() != nil {
		log.Fatalf("发送失败: %v", token.Error())
	}

	fmt.Println("消息发送成功！")

	// 等待一下再退出
	time.Sleep(1 * time.Second)
}
