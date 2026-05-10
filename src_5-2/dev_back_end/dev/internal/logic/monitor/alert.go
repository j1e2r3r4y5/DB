package monitor

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
)

// AlertType 告警类型
type AlertType string

const (
	AlertTypeDeviceOffline  AlertType = "device_offline"
	AlertTypeDeviceOnline   AlertType = "device_online"
	AlertTypeDataMissing    AlertType = "data_missing"
	AlertTypeParseError     AlertType = "parse_error"
	AlertTypeSystemCritical AlertType = "system_critical"
)

// AlertLevel 告警级别
type AlertLevel string

const (
	AlertLevelInfo     AlertLevel = "info"
	AlertLevelWarning  AlertLevel = "warning"
	AlertLevelCritical AlertLevel = "critical"
)

// Alert 告警信息
type Alert struct {
	ID        string       `json:"id"`
	Type      AlertType    `json:"type"`
	Level     AlertLevel   `json:"level"`
	Title     string       `json:"title"`
	Message   string       `json:"message"`
	DeviceID  string       `json:"device_id,omitempty"`
	DevName   string       `json:"dev_name,omitempty"`
	Location  string       `json:"location,omitempty"`
	CreatedAt gtime.Time   `json:"created_at"`
}

// AlertNotifier 告警通知器
type AlertNotifier struct {
	ctx          context.Context
	dingTalkWebhook string
	mu           sync.Mutex
	lastAlertMap map[string]time.Time // 防止告警风暴
}

var (
	alertNotifierInstance *AlertNotifier
	alertNotifierOnce     sync.Once
)

// GetAlertNotifier 获取告警通知器单例
func GetAlertNotifier(ctx context.Context) *AlertNotifier {
	alertNotifierOnce.Do(func() {
		webhook := g.Cfg().MustGet(ctx, "alert.dingtalk.webhook", "").String()
		alertNotifierInstance = &AlertNotifier{
			ctx:          ctx,
			dingTalkWebhook: webhook,
			lastAlertMap: make(map[string]time.Time),
		}
	})
	return alertNotifierInstance
}

// SendAlert 发送告警
func (n *AlertNotifier) SendAlert(alert *Alert) error {
	alert.CreatedAt = *gtime.Now()
	alert.ID = fmt.Sprintf("%s-%d", alert.Type, alert.CreatedAt.Timestamp())

	// 记录告警
	GetMetrics().IncAlert(string(alert.Type))

	// 防止告警风暴（相同设备的同类型告警，5分钟内只发一次）
	if alert.DeviceID != "" {
		key := string(alert.Type) + ":" + alert.DeviceID
		if n.shouldSuppressAlert(key) {
			g.Log().Debug(n.ctx, "Alert suppressed due to rate limit", "key", key)
			return nil
		}
	}

	// 记录日志
	g.Log().Warning(n.ctx, "Alert triggered",
		"type", alert.Type,
		"level", alert.Level,
		"title", alert.Title,
		"device", alert.DeviceID)

	// 发送钉钉通知
	if n.dingTalkWebhook != "" {
		return n.sendDingTalk(alert)
	}

	// 如果没有配置钉钉，只记录日志
	return nil
}

// shouldSuppressAlert 检查是否应该抑制告警
func (n *AlertNotifier) shouldSuppressAlert(key string) bool {
	n.mu.Lock()
	defer n.mu.Unlock()

	now := time.Now()
	if lastTime, exists := n.lastAlertMap[key]; exists {
		if now.Sub(lastTime) < 5*time.Minute {
			return true
		}
	}
	n.lastAlertMap[key] = now
	return false
}

// sendDingTalk 发送钉钉机器人通知
func (n *AlertNotifier) sendDingTalk(alert *Alert) error {
	// 构建钉钉消息
	message := map[string]interface{}{
		"msgtype": "markdown",
		"markdown": map[string]interface{}{
			"title": alert.Title,
			"text":  n.formatMarkdownMessage(alert),
		},
	}

	jsonData, err := json.Marshal(message)
	if err != nil {
		return err
	}

	// 发送 HTTP 请求
	resp, err := http.Post(n.dingTalkWebhook, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		g.Log().Error(n.ctx, "Failed to send DingTalk alert", err)
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		g.Log().Error(n.ctx, "DingTalk alert returned non-200 status", "status", resp.StatusCode)
	}

	return nil
}

// formatMarkdownMessage 格式化 Markdown 消息
func (n *AlertNotifier) formatMarkdownMessage(alert *Alert) string {
	var levelEmoji string
	switch alert.Level {
	case AlertLevelCritical:
		levelEmoji = "🚨"
	case AlertLevelWarning:
		levelEmoji = "⚠️"
	default:
		levelEmoji = "ℹ️"
	}

	text := fmt.Sprintf("### %s %s\n\n", levelEmoji, alert.Title)
	text += fmt.Sprintf("- **时间**: %s\n", alert.CreatedAt.Format("Y-m-d H:i:s"))
	text += fmt.Sprintf("- **类型**: %s\n", alert.Type)
	text += fmt.Sprintf("- **级别**: %s\n", alert.Level)

	if alert.DeviceID != "" {
		text += fmt.Sprintf("- **设备序列号**: %s\n", alert.DeviceID)
	}
	if alert.DevName != "" {
		text += fmt.Sprintf("- **设备名称**: %s\n", alert.DevName)
	}
	if alert.Location != "" {
		text += fmt.Sprintf("- **位置**: %s\n", alert.Location)
	}

	text += fmt.Sprintf("\n**详情**: %s\n", alert.Message)

	return text
}

// AlertDeviceOffline 创建设备离线告警
func AlertDeviceOffline(ctx context.Context, devSerial, devName, location string, lastOnline *gtime.Time) {
	alert := &Alert{
		Type:     AlertTypeDeviceOffline,
		Level:    AlertLevelWarning,
		Title:    "设备离线告警",
		Message:  fmt.Sprintf("设备已离线，最后在线时间: %s", lastOnline.Format("Y-m-d H:i:s")),
		DeviceID: devSerial,
		DevName:  devName,
		Location: location,
	}

	GetAlertNotifier(ctx).SendAlert(alert)
}

// AlertDeviceOnline 创建设备恢复在线通知
func AlertDeviceOnline(ctx context.Context, devSerial, devName, location string) {
	alert := &Alert{
		Type:     AlertTypeDeviceOnline,
		Level:    AlertLevelInfo,
		Title:    "设备恢复在线",
		Message:  "设备已恢复在线",
		DeviceID: devSerial,
		DevName:  devName,
		Location: location,
	}

	GetAlertNotifier(ctx).SendAlert(alert)
}

// AlertDataMissing 创建数据缺失告警
func AlertDataMissing(ctx context.Context, devSerial, devName string) {
	alert := &Alert{
		Type:     AlertTypeDataMissing,
		Level:    AlertLevelWarning,
		Title:    "数据上报异常",
		Message:  "设备数据上报异常，请注意检查",
		DeviceID: devSerial,
		DevName:  devName,
	}

	GetAlertNotifier(ctx).SendAlert(alert)
}
