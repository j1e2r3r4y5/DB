<template>
    <div class="device-table-wrapper">
        <el-breadcrumb style="margin-bottom: 12px;">
            <el-breadcrumb-item>数据管理</el-breadcrumb-item>
            <el-breadcrumb-item>数据导出</el-breadcrumb-item>
        </el-breadcrumb>
        <div style="display: flex; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
            <el-button type="default" @click="goBack">返回</el-button>
            <span style="font-size: 14px; color: #222; font-weight: bold;">请选择设备</span>
            <el-select v-model="selectedDevID" placeholder="请选择设备" style="width:260px;" @change="onDeviceChange">
                <el-option v-for="dev in deviceOptions" :key="dev.id" :label="`${dev.name} (${dev.serial})`" :value="dev.id" />
            </el-select>
            <span style="font-size: 14px; color: #222; font-weight: bold;">导出格式</span>
            <el-radio-group v-model="exportFormat">
                <el-radio value="TXT">TXT</el-radio>
                <el-radio value="CSV">CSV</el-radio>
                <el-radio value="JSON">JSON</el-radio>
            </el-radio-group>
        </div>
        <div v-if="variableOptions.length > 0" style="margin-bottom: 12px;">
            <span style="font-size: 14px; color: #222; font-weight: bold; margin-right: 12px;">筛选变量</span>
            <el-checkbox-group v-model="selectedVars">
                <el-checkbox v-for="v in variableOptions" :key="v.id || v.varName" :label="v.varName" />
            </el-checkbox-group>
        </div>
        <div style="margin-bottom: 12px;">
            <el-button type="primary" @click="handleExport" :disabled="totalCount === 0">导出</el-button>
            <span style="margin-left: 12px; font-size: 13px; color: #999;">共 {{ totalCount }} 条数据</span>
            <span v-if="totalCount > 20" style="margin-left: 8px; font-size: 13px; color: #999;">（预览前20条）</span>
        </div>
        <el-table :data="previewData" style="width: 100%;" :header-cell-style="{ color: '#000', fontWeight: 'bold' }" border max-height="500">
            <el-table-column prop="varName" label="变量名" min-width="140" />
            <el-table-column prop="dataTypeLabel" label="数据类型" min-width="100" />
            <el-table-column prop="displayValue" label="数据值" min-width="150" />
            <el-table-column prop="time" label="时间" min-width="160" />
        </el-table>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { formatDataType } from '../../utils/datatype'
import { formatDisplayValue } from '../../utils/dataUtils'

const router = useRouter()
const route = useRoute()
function goBack() { router.back() }

const selectedDevID = ref(null)
const deviceOptions = ref([])
const variableOptions = ref([])
const selectedVars = ref([])
const exportFormat = ref('TXT')
const allData = ref([])

const selectedDevice = computed(() => deviceOptions.value.find(dev => dev.id === selectedDevID.value))

const filteredData = computed(() => {
    let list = allData.value
    if (selectedVars.value.length > 0) {
        list = list.filter(item => selectedVars.value.includes(item.varName))
    }
    return list
})
const previewData = computed(() => filteredData.value.slice(0, 20))
const totalCount = computed(() => filteredData.value.length)

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
    if (!selectedDevID.value) { variableOptions.value = []; return }
    try {
        const res = await api.getvariables({ devID: selectedDevID.value })
        const allVariables = res.data?.data?.variables || []
        variableOptions.value = allVariables.filter(v => v.devID == selectedDevID.value)
    } catch (e) { variableOptions.value = [] }
}

async function fetchLatestData() {
    if (!selectedDevID.value || !variableOptions.value.length) { allData.value = []; return }
    const dev = selectedDevice.value
    if (!dev) return
    const groups = {}
    variableOptions.value.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groups[key]) groups[key] = { slave: v.modbusDevice, dtype: v.modbusType, addrs: new Set(), vars: [] }
        groups[key].addrs.add(Number(v.modbusAddr)); groups[key].vars.push(v)
    })
    const list = []
    for (const gk of Object.keys(groups)) {
        const g = groups[gk]
        const params = { DevSerial: dev.serial, SlaveAddr: Number(g.slave), ModbusType: Number(g.dtype), DataAddrs: Array.from(g.addrs) }
        try {
            const queryRes = await api.dataquery(params)
            const resp = queryRes.data
            const dataArr = Array.isArray(resp) ? resp : (Array.isArray(resp?.data) ? resp.data : [])
            dataArr.forEach((item) => {
                const daddr = Number(item.DataAddr ?? item.dataAddr ?? item.data_addr ?? item.addr)
                const v = g.vars.find(x => Number(x.modbusAddr) === daddr)
                if (v) {
                    list.push({
                        varName: v.varName, dataTypeLabel: formatDataType(v.dataType), dataType: v.dataType,
                        displayValue: formatDisplayValue({ ...v, data: item.value ?? item.Value ?? item.Val, valueBool: item.valueBool ?? item.ValueBool, valueInt: item.valueInt ?? item.ValueInt, valueFloat: item.valueFloat ?? item.ValueFloat, valueString: item.valueString ?? item.ValueString, parsedValue: item.ParsedValue ?? item.parsedValue }),
                        time: item.Time ?? item.time ?? item.TimeStr ?? '-'
                    })
                }
            })
        } catch (err) { console.error('按组查询失败', gk, err) }
    }
    allData.value = list
}

async function onDeviceChange() {
    selectedVars.value = []
    await fetchVariables()
    await fetchLatestData()
}

function handleExport() {
    const list = filteredData.value
    if (list.length === 0) { ElMessage.warning('没有数据可导出'); return }
    let content, mimeType, ext
    const now = new Date()
    const ts = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}`
    const serial = selectedDevice.value?.serial || 'unknown'
    if (exportFormat.value === 'TXT') {
        const header = `# 数据导出 - ${now.toLocaleString()}\n# 设备: ${selectedDevice.value?.name || ''} (${serial})\n# 格式: 变量名 | 数据类型 | 数据值 | 时间\n#\n`
        content = header + list.map(item => `${item.varName} | ${item.dataTypeLabel} | ${item.displayValue} | ${item.time}`).join('\n')
        mimeType = 'text/plain;charset=utf-8'; ext = 'txt'
    } else if (exportFormat.value === 'CSV') {
        content = '\uFEFF变量名,数据类型,数据值,时间\n' + list.map(item => `"${item.varName}","${item.dataTypeLabel}","${item.displayValue}","${item.time}"`).join('\n')
        mimeType = 'text/csv;charset=utf-8'; ext = 'csv'
    } else {
        content = JSON.stringify(list.map(item => ({ varName: item.varName, dataType: item.dataTypeLabel, value: item.displayValue, time: item.time })), null, 2)
        mimeType = 'application/json;charset=utf-8'; ext = 'json'
    }
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = `data_export_${serial}_${ts}.${ext}`
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
}

onMounted(() => { fetchDeviceOptions() })
</script>
