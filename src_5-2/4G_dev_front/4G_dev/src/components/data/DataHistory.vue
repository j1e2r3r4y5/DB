<template>
    <div class="device-table-wrapper">
        <el-breadcrumb style="margin-bottom: 12px;">
            <el-breadcrumb-item>数据管理</el-breadcrumb-item>
            <el-breadcrumb-item>历史数据</el-breadcrumb-item>
        </el-breadcrumb>
        <div style="display: flex; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
            <el-button type="default" @click="goBack">返回</el-button>
            <span style="font-size: 14px; color: #222; font-weight: bold;">请选择设备</span>
            <el-select v-model="selectedDevID" placeholder="请选择设备" style="width:260px;" @change="onDeviceChange">
                <el-option v-for="dev in deviceOptions" :key="dev.id" :label="`${dev.name} (${dev.serial})`" :value="dev.id" />
            </el-select>
            <span style="font-size: 14px; color: #222; font-weight: bold;">变量</span>
            <el-select v-model="selectedVarName" placeholder="请选择变量" style="width:200px;" @change="onVarChange">
                <el-option v-for="v in variableOptions" :key="v.varName" :label="v.varName" :value="v.varName" />
            </el-select>
            <span style="font-size: 14px; color: #222; font-weight: bold;">时间范围</span>
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="onDateChange" />
            <el-button type="primary" size="small" @click="fetchHistoryData">查询</el-button>
        </div>
        <div style="display: flex; gap: 16px; margin-bottom: 12px; flex-wrap: wrap;">
            <el-card shadow="hover" style="flex:1; min-width:140px;">
                <div style="font-size:13px; color:#999;">数据总量</div>
                <div style="font-size:24px; font-weight:bold;">{{ stats.totalCount }}</div>
            </el-card>
            <el-card shadow="hover" style="flex:1; min-width:140px;">
                <div style="font-size:13px; color:#999;">均值</div>
                <div style="font-size:24px; font-weight:bold;">{{ stats.avg }}</div>
            </el-card>
            <el-card shadow="hover" style="flex:1; min-width:140px;">
                <div style="font-size:13px; color:#999;">最大值</div>
                <div style="font-size:24px; font-weight:bold;">{{ stats.max }}</div>
            </el-card>
            <el-card shadow="hover" style="flex:1; min-width:140px;">
                <div style="font-size:13px; color:#999;">最小值</div>
                <div style="font-size:24px; font-weight:bold;">{{ stats.min }}</div>
            </el-card>
        </div>
        <el-table :data="pagedData" style="width: 100%;" :header-cell-style="{ color: '#000', fontWeight: 'bold' }" v-loading="loading" border>
            <el-table-column label="数据值" min-width="200">
                <template #default="scope">{{ scope.row.displayValue }}</template>
            </el-table-column>
            <el-table-column label="时间" min-width="180">
                <template #default="scope">{{ scope.row.time }}</template>
            </el-table-column>
        </el-table>
        <div style="margin-top: 12px; display: flex; justify-content: flex-end;">
            <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="historyData.length" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" />
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'
import { formatDisplayValue } from '../../utils/dataUtils'

const router = useRouter()
const route = useRoute()
function goBack() { router.back() }

const selectedDevID = ref(null)
const deviceOptions = ref([])
const variableOptions = ref([])
const selectedVarName = ref('')
const dateRange = ref(null)
const historyData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)

const selectedDevice = computed(() => deviceOptions.value.find(dev => dev.id === selectedDevID.value))
const selectedVariable = computed(() => variableOptions.value.find(v => v.varName === selectedVarName.value))

const pagedData = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    return historyData.value.slice(start, start + pageSize.value)
})

const stats = computed(() => {
    const list = historyData.value; const values = []
    list.forEach(d => {
        const val = d.valueFloat != null ? parseFloat(d.valueFloat) : (d.valueInt != null ? parseInt(d.valueInt) : (d.rawValue != null ? parseFloat(d.rawValue) : NaN))
        if (!isNaN(val)) values.push(val)
    })
    const avg = values.length > 0 ? (values.reduce((s, v) => s + v, 0) / values.length).toFixed(2) : '-'
    const max = values.length > 0 ? Math.max(...values) : '-'
    const min = values.length > 0 ? Math.min(...values) : '-'
    return { totalCount: list.length, avg, max, min }
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

async function fetchVariableOptions() {
    if (!selectedDevID.value) { variableOptions.value = []; return }
    try {
        const res = await api.getvariables({ devID: selectedDevID.value })
        const allVariables = res.data?.data?.variables || []
        variableOptions.value = allVariables.filter(v => v.devID == selectedDevID.value)
        const varNameFromRoute = route.query.varName
        if (varNameFromRoute && variableOptions.value.some(v => v.varName === varNameFromRoute)) {
            selectedVarName.value = varNameFromRoute
        }
    } catch (e) { variableOptions.value = [] }
}

async function fetchHistoryData() {
    if (!selectedDevID.value || !selectedVarName.value) { historyData.value = []; return }
    const dev = selectedDevice.value; const v = selectedVariable.value
    if (!dev || !v) return
    loading.value = true
    try {
        const params = { DevSerial: dev.serial, SlaveAddr: Number(v.modbusDevice), ModbusType: Number(v.modbusType), DataAddr: Number(v.modbusAddr) }
        const res = await api.alldata(params)
        let data = res.data?.data || []
        if (dateRange.value) {
            const start = dateRange.value[0].getTime()
            const end = dateRange.value[1].getTime() + 24 * 60 * 60 * 1000 - 1
            data = data.filter(d => { const t = new Date(d.time || d.Time || d.TimeStr).getTime(); return t >= start && t <= end })
        }
        data.sort((a, b) => new Date(b.time || b.Time || b.TimeStr) - new Date(a.time || a.Time || a.TimeStr))
        historyData.value = data.map(d => ({
            time: d.time || d.Time || d.TimeStr || '-',
            rawValue: d.value ?? d.Value ?? d.Val,
            valueBool: d.valueBool ?? d.ValueBool, valueInt: d.valueInt ?? d.ValueInt,
            valueFloat: d.valueFloat ?? d.ValueFloat, valueString: d.valueString ?? d.ValueString,
            parsedValue: d.ParsedValue ?? d.parsedValue,
            displayValue: formatDisplayValue({
                dataType: v.dataType, data: d.value ?? d.Value ?? d.Val,
                valueBool: d.valueBool ?? d.ValueBool, valueInt: d.valueInt ?? d.ValueInt,
                valueFloat: d.valueFloat ?? d.ValueFloat, valueString: d.valueString ?? d.ValueString,
                parsedValue: d.ParsedValue ?? d.parsedValue
            })
        }))
        currentPage.value = 1
    } catch (e) { console.error('获取历史数据失败', e); historyData.value = [] }
    loading.value = false
}

function onDeviceChange() { selectedVarName.value = ''; historyData.value = []; fetchVariableOptions() }
function onVarChange() { fetchHistoryData() }
function onDateChange() { fetchHistoryData() }

onMounted(() => { fetchDeviceOptions() })
</script>
