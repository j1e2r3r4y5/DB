<template>
    <div class="device-table-wrapper">
        <el-breadcrumb style="margin-bottom: 12px;">
            <el-breadcrumb-item>数据管理</el-breadcrumb-item>
            <el-breadcrumb-item>数据统计</el-breadcrumb-item>
        </el-breadcrumb>
        <div style="display: flex; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
            <el-button type="default" @click="goBack">返回</el-button>
            <span style="font-size: 14px; color: #222; font-weight: bold;">请选择设备</span>
            <el-select v-model="selectedDevID" placeholder="请选择设备" style="width:260px;" @change="onDeviceChange">
                <el-option v-for="dev in deviceOptions" :key="dev.id" :label="`${dev.name} (${dev.serial})`" :value="dev.id" />
            </el-select>
            <el-button type="primary" size="small" @click="refreshData">刷新</el-button>
        </div>
        <el-row :gutter="16" style="margin-bottom: 16px;">
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="变量总数" :value="stats.totalCount" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="数值型变量数" :value="stats.numericCount" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="最大值" :value="stats.max" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover"><el-statistic title="平均值" :value="stats.avg" /></el-card></el-col>
        </el-row>
        <el-row :gutter="16">
            <el-col :span="12"><div ref="pieChartRef" style="width: 100%; height: 400px;"></div></el-col>
            <el-col :span="12"><div ref="barChartRef" style="width: 100%; height: 400px;"></div></el-col>
        </el-row>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'
import * as echarts from 'echarts'
import { isNumericType } from '../../utils/datatype'

const router = useRouter()
const route = useRoute()
function goBack() { router.back() }

const selectedDevID = ref(null)
const deviceOptions = ref([])
const variableList = ref([])
const pieChartRef = ref(null)
const barChartRef = ref(null)
let pieChartInstance = null
let barChartInstance = null
let timer = null

const stats = computed(() => {
    const list = variableList.value; const totalCount = list.length
    const numericVars = list.filter(v => isNumericType(v.dataType)); const numericCount = numericVars.length
    const values = []
    numericVars.forEach(v => { const val = parseFloat(v.valueFloat ?? v.valueInt ?? v.data); if (!isNaN(val)) values.push(val) })
    const max = values.length > 0 ? Math.max(...values) : '-'
    const avg = values.length > 0 ? (values.reduce((s, v) => s + v, 0) / values.length).toFixed(2) : '-'
    return { totalCount, numericCount, max, avg }
})

const dataTypeDistribution = computed(() => {
    const map = { '0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 }
    variableList.value.forEach(v => { const dt = String(v.dataType); if (map[dt] !== undefined) map[dt]++ })
    const labels = { '0': 'BOOL', '1': 'INT16', '2': 'INT32', '3': 'FLOAT32', '4': 'FLOAT64', '5': 'STRING' }
    return Object.entries(map).filter(([, v]) => v > 0).map(([k, v]) => ({ name: labels[k] || k, value: v }))
})

const modbusGroupStats = computed(() => {
    const map = {}
    variableList.value.forEach(v => { const key = v.modbusDevice || 'unknown'; if (!map[key]) map[key] = 0; map[key]++ })
    return Object.entries(map).map(([name, value]) => ({ name: `Modbus ${name}`, value }))
})

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

async function fetchVariables() {
    if (!selectedDevID.value) { variableList.value = []; return }
    try {
        const res = await api.getvariables({ devID: selectedDevID.value })
        const allVariables = res.data?.data?.variables || []
        variableList.value = allVariables.filter(v => v.devID == selectedDevID.value)
    } catch (e) { variableList.value = [] }
}

function renderPieChart() {
    if (!pieChartRef.value) return
    if (pieChartInstance) pieChartInstance.dispose()
    pieChartInstance = echarts.init(pieChartRef.value)
    pieChartInstance.setOption({
        title: { text: '数据类型分布', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left' },
        series: [{ type: 'pie', radius: ['40%', '70%'], center: ['55%', '55%'], avoidLabelOverlap: false, itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }, label: { show: false }, emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } }, data: dataTypeDistribution.value }]
    })
    pieChartInstance.resize()
}

function renderBarChart() {
    if (!barChartRef.value) return
    if (barChartInstance) barChartInstance.dispose()
    barChartInstance = echarts.init(barChartRef.value)
    barChartInstance.setOption({
        title: { text: 'Modbus分组变量数量统计', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: modbusGroupStats.value.map(s => s.name) },
        yAxis: { type: 'value' },
        series: [{ type: 'bar', data: modbusGroupStats.value.map(s => s.value), itemStyle: { color: '#409EFF', borderRadius: [4, 4, 0, 0] }, barWidth: '50%' }]
    })
    barChartInstance.resize()
}

function renderCharts() { nextTick(() => { renderPieChart(); renderBarChart() }) }

async function refreshData() { await fetchVariables(); renderCharts() }
function onDeviceChange() { refreshData() }
function startAutoRefresh() { timer = setInterval(() => { if (selectedDevID.value) refreshData() }, 10000) }
function stopAutoRefresh() { if (timer) { clearInterval(timer); timer = null } }

onMounted(async () => { await fetchDeviceOptions(); await refreshData(); startAutoRefresh() })
onUnmounted(() => { stopAutoRefresh(); if (pieChartInstance) { pieChartInstance.dispose(); pieChartInstance = null }; if (barChartInstance) { barChartInstance.dispose(); barChartInstance = null } })
</script>
