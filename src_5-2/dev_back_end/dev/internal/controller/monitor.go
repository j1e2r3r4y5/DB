package controller

import (
	"dev/internal/logic/monitor"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

var Monitor = cmonitor{}

type cmonitor struct{}

// Health 健康检查端点
func (c *cmonitor) Health(r *ghttp.Request) {
	ctx := r.Context()
	checker := monitor.NewHealthChecker(ctx)
	checks := checker.CheckAll()
	healthy := checker.IsHealthy()

	r.Response.WriteJsonExit(g.Map{
		"status":  map[bool]string{true: "pass", false: "fail"}[healthy],
		"checks":  checks,
		"healthy": healthy,
	})
}

// Metrics Prometheus 指标端点
func (c *cmonitor) Metrics(r *ghttp.Request) {
	metrics := monitor.GetMetrics()
	r.Response.Write(metrics.ExportPrometheusMetrics())
}

// Stats 指标统计端点
func (c *cmonitor) Stats(r *ghttp.Request) {
	metrics := monitor.GetMetrics()
	r.Response.WriteJsonExit(metrics.GetStats())
}
