<template>
  <div class="dashboard">
    <SkeletonLoader v-if="monitorStore.loading && !monitorStore.stats.devices_total" :count="4" />
    <template v-else>
      <div class="dashboard-header">
        <div class="overview-cards">
          <div class="overview-card total">
            <div class="overview-icon">📊</div>
            <div class="overview-info">
              <div class="overview-value">{{ monitorStore.stats.devices_total }}</div>
              <div class="overview-label">总设备数</div>
            </div>
          </div>
          <div class="overview-card online">
            <div class="overview-icon">✅</div>
            <div class="overview-info">
              <div class="overview-value">{{ monitorStore.stats.devices_online }}</div>
              <div class="overview-label">在线设备</div>
            </div>
          </div>
          <div class="overview-card offline">
            <div class="overview-icon">⚠️</div>
            <div class="overview-info">
              <div class="overview-value">{{ monitorStore.stats.devices_offline }}</div>
              <div class="overview-label">离线设备</div>
            </div>
          </div>
          <div class="overview-card data">
            <div class="overview-icon">📝</div>
            <div class="overview-info">
              <div class="overview-value">{{ formatNumber(monitorStore.stats.datapoints_written) }}</div>
              <div class="overview-label">今日数据</div>
            </div>
          </div>
        </div>
      </div>

      <div class="dashboard-body">
        <div class="health-section">
          <div class="section-header">
            <h3>系统健康状态</h3>
            <span class="refresh-time" v-if="monitorStore.lastRefreshTime">
              最后刷新: {{ monitorStore.lastRefreshTime }}
            </span>
          </div>
          <div class="health-cards">
            <div class="health-card" :class="{ good: monitorStore.health.mysql?.healthy, bad: !monitorStore.health.mysql?.healthy }">
              <div class="health-icon">🗄️</div>
              <div class="health-label">MySQL</div>
              <div class="health-status">{{ monitorStore.health.mysql?.healthy ? '正常' : '异常' }}</div>
            </div>
            <div class="health-card" :class="{ good: monitorStore.health.redis?.healthy, bad: !monitorStore.health.redis?.healthy }">
              <div class="health-icon">⚡</div>
              <div class="health-label">Redis</div>
              <div class="health-status">{{ monitorStore.health.redis?.healthy ? '正常' : '异常' }}</div>
            </div>
            <div class="health-card" :class="{ good: monitorStore.health.influxdb?.healthy, bad: !monitorStore.health.influxdb?.healthy }">
              <div class="health-icon">📊</div>
              <div class="health-label">InfluxDB</div>
              <div class="health-status">{{ monitorStore.health.influxdb?.healthy ? '正常' : '异常' }}</div>
            </div>
            <div class="health-card" :class="{ good: monitorStore.health.mqtt?.healthy, bad: !monitorStore.health.mqtt?.healthy }">
              <div class="health-icon">📡</div>
              <div class="health-label">MQTT</div>
              <div class="health-status">{{ monitorStore.health.mqtt?.healthy ? '正常' : '异常' }}</div>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <div class="section-header">
            <h3>数据统计</h3>
            <el-button type="primary" size="small" @click="handleRefresh" :loading="monitorStore.loading">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
          <div class="stats-cards">
            <div class="stat-card">
              <div class="stat-icon">📥</div>
              <div class="stat-value">{{ formatNumber(monitorStore.stats.mqtt_messages_received) }}</div>
              <div class="stat-label">收到消息</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📤</div>
              <div class="stat-value">{{ formatNumber(monitorStore.stats.mqtt_messages_sent) }}</div>
              <div class="stat-label">发送消息</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📝</div>
              <div class="stat-value">{{ formatNumber(monitorStore.stats.datapoints_written) }}</div>
              <div class="stat-label">数据点数</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">⏱️</div>
              <div class="stat-value">{{ monitorStore.formatUptime(monitorStore.stats.app_uptime_seconds) }}</div>
              <div class="stat-label">运行时间</div>
            </div>
          </div>
        </div>

        <div class="charts-section">
          <div class="chart-card">
            <h3>设备在线趋势 (24小时)</h3>
            <div class="chart-container" ref="trendChartRef"></div>
          </div>
          <div class="chart-card">
            <h3>在线/离线比例</h3>
            <div class="chart-container" ref="pieChartRef"></div>
          </div>
        </div>

        <div class="bar-chart-section">
          <div class="chart-card full-width">
            <h3>数据上报量趋势 (近7天)</h3>
            <div class="chart-container" ref="barChartRef"></div>
          </div>
        </div>

        <div class="alerts-section">
          <div class="section-header">
            <h3>最近事件</h3>
          </div>
          <div class="alerts-list">
            <el-empty v-if="monitorStore.alerts.length === 0" description="暂无事件" />
            <div v-for="(alert, idx) in monitorStore.alerts" :key="idx" class="alert-item" :class="alert.type">
              <span class="alert-time">{{ alert.time }}</span>
              <span class="alert-content">{{ alert.content }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useMonitorStore } from '../stores'
import * as echarts from 'echarts'
import SkeletonLoader from '../components/SkeletonLoader.vue'

const monitorStore = useMonitorStore()

const trendChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
let trendChart = null
let pieChart = null
let barChart = null
let timer = null

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return String(num)
}

function handleRefresh() {
  monitorStore.refreshAll()
}

