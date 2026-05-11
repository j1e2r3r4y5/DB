<template>
    <div class="device-table-wrapper">
        <el-breadcrumb style="margin-bottom: 12px;">
            <el-breadcrumb-item>数据管理</el-breadcrumb-item>
            <el-breadcrumb-item>沙箱数据</el-breadcrumb-item>
        </el-breadcrumb>
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <el-button type="default" style="margin-right:8px;" @click="goBack">返回</el-button>
            <span style="margin-right: 8px; font-size: 14px; color: #222; font-weight: bold;">请选择设备</span>
            <el-select v-model="selectedDevID" placeholder="请选择设备" style="width:260px;">
                <el-option v-for="dev in deviceOptions" :key="dev.id" :label="`${dev.name} (${dev.serial})`"
                    :value="dev.id" />
            </el-select>
            <span v-if="selectedDevice" style="margin-left: 16px; font-size: 14px; color: #222; font-weight: bold;">
                最后在线: {{ selectedDevice.latest_online }} | 状态: {{ selectedDevice.status === '1' ? '在线' : '离线' }}
            </span>
            <el-button type="primary" size="small" style="margin-left: 24px;" @click="refresh">刷新</el-button>
        </div>

        <div style="margin-bottom: 12px; padding: 12px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px;">
            <el-icon style="color: #faad14; margin-right: 8px;"><Warning /></el-icon>
            <span style="color: #ad6b00;">沙箱数据由模拟器生成，不会影响真实设备</span>
        </div>

        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
            <el-input v-model="searchQuery" placeholder="搜索变量名..." clearable style="width: 240px;" :prefix-icon="Search" />
        </div>

        <div style="margin-bottom: 8px; font-size: 13px; color: #666;">
            <span style="margin-right: 8px;">排序：</span>
            <el-radio-group v-model="sortField" size="small">
                <el-radio-button value="">默认</el-radio-button>
                <el-radio-button value="varName">变量名</el-radio-button>
                <el-radio-button value="dataType">数据类型</el-radio-button>
                <el-radio-button value="lasttime">时间</el-radio-button>
            </el-radio-group>
            <el-switch v-model="sortAsc" style="margin-left: 12px;" active-text="升序" inactive-text="降序" size="small" />
        </div>

        <el-table ref="tableRef" :data="sortedList" style="width: 100%;"
            :header-cell-style="{ color: '#000', fontWeight: 'bold' }"
            v-loading="loading" element-loading-text="数据加载中..." virtual :item-size="50" height="500"
            :row-class-name="rowClassName">
            <el-table-column label="变量名" min-width="160">
                <template #default="scope">
                    <span>{{ scope.row.varName }}</span>
                    <el-tag size="small" type="warning" style="margin-left: 6px;">沙箱</el-tag>
                </template>
            </el-table-column>
            <el-table-column label="数据类型" min-width="100">
                <template #default="scope">{{ formatDataType(scope.row.dataType) }}</template>
            </el-table-column>
            <el-table-column label="数据值" min-width="150">
                <template #default="scope">
                    <span :class="{ 'value-updated': isUpdated(scope.row) }">{{ formatDisplayValue(scope.row) }}</span>
                </template>
            </el-table-column>
            <el-table-column label="最新上传时间" min-width="100" />
        </el-table>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, Warning } from '@element-plus/icons-vue'
import api from '../../api'
import { formatDataType } from '../../utils/datatype'
import { formatDisplayValue, getSortValue, getSandboxVariableIds } from '../../utils/dataUtils'

const router = useRouter()
const route = useRoute()
function goBack() { router.back() }

const selectedDevID = ref(null)
const deviceOptions = ref([])
const variableList = ref([])
const loading = ref(false)
const selectedDevice = computed(() => deviceOptions.value.find(dev => dev.id === selectedDevID.value))

const searchQuery = ref('')
const filteredList = computed(() => {
    if (!searchQuery.value) return variableList.value
    const q = searchQuery.value.toLowerCase()
    return variableList.value.filter(v => v.varName && v.varName.toLowerCase().includes(q))
})

const sortField = ref('')
const sortAsc = ref(true)
const sortedList = computed(() => {
    const list = [...filteredList.value]
    if (!sortField.value) return list
    list.sort((a, b) => {
        const va = getSortValue(a, sortField.value)
        const vb = getSortValue(b, sortField.value)
        const bothNumeric = typeof va === 'number' && typeof vb === 'number'
        let cmp = 0
        if (bothNumeric) { cmp = va - vb }
        else {
            const sa = String(va).toLowerCase()
            const sb = String(vb).toLowerCase()
            if (sa < sb) cmp = -1
            if (sa > sb) cmp = 1
        }
        return sortAsc.value ? cmp : -cmp
    })
    return list
})

