package logic

import (
	"context"
	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"
	"fmt"
	"regexp"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
)

var (
	opts       = mqtt.NewClientOptions()
	BrokerURI  = g.Cfg().MustGet(context.Background(), "mqtt.brokerURI").String()
	mqttClient mqtt.Client

	SubscribedDevIds = make([]uint64, 0)
)

type sMqtt struct {
}

func init() {
	service.RegisterMqtt(New_Mqtt())
}
func New_Mqtt() *sMqtt {
	return &sMqtt{}
}

// Init 初始化
func (s *sMqtt) Init() {
	opts.AddBroker(BrokerURI)
	opts.SetClientID(g.Cfg().MustGet(context.Background(), "mqtt.clientID").String())
	opts.SetCleanSession(g.Cfg().MustGet(context.Background(), "mqtt.cleanSession").Bool())
	opts.SetUsername(g.Cfg().MustGet(context.Background(), "mqtt.username").String())
	opts.SetPassword(g.Cfg().MustGet(context.Background(), "mqtt.password").String())
	opts.OnConnect = func(c mqtt.Client) {
		fmt.Println("连接成功")
		s.subscribeAll(context.Background())
		s.subscribeAllSandbox(context.Background())
	}
	mqttClient = mqtt.NewClient(opts)

	if token := mqttClient.Connect(); token.Wait() && token.Error() != nil {
		g.Log().Panic(context.Background(), token.Error())
	}

	// err := s.RefreshDeviceTopics(context.Background())
	// if err != nil {
	// 	g.Log().Debug(context.Background(), "RefreshDeviceTopics error", err)
	// }
	// g.Log().Info(context.Background(), "mqtt client initialization completed.")
}

// getUPTopic 获得指定设备的上行主题
func (s *sMqtt) getUPTopic(device string) string {
	return fmt.Sprintf("/dtu/%s/up", device)
}

// subscribeTopic 订阅指定主题
func (s *sMqtt) SubscribeTopic(ctx context.Context, device string) {
	topic := s.getUPTopic(device)
	fmt.Printf("add topic %s\n", topic)
	if token := mqttClient.Subscribe(topic, 2, func(c mqtt.Client, msg mqtt.Message) {
		if err := s.messageHandler(ctx, c, msg); err != nil {
			g.Log().Error(ctx, "mqtt messageHandler error", err)
		}
	}); token.Wait() && token.Error() != nil {
		g.Log().Error(ctx, token.Error())
	}
}
func (s *sMqtt) subscribeAll(ctx context.Context) error {
	var list []*model.Device
	err := dao.Dev.Ctx(ctx).WhereNotNull(dao.Dev.Columns().DevSerial).Scan(&list)
	if err != nil {
		g.Log().Error(ctx, "Failed to get device list", err)
	}
	for _, dev := range list {
		s.SubscribeTopic(ctx, dev.DevSerial)
	}
	return err
}

func (s *sMqtt) getSandboxUPTopic(device string) string {
	return fmt.Sprintf("/dtu/%s/sandbox/up", device)
}

func (s *sMqtt) subscribeAllSandbox(ctx context.Context) error {
	var list []*model.Device
	err := dao.Dev.Ctx(ctx).WhereNotNull(dao.Dev.Columns().DevSerial).Scan(&list)
	if err != nil {
		g.Log().Error(ctx, "Failed to get device list for sandbox", err)
		return err
	}
	for _, dev := range list {
		topic := s.getSandboxUPTopic(dev.DevSerial)
		fmt.Printf("add sandbox topic %s\n", topic)
		if token := mqttClient.Subscribe(topic, 2, func(c mqtt.Client, msg mqtt.Message) {
			ctxWithScope := context.WithValue(context.Background(), "scope", "sandbox")
			if err := s.messageHandler(ctxWithScope, c, msg); err != nil {
				g.Log().Error(ctx, "sandbox mqtt messageHandler error", err)
			}
		}); token.Wait() && token.Error() != nil {
			g.Log().Error(ctx, token.Error())
		}
	}
	return err
}

