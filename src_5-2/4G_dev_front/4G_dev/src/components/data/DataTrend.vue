<template>
    <div class="device-table-wrapper">
        <el-breadcrumb style="margin-bottom: 12px;">
            <el-breadcrumb-item>数据管理</el-breadcrumb-item>
            <el-breadcrumb-item>趋势图</el-breadcrumb-item>
        </el-breadcrumb>
        <div style="display: flex; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
            <el-button type="default" @click="goBack">返回</el-button>
            <span style="font-size: 14px; color: #222; font-weight: bold;">请选择设备</span>
            <el-select v-model="selectedDevID" placeholder="请选择设备" style="width:260px;" @change="onDeviceChange">
                <el-option v-for="dev in deviceOptions" :key="dev.id" :label="`${dev.name} (${dev.serial})`" :value="dev.id" />
            </el-select>
            <span style="font-size: 14px; color: #222; font-weight: bold;">变量</span>
            <el-select v-model="selectedVarNames" multiple placeholder="请选择变量" style="width:300px;" @change="onVarChange">
                <el-option v-for="v in variableOptions" :key="v.varName" :label="v.varName" :value="v.varName" />
            </el-select>
            <span style="font-size: 14px; color: #222; font-weight: bold;">时间范围</span>
            <el-radio-group v-model="timeRange" size="small" @change="onTimeRangeChange">
                <el-radio-button value="1h">1h</el-radio-button>
                <el-radio-button value="6h">6h</el-radio-button>
                <el-radio-button value="24h">24h</el-radio-button>
                <el-radio-button value="custom">自定义</el-radio-button>
            </el-radio-group>
            <el-date-picker v-if="timeRange === 'custom'" v-model="customTimeRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" @change="onTimeRangeChange" />
            <el-button type="primary" size="small" @click="fetchTrendData">查询</el-button>
        </div>
        <div ref="trendChartRef" style="width: 100%; height: 450px;"></div>
        <div style="margin-top: 12px; display: flex; gap: 8px;">
            <el-button type="primary" @click="exportImage">导出图片</el-button>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()

function goBack() { router.back() }

const selectedDevID = ref(null)
const deviceOptions = ref([])
const selectedVarNames = ref([])
const variableOptions = ref([])
const timeRange = ref('1h')
const customTimeRange = ref(null)
const trendChartRef = ref(null)
let chartInstance = null

const selectedDevice = computed(() => deviceOptions.value.find(dev => dev.id === selectedDevID.value))

async function fetchDeviceOptions() {
    try {
        const res = await api.getDeviceList({})
        deviceOptions.value = res.data?.data?.devicelist || []
        const devIdFromRoute = route.query.devId
        if (devIdFromRoute && deviceOptions.value.some(dev => dev.id == devIdFromRoute)) {
            selectedDevID.value = devIdFromRoute
        } else if (deviceOptions.value.length > 0 && !selectedDevID.value) {
            selectedDevID.value = deviceOptions.value[0].id
        }
    } catch (e) { deviceOptions.value = [] }
}

async function fetchVariableOptions() {
    if (!selectedDevID.value) { variableOptions.value = []; return }
    try {
        const res = await api.getvariables({ devID: selectedDevID.value })
        const allVariables = res.data?.data?.variables || []
        variableOptions.value = allVariables.filter(v => v.devID == selectedDevID.value)
        const varNameFromRoute = route.query.varName
        if (varNameFromRoute && variableOptions.value.some(v => v.varName === varNameFromRoute)) {
            selectedVarNames.value = [varNameFromRoute]
        }
    } catch (e) { variableOptions.value = [] }
}

function getTimeParams() {
    const now = new Date()
    let startTime = null
    if (timeRange.value === '1h') { startTime = new Date(now.getTime() - 60 * 60 * 1000) }
    else if (timeRange.value === '6h') { startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000) }
    else if (timeRange.value === '24h') { startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000) }
    else if (timeRange.value === 'custom' && customTimeRange.value) {
        startTime = customTimeRange.value[0]; now.setTime(customTimeRange.value[1].getTime())
    }
    return { startTime, endTime: now }
}