function initCharts() {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    const times = monitorStore.stats.online_trend?.times || generateMockTimes()
    const values = monitorStore.stats.online_trend?.values || generateMockValues()
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: times, boundaryGap: false },
      yAxis: { type: 'value' },
      series: [{
        name: '在线设备',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 },
        data: values,
        itemStyle: { color: '#67C23A' }
      }]
    })
  }

  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%', left: 'center' },
      series: [{
        name: '设备状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, position: 'center', formatter: '{b}\n{c}' },
        emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
        data: [
          { value: monitorStore.stats.devices_online, name: '在线', itemStyle: { color: '#67C23A' } },
          { value: monitorStore.stats.devices_offline, name: '离线', itemStyle: { color: '#E6A23C' } }
        ]
      }]
    })
  }

  if (barChartRef.value) {
    barChart = echarts.init(barChartRef.value)
    const dates = monitorStore.stats.data_trend?.dates || generateMockDates()
    const values = monitorStore.stats.data_trend?.values || generateMockBarValues()
    barChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [{
        name: '数据点数',
        type: 'bar',
        barWidth: '50%',
        data: values,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#79bbff' }
          ])
        }
      }]
    })
  }
}

function generateMockTimes() {
  const times = []
  for (let i = 24; i >= 0; i--) {
    const hour = new Date(Date.now() - i * 3600000).getHours()
    times.push(hour + ':00')
  }
  return times
}

function generateMockValues() {
  const values = []
  for (let i = 0; i < 25; i++) {
    values.push(Math.floor(Math.random() * 10) + 45)
  }
  return values
}

function generateMockDates() {
  const dates = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000)
    dates.push((d.getMonth() + 1) + '/' + d.getDate())
  }
  return dates
}

function generateMockBarValues() {
  const values = []
  for (let i = 0; i < 7; i++) {
    values.push(Math.floor(Math.random() * 200000) + 400000)
  }
  return values
}

function resizeCharts() {
  trendChart?.resize()
  pieChart?.resize()
  barChart?.resize()
}

watch(() => monitorStore.stats, () => {
  nextTick(() => {
    if (trendChart) {
      trendChart.setOption({
        xAxis: { data: monitorStore.stats.online_trend?.times || generateMockTimes() },
        series: [{ data: monitorStore.stats.online_trend?.values || generateMockValues() }]
      })
    }
    if (pieChart) {
      pieChart.setOption({
        series: [{
          data: [
            { value: monitorStore.stats.devices_online, name: '在线', itemStyle: { color: '#67C23A' } },
            { value: monitorStore.stats.devices_offline, name: '离线', itemStyle: { color: '#E6A23C' } }
          ]
        }]
      })
    }
    if (barChart) {
      barChart.setOption({
        xAxis: { data: monitorStore.stats.data_trend?.dates || generateMockDates() },
        series: [{ data: monitorStore.stats.data_trend?.values || generateMockBarValues() }]
      })
    }
  })
}, { deep: true })

onMounted(async () => {
  await monitorStore.refreshAll()
  nextTick(() => {
    initCharts()
  })
  window.addEventListener('resize', resizeCharts)
  timer = setInterval(() => {
    monitorStore.refreshAll()
  }, 15000)
})

onUnmounted(() => {
  trendChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  window.removeEventListener('resize', resizeCharts)
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dashboard-header {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7eb 100%);
}

.overview-card.total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }
.overview-card.online { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: #fff; }
.overview-card.offline { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #fff; }
.overview-card.data { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #fff; }

.overview-icon { font-size: 2.5rem; }
.overview-value { font-size: 2rem; font-weight: 700; }
.overview-label { font-size: 0.95rem; opacity: 0.9; }

.dashboard-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  color: #223147;
  font-size: 1.15rem;
  font-weight: 600;
  margin: 0;
}

.refresh-time {
  color: #909399;
  font-size: 0.85rem;
}

.health-section, .stats-section, .charts-section, .bar-chart-section, .alerts-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.chart-card.full-width {
  width: 100%;
}

.health-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.health-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  border-radius: 10px;
  transition: transform 0.2s;
}

.health-card.good { background: linear-gradient(135deg, #e6f7ff 0%, #f0fff4 100%); }
.health-card.bad { background: linear-gradient(135deg, #fff0f0 0%, #ffe6e6 100%); }

.health-icon { font-size: 2rem; margin-bottom: 8px; }
.health-label { font-size: 1rem; color: #223147; font-weight: 600; }
.health-status { font-size: 0.9rem; margin-top: 4px; }
.health-card.good .health-status { color: #008a00; font-weight: 700; }
.health-card.bad .health-status { color: #cf1322; font-weight: 700; }

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
}

.stat-icon { font-size: 1.8rem; margin-bottom: 8px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #223147; margin-bottom: 4px; }
.stat-label { font-size: 0.9rem; color: #555; }

.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
}

.chart-card h3 {
  color: #223147;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.chart-container {
  height: 280px;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #d9d9d9;
}

.alert-item.warning { border-left-color: #ff9100; background: #fff7e6; }
.alert-item.error { border-left-color: #cf1322; background: #fff1f0; }
.alert-item.success { border-left-color: #008a00; background: #f0fff4; }

.alert-time { color: #999; font-size: 0.85rem; min-width: 80px; }
.alert-content { color: #333; flex: 1; }

@media (max-width: 1200px) {
  .overview-cards { grid-template-columns: repeat(2, 1fr); }
  .health-cards { grid-template-columns: repeat(2, 1fr); }
  .stats-cards { grid-template-columns: repeat(2, 1fr); }
  .charts-section { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .overview-cards { grid-template-columns: 1fr; }
  .health-cards { grid-template-columns: 1fr; }
  .stats-cards { grid-template-columns: 1fr; }
}
</style>
