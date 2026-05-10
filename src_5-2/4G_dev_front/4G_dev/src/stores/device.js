import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useDeviceStore = defineStore('device', () => {
  const deviceList = ref([])
  const selectedDevices = ref([])
  const lastFetchTime = ref(0)
  const loading = ref(false)

  async function fetchDevices(force = false) {
    if (!force && Date.now() - lastFetchTime.value < 30000 && deviceList.value.length > 0) {
      return deviceList.value
    }

    loading.value = true
    try {
      const res = await api.getDeviceList()
      let list = []
      if (res.data && res.data.code === 0) {
        if (res.data.data && res.data.data.devicelist) {
          list = res.data.data.devicelist
        } else if (res.data.devicelist) {
          list = res.data.devicelist
        }
      }
      deviceList.value = (list || []).map((item, idx) => ({
        id: item.id || idx,
        name: item.Devname || item.name || '',
        sn: item.DevSerial || item.serial || '',
        location: item.DevLocation || item.location || '',
        status: item.DevStatus === 1 || item.DevStatus === '1' || item.status === 1 || item.status === '1' ? '在线' : '离线',
        lastOnline: item.LatestOnline || item.latest_online || '无记录',
        sendmodel: item.Sendmodel || item.sendmodel || item.send_model || '',
        config: item.Config || item.config || item.configdata || '',
        baud: item.Baud || item.baud || '',
        chengeFlag: item.chengeFlag ?? 0,
        successFlag: item.successFlag ?? 0,
      }))
      lastFetchTime.value = Date.now()
      return deviceList.value
    } catch (e) {
      console.error('获取设备列表失败', e)
      return []
    } finally {
      loading.value = false
    }
  }

  function setSelection(devices) {
    selectedDevices.value = devices
  }

  function clearSelection() {
    selectedDevices.value = []
  }

  function clearCache() {
    lastFetchTime.value = 0
  }

  return {
    deviceList,
    selectedDevices,
    loading,
    fetchDevices,
    setSelection,
    clearSelection,
    clearCache
  }
})