const updatedKeys = ref(new Set())
let prevDataMap = {}
function markUpdated(newList) {
    const newMap = {}; const keys = new Set()
    newList.forEach(v => {
        const key = `${v.id || v.varName}_${v.modbusDevice}_${v.modbusAddr}`
        const val = v.data; newMap[key] = val
        if (prevDataMap[key] !== undefined && prevDataMap[key] !== val) keys.add(key)
    })
    updatedKeys.value = keys; prevDataMap = newMap
    setTimeout(() => { updatedKeys.value = new Set() }, 3000)
}
function isUpdated(row) {
    const key = `${row.id || row.varName}_${row.modbusDevice}_${row.modbusAddr}`
    return updatedKeys.value.has(key)
}
function rowClassName({ row }) { return isUpdated(row) ? 'row-updated' : '' }

async function refresh() {
    await fetchDeviceOptions()
    if (selectedDevID.value) await fetchSandboxData(selectedDevID.value)
}

function getDeviceSerial(devID) {
    const dev = deviceOptions.value.find(d => d.id == devID)
    return dev?.serial || null
}

async function fetchSandboxData(devID) {
    if (!devID) { variableList.value = []; return }
    loading.value = true
    try {
        const res = await api.getvariables({ devID })
        const allVariables = res.data?.data?.variables || []
        const sandboxVars = allVariables.filter(v => v.devID == devID && v.scope === 'sandbox')
        if (!sandboxVars.length) { variableList.value = []; loading.value = false; return }

        const groups = {}
        sandboxVars.forEach(v => {
            const slave = v.modbusDevice; const dtype = v.modbusType
            const key = `${slave}_${dtype}`
            if (!groups[key]) groups[key] = { slave, dtype, addrs: new Set(), vars: [] }
            groups[key].addrs.add(Number(v.modbusAddr)); groups[key].vars.push(v)
        })

        const DevSerial = getDeviceSerial(devID)
        if (!DevSerial) { variableList.value = sandboxVars.map(v => ({ ...v, lasttime: '-', data: '-' })); loading.value = false; return }

        const latestDataMap = {}
        for (const gk of Object.keys(groups)) {
            const g = groups[gk]
            const params = { DevSerial, SlaveAddr: Number(g.slave), ModbusType: Number(g.dtype), DataAddrs: Array.from(g.addrs) }
            try {
                const queryRes = await api.sandboxDataQuery(params)
                const resp = queryRes.data
                let latestDataArr = Array.isArray(resp) ? resp : (Array.isArray(resp?.data) ? resp.data : [])
                latestDataArr.forEach((item) => {
                    let slave = Number(item.SlaveAddr ?? item.slaveAddr ?? item.slave_addr ?? params.SlaveAddr)
                    let dtype = Number(item.DataType ?? item.dataType ?? item.data_type ?? params.ModbusType)
                    let daddr = Number(item.DataAddr ?? item.dataAddr ?? item.data_addr ?? item.addr)
                    if (Number.isNaN(slave) || Number.isNaN(dtype) || Number.isNaN(daddr)) return
                    const key = `${slave}_${dtype}_${daddr}`
                    latestDataMap[key] = {
                        time: item.Time ?? item.time ?? '-', value: item.Value ?? item.value ?? '-',
                        valueBool: item.ValueBool ?? item.valueBool, valueInt: item.ValueInt ?? item.valueInt,
                        valueFloat: item.ValueFloat ?? item.valueFloat, valueString: item.ValueString ?? item.valueString,
                        parsedValue: item.ParsedValue ?? item.parsedValue
                    }
                })
            } catch (err) { console.error('沙箱数据查询失败', gk, err) }
        }

        variableList.value = sandboxVars.map(v => {
            const key = `${Number(v.modbusDevice)}_${Number(v.modbusType)}_${Number(v.modbusAddr)}`
            const latest = latestDataMap[key] || {}
            return { ...v, lasttime: latest.time ?? '-', data: latest.value ?? '-', valueBool: latest.valueBool, valueInt: latest.valueInt, valueFloat: latest.valueFloat, valueString: latest.valueString, parsedValue: latest.parsedValue, _sortNum: parseFloat(latest.valueFloat ?? latest.valueInt ?? latest.value) }
        })
    } catch (e) { console.error('fetchSandboxData error', e); variableList.value = [] }
    loading.value = false
}

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

watch(selectedDevID, (id) => { if (id) fetchSandboxData(id) })

onMounted(() => refresh())
</script>

<style scoped>
.row-updated { animation: highlightFade 3s ease-out; }
@keyframes highlightFade {
    0% { background-color: #e6f7ff; }
    50% { background-color: #bae7ff; }
    100% { background-color: transparent; }
}
.value-updated { font-weight: bold; color: #1890ff; }
</style>
