import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useMonitorStore = defineStore('monitor', () => {
  const health = ref({
    mysql: { healthy: false },
    redis: { healthy: false },
    influxdb: { healthy: false },
    mqtt: { healthy: false }
  })

  const stats = ref({
    devices_online: 0,
    devices_offline: 0,
    devices_total: 0,
    mqtt_messages_received: 0,
    mqtt_messages_sent: 0,
    datapoints_written: 0,
    app_uptime_seconds: 0,
    online_trend: { times: [], values: [] },
    data_trend: { dates: [], values: [] }
  })

  const alerts = ref([])
  const lastRefreshTime = ref('')
  const loading = ref(false)

  async function refreshHealth() {
    try {
      const res = await api.getHealth()
      if (res.data && res.data.checks) {
        health.value = res.data.checks
      }
    } catch (e) {
      console.error('获取健康状态失败', e)
    }
  }

  async function refreshStats() {
    try {
      const res = await api.getStats()
      if (res.data) {
        stats.value.devices_online = res.data.devices_online || 0
        stats.value.devices_offline = res.data.devices_offline || 0
        stats.value.devices_total = (res.data.devices_online || 0) + (res.data.devices_offline || 0)
        stats.value.mqtt_messages_received = res.data.mqtt_messages_received || 0
        stats.value.mqtt_messages_sent = res.data.mqtt_messages_sent || 0
        stats.value.datapoints_written = res.data.datapoints_written || 0
        stats.value.app_uptime_seconds = res.data.uptime_seconds || 0
        
        if (res.data.online_trend) {
          stats.value.online_trend = res.data.online_trend
        }
        if (res.data.data_trend) {
          stats.value.data_trend = res.data.data_trend
        }
      }
      lastRefreshTime.value = new Date().toLocaleTimeString()
    } catch (e) {
      console.error('获取统计数据失败', e)
    }
  }

  async function refreshAll() {
    loading.value = true
    try {
      await Promise.all([refreshHealth(), refreshStats()])
    } finally {
      loading.value = false
    }
  }

  function formatUptime(seconds) {
    if (!seconds) return '0秒'
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    let res = ''
    if (days > 0) res += days + '天'
    if (hours > 0) res += hours + '时'
    if (minutes > 0) res += minutes + '分'
    if (secs > 0) res += secs + '秒'
    return res || '0秒'
  }

  return {
    health,
    stats,
    alerts,
    lastRefreshTime,
    loading,
    refreshHealth,
    refreshStats,
    refreshAll,
    formatUptime
  }
})
