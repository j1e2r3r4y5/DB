package monitor

import (
	"fmt"
	"sync"
	"time"

	"github.com/gogf/gf/v2/frame/g"
)

var (
	metricsInstance *Metrics
	metricsOnce     sync.Once
)

// Metrics 应用指标收集器
type Metrics struct {
	mu sync.RWMutex

	// 设备指标
	devicesOnline  int64
	devicesOffline int64

	// MQTT 指标
	mqttMessagesReceivedTotal int64
	mqttMessagesSentTotal     int64

	// 数据点指标
	datapointsWrittenTotal int64

	// HTTP 指标
	httpRequestsTotal   map[string]int64 // path -> count
	httpRequestDuration map[string][]float64

	// 告警指标
	alertsTotal map[string]int64 // alert_type -> count

	// 健康检查
	healthChecks map[string]bool // component -> healthy

	startTime time.Time
}

// GetMetrics 获取指标单例
func GetMetrics() *Metrics {
	metricsOnce.Do(func() {
		metricsInstance = &Metrics{
			httpRequestsTotal:   make(map[string]int64),
			httpRequestDuration: make(map[string][]float64),
			alertsTotal:         make(map[string]int64),
			healthChecks:        make(map[string]bool),
			startTime:           time.Now(),
		}
	})
	return metricsInstance
}

// IncMQTTMessagesReceived 增加 MQTT 接收消息计数
func (m *Metrics) IncMQTTMessagesReceived() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.mqttMessagesReceivedTotal++
}

// IncMQTTMessagesSent 增加 MQTT 发送消息计数
func (m *Metrics) IncMQTTMessagesSent() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.mqttMessagesSentTotal++
}

// IncDatapointsWritten 增加数据点写入计数
func (m *Metrics) IncDatapointsWritten() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.datapointsWrittenTotal++
}

// IncHTTPRequest 增加 HTTP 请求计数
func (m *Metrics) IncHTTPRequest(method, path, status string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	key := method + ":" + path + ":" + status
	m.httpRequestsTotal[key]++
}

// ObserveHTTPRequestDuration 记录 HTTP 请求耗时
func (m *Metrics) ObserveHTTPRequestDuration(path string, duration float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.httpRequestDuration[path] == nil {
		m.httpRequestDuration[path] = make([]float64, 0, 100)
	}
	if len(m.httpRequestDuration[path]) >= 100 {
		m.httpRequestDuration[path] = m.httpRequestDuration[path][1:]
	}
	m.httpRequestDuration[path] = append(m.httpRequestDuration[path], duration)
}

// SetDeviceStatus 更新设备状态计数
func (m *Metrics) SetDeviceStatus(online, offline int64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.devicesOnline = online
	m.devicesOffline = offline
}

// IncAlert 增加告警计数
func (m *Metrics) IncAlert(alertType string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.alertsTotal[alertType]++
}

// SetHealthCheck 更新组件健康状态
func (m *Metrics) SetHealthCheck(component string, healthy bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.healthChecks[component] = healthy
}

// GetStats 获取指标统计
func (m *Metrics) GetStats() g.Map {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stats := g.Map{
		"uptime_seconds":           time.Since(m.startTime).Seconds(),
		"devices_online":           m.devicesOnline,
		"devices_offline":          m.devicesOffline,
		"mqtt_messages_received":   m.mqttMessagesReceivedTotal,
		"mqtt_messages_sent":       m.mqttMessagesSentTotal,
		"datapoints_written":       m.datapointsWrittenTotal,
		"http_requests_total":      m.httpRequestsTotal,
		"alerts_total":             m.alertsTotal,
		"health_checks":            m.healthChecks,
		"online_trend":             m.generateOnlineTrend(),
		"data_trend":               m.generateDataTrend(),
	}

	// 计算平均请求耗时
	averageDurations := make(map[string]float64)
	for path, durations := range m.httpRequestDuration {
		if len(durations) > 0 {
			var sum float64
			for _, d := range durations {
				sum += d
			}
			averageDurations[path] = sum / float64(len(durations))
		}
	}
	stats["http_request_duration_avg"] = averageDurations

	return stats
}

// generateOnlineTrend 生成24小时设备在线趋势数据
func (m *Metrics) generateOnlineTrend() g.Map {
	times := make([]string, 0, 24)
	values := make([]int64, 0, 24)
	
	now := time.Now()
	for i := 23; i >= 0; i-- {
		t := now.Add(-time.Duration(i) * time.Hour)
		times = append(times, t.Format("15:04"))
		// 模拟数据：当前值附近波动
		base := m.devicesOnline
		if base == 0 {
			base = 1
		}
		fluctuation := int64((i % 5) - 2)
		value := base + fluctuation
		if value < 0 {
			value = 0
		}
		values = append(values, value)
	}
	
	return g.Map{
		"times":  times,
		"values": values,
	}
}

// generateDataTrend 生成7天数据上报趋势
func (m *Metrics) generateDataTrend() g.Map {
	dates := make([]string, 0, 7)
	values := make([]int64, 0, 7)
	
	now := time.Now()
	baseValue := m.datapointsWrittenTotal / 7
	if baseValue == 0 {
		baseValue = 1000
	}
	
	for i := 6; i >= 0; i-- {
		t := now.Add(-time.Duration(i) * 24 * time.Hour)
		dates = append(dates, t.Format("1/2"))
		// 模拟数据：基础值附近波动
		fluctuation := int64((i % 3) - 1) * baseValue / 10
		value := baseValue + fluctuation
		if value < 0 {
			value = 0
		}
		values = append(values, value)
	}
	
	return g.Map{
		"dates":  dates,
		"values": values,
	}
}

// ExportPrometheusMetrics 导出 Prometheus 格式指标
func (m *Metrics) ExportPrometheusMetrics() string {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var result string

	result += "# HELP devices_online Number of online devices\n"
	result += "# TYPE devices_online gauge\n"
	result += fmt.Sprintf("devices_online %d\n", m.devicesOnline)

	result += "# HELP devices_offline Number of offline devices\n"
	result += "# TYPE devices_offline gauge\n"
	result += fmt.Sprintf("devices_offline %d\n", m.devicesOffline)

	result += "# HELP mqtt_messages_received_total Total number of MQTT messages received\n"
	result += "# TYPE mqtt_messages_received_total counter\n"
	result += fmt.Sprintf("mqtt_messages_received_total %d\n", m.mqttMessagesReceivedTotal)

	result += "# HELP mqtt_messages_sent_total Total number of MQTT messages sent\n"
	result += "# TYPE mqtt_messages_sent_total counter\n"
	result += fmt.Sprintf("mqtt_messages_sent_total %d\n", m.mqttMessagesSentTotal)

	result += "# HELP datapoints_written_total Total number of datapoints written\n"
	result += "# TYPE datapoints_written_total counter\n"
	result += fmt.Sprintf("datapoints_written_total %d\n", m.datapointsWrittenTotal)

	result += "# HELP app_uptime_seconds Application uptime in seconds\n"
	result += "# TYPE app_uptime_seconds counter\n"
	result += fmt.Sprintf("app_uptime_seconds %f\n", time.Since(m.startTime).Seconds())

	return result
}

// DeviceOnline 记录设备上线
func (m *Metrics) DeviceOnline() {
	m.IncMQTTMessagesReceived()
}

// DeviceDataReported 记录设备数据上报
func (m *Metrics) DeviceDataReported() {
	m.IncMQTTMessagesReceived()
	m.IncDatapointsWritten()
}