func (s *sMqtt) messageHandler(ctx context.Context, c mqtt.Client, msg mqtt.Message) error {
	// 处理接收到的消息
	fmt.Printf("[%s] 主题: %s | 消息: %2x\n",
		time.Now().Format("15:04:05"),
		msg.Topic(),
		string(msg.Payload()))
	serial, err := s.fetchDeviceSerial(msg)
	if err != nil {
		g.Log().Error(ctx, "无法提取设备序列号", err)
		return err
	}

	scope, _ := ctx.Value("scope").(string)
	isSandbox := scope == "sandbox"
	g.Log().Info(ctx, "接收到设备消息", "设备序列号", serial, "scope", scope)

	// 解析消息
	isRepeat, Featurescode, DevUpdate, LogUpdate, err := service.Payload().PayloadHandler(ctx, serial, msg.Payload())
	if err != nil {
		g.Log().Error(ctx, "PayloadHandler error", err)
		return err
	}
	g.Log().Debug(ctx, "Featurescode", Featurescode)
	g.Log().Debug(ctx, "devUpdateItem", DevUpdate)
	g.Log().Debug(ctx, "logUpdateItem", LogUpdate)

	if isRepeat {
		g.Log().Debug(ctx, "重复上报，忽略")
		return nil
	}
	
	if DevUpdate != nil && !isSandbox {
		g.Log().Info(ctx, "准备更新设备状态", 
			"设备序列号", DevUpdate.DevSerial, 
			"状态", DevUpdate.DevStatus, 
			"最新在线时间", DevUpdate.LatestOnline)
		_, err = dao.Dev.Ctx(ctx).OmitEmpty().Where(dao.Dev.Columns().DevSerial, DevUpdate.DevSerial).Data(g.Map{
			dao.Dev.Columns().DevStatus:    DevUpdate.DevStatus,
			dao.Dev.Columns().LatestOnline: DevUpdate.LatestOnline,
			dao.Dev.Columns().Sendmodel:    DevUpdate.Sendmodel,
			dao.Dev.Columns().Configdata:   DevUpdate.Configdata,
			dao.Dev.Columns().Baud:         DevUpdate.Baud,
		}).Update()
		if err != nil {
			g.Log().Error(ctx, "更新设备状态失败", err)
		} else {
			g.Log().Info(ctx, "设备状态更新成功", "设备序列号", DevUpdate.DevSerial)
		}
	}

	if err != nil {
		g.Log().Error(ctx, "更新设备状态失败", err)
	}
	// s.SendMessage(c, msg, msg.Topic())
	return nil
}

func (s *sMqtt) SendMessage(client mqtt.Client, msg mqtt.Message, topic string) {
	fmt.Printf("正在转发消息到主题: %s,消息：%02x\n", topic, string(msg.Payload()))

	token := client.Publish(topic, 1, false, msg.Payload())
	token.Wait()

	if token.Error() != nil {
		fmt.Printf("转发失败: %v\n", token.Error())
	} else {
		fmt.Printf("转发成功到主题: %s\n", topic)
	}
}

// PublishBytes 便捷方法：直接发送字节数组到指定主题
func (s *sMqtt) PublishBytes(topic string, payload []byte) error {
	g.Log().Debug(context.Background(), "PublishBytes", "topic", topic, "payload", fmt.Sprintf("%02x", payload))
	token := mqttClient.Publish(topic, 1, false, payload)
	token.Wait()
	if token.Error() != nil {
		g.Log().Error(context.Background(), "PublishBytes 失败", token.Error())
		return token.Error()
	}
	g.Log().Info(context.Background(), "PublishBytes 成功", "topic", topic)
	return nil
}

// fetchDeviceSerial 获取设备序列号
func (s *sMqtt) fetchDeviceSerial(msg mqtt.Message) (string, error) {
	devSerial, err := s.parseTopic(msg.Topic())
	return devSerial, err
}

// parseTopic 正则解析获取topic中的设备序列号
func (s *sMqtt) parseTopic(topic string) (string, error) {

	re := regexp.MustCompile(`/dtu/([0-9A-Fa-f]+)`)
	match := re.FindStringSubmatch(topic)
	if len(match) >= 2 {
		result := match[1]
		return result, nil
	}
	return "", gerror.New("无法解析设备序列号")
}