async function fetchTrendData() {
    if (!selectedDevID.value || selectedVarNames.value.length === 0) {
        ElMessage.warning('请选择设备和变量'); return
    }
    const dev = selectedDevice.value
    if (!dev) return
    const { startTime, endTime } = getTimeParams()
    let allSeriesData = []
    let allTimes = new Set()
    const selectedVars = variableOptions.value.filter(v => selectedVarNames.value.includes(v.varName))
    for (const v of selectedVars) {
        const params = { DevSerial: dev.serial, SlaveAddr: Number(v.modbusDevice), ModbusType: Number(v.modbusType), DataAddr: Number(v.modbusAddr) }
        try {
            const res = await api.alldata(params)
            let data = res.data?.data || []
            data.sort((a, b) => new Date(a.time || a.Time || a.TimeStr) - new Date(b.time || b.Time || b.TimeStr))
            if (startTime) { data = data.filter(d => { const t = new Date(d.time || d.Time || d.TimeStr); return t >= startTime && t <= endTime }) }
            const times = data.map(d => d.time || d.Time || d.TimeStr)
            const values = data.map(d => {
                const val = d.value ?? d.Value ?? d.Val ?? null
                if (val !== null) return parseFloat(val)
                if (d.valueFloat !== undefined && d.valueFloat !== null) return parseFloat(d.valueFloat)
                if (d.valueInt !== undefined && d.valueInt !== null) return parseInt(d.valueInt)
                return null
            })
            times.forEach(t => allTimes.add(t))
            allSeriesData.push({ name: v.varName, type: 'line', smooth: true, showSymbol: false, data: values, times })
        } catch (e) { console.error('获取趋势数据失败', v.varName, e) }
    }
    renderChart(allSeriesData, Array.from(allTimes).sort())
}

function renderChart(seriesList, times) {
    if (!trendChartRef.value) return
    if (chartInstance) chartInstance.dispose()
    chartInstance = echarts.init(trendChartRef.value)
    const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#B37FEB']
    chartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: seriesList.map(s => s.name), bottom: 30 },
        grid: { left: '3%', right: '4%', bottom: '18%', containLabel: true },
        xAxis: { type: 'category', data: times, axisLabel: { rotate: 45, fontSize: 11 } },
        yAxis: { type: 'value' },
        dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', start: 0, end: 100, height: 24, bottom: 0 }],
        series: seriesList.map((s, idx) => ({
            name: s.name, type: 'line', smooth: true, showSymbol: false,
            lineStyle: { width: 2, color: colors[idx % colors.length] },
            areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: colors[idx % colors.length] + '4D' }, { offset: 1, color: colors[idx % colors.length] + '0D' }]) },
            data: times.map(t => { const i = s.times.indexOf(t); return i !== -1 ? s.data[i] : null })
        }))
    })
    chartInstance.resize()
}

function exportImage() {
    if (!chartInstance) { ElMessage.warning('暂无图表可导出'); return }
    chartInstance.setOption({ backgroundColor: '#ffffff' })
    const url = chartInstance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' })
    const link = document.createElement('a'); link.href = url
    link.download = `趋势图_${new Date().getTime()}.png`
    document.body.appendChild(link); link.click(); document.body.removeChild(link)
    ElMessage.success('图片导出成功')
}

function onDeviceChange() { selectedVarNames.value = []; fetchVariableOptions() }
function onVarChange() { fetchTrendData() }
function onTimeRangeChange() { if (timeRange.value !== 'custom') fetchTrendData() }

onMounted(() => { fetchDeviceOptions() })
onUnmounted(() => { if (chartInstance) { chartInstance.dispose(); chartInstance = null } })
</script>
