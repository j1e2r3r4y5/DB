<template>
    <div class="device-table-wrapper">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <el-button type="default" style="margin-right:8px; margin-bottom: 12px;" @click="goBack">返回</el-button>
            <span style="margin-right: 8px; font-size: 14px; color: #222; font-weight: bold;">请选择设备</span>
            <el-select v-model="selectedDevID" placeholder="请选择设备" style="width:260px;">
                <el-option v-for="dev in deviceOptions" :key="dev.id" :label="`${dev.name} (${dev.serial})`"
                    :value="dev.id" />
            </el-select>
            <span v-if="selectedDevice" style="margin-left: 16px; font-size: 14px; color: #222; font-weight: bold;">
                最后在线: {{ selectedDevice.latest_online }} | 状态: {{ selectedDevice.status === '1' ? '在线' : '离线' }}
            </span>
            <el-button type="primary" size="small" style="margin-left: 24px;" @click="refresh">
                刷新
            </el-button>
        </div>

        <el-tabs v-model="activeTab" style="margin-bottom: 12px;">
            <el-tab-pane label="真实数据" name="production">
                <div v-if="!showAllVariables && hasActiveVariables === false" style="margin-bottom: 12px; padding: 12px; background: #fff7e6; border: 1px solid #ffd591; border-radius: 4px;">
                    <el-icon style="color: #fa9d3b; margin-right: 8px;"><Warning /></el-icon>
                    <span style="color: #874a00;">还没有下发变量配置，请先去变量管理页面下发配置</span>
                </div>
                <el-checkbox v-model="showAllVariables" style="margin-bottom: 12px;" @change="refresh">
                    显示所有变量
                </el-checkbox>
            </el-tab-pane>
            <el-tab-pane label="沙箱数据" name="sandbox">
                <div style="margin-bottom: 12px; padding: 12px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px;">
                    <el-icon style="color: #faad14; margin-right: 8px;"><Warning /></el-icon>
                    <span style="color: #ad6b00;">沙箱数据由模拟器生成，不会影响真实设备</span>
                </div>
            </el-tab-pane>
        </el-tabs>

        <!-- 工具栏：搜索 + 导出 + 统计 -->
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
            <el-input
                v-model="searchQuery"
                placeholder="搜索变量名..."
                clearable
                style="width: 240px;"
                :prefix-icon="Search"
            />
            <el-button type="success" size="small" @click="handleExport">
                导出TXT
            </el-button>
            <el-button size="small" @click="showStats = !showStats">
                {{ showStats ? '隐藏统计' : '显示统计' }}
            </el-button>
        </div>

        <!-- 统计信息 -->
        <el-collapse-transition>
            <div v-if="showStats" style="margin-bottom: 12px; padding: 12px; background: #f0f9ff; border: 1px solid #b3d8ff; border-radius: 6px;">
                <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                    <div><strong>变量总数:</strong> {{ stats.totalCount }}</div>
                    <div><strong>数值型变量:</strong> {{ stats.numericCount }}</div>
                    <div v-if="stats.min !== null"><strong>最小值:</strong> {{ stats.min }}</div>
                    <div v-if="stats.max !== null"><strong>最大值:</strong> {{ stats.max }}</div>
                    <div v-if="stats.avg !== null"><strong>平均值:</strong> {{ stats.avg }}</div>
                    <div v-if="stats.lastUpdate !== '-'"><strong>最后更新:</strong> {{ stats.lastUpdate }}</div>
                </div>
            </div>
        </el-collapse-transition>

        <!-- 排序控制 -->
        <div style="margin-bottom: 8px; font-size: 13px; color: #666;">
            <span style="margin-right: 8px;">排序：</span>
            <el-radio-group v-model="sortField" size="small">
                <el-radio-button value="">默认</el-radio-button>
                <el-radio-button value="varName">变量名</el-radio-button>
                <el-radio-button value="dataType">数据类型</el-radio-button>
                <el-radio-button value="lasttime">时间</el-radio-button>
            </el-radio-group>
            <el-switch
                v-model="sortAsc"
                style="margin-left: 12px;"
                active-text="升序"
                inactive-text="降序"
                size="small"
            />
        </div>

        <!-- 虚拟滚动表格 -->
        <el-table
            ref="tableRef"
            :data="sortedList"
            style="width: 100%;"
            :header-cell-style="{ color: '#000', fontWeight: 'bold' }"
            v-loading="loading"
            element-loading-text="数据加载中..."
            virtual
            :item-size="50"
            height="500"
            :row-class-name="rowClassName"
        >
            <el-table-column label="变量名" min-width="160">
                <template #default="scope">
                    <span>{{ scope.row.varName }}</span>
                    <el-tag v-if="scope.row.scope === 'sandbox' || activeTab === 'sandbox'" size="small" type="warning" style="margin-left: 6px;">🧪 沙箱</el-tag>
                </template>
            </el-table-column>
            <el-table-column label="数据类型" min-width="100">
                <template #default="scope">
                    {{ formatDataType(scope.row.dataType) }}
                </template>
            </el-table-column>
            <el-table-column label="数据值" min-width="150">
                <template #default="scope">
                    <span :class="{ 'value-updated': isUpdated(scope.row) }">
                        {{ formatDisplayValue(scope.row) }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="最新上传时间" min-width="100"></el-table-column>
            <el-table-column label="趋势图" min-width="100">
                <template #default="scope">
                    <el-button type="primary" size="small" @click="showTrend(scope.row)">
                        趋势图
                    </el-button>
                </template>
            </el-table-column>
            <el-table-column label="历史数据" min-width="100">
                <template #default="scope">
                    <el-button type="default" size="small" @click="showHistory(scope.row)">
                        历史
                    </el-button>
                </template>
            </el-table-column>
        </el-table>
        <data-dialog v-model="historyDialogVisible" :history-data="historyData" />

        <!-- 趋势图弹窗 -->
        <el-dialog v-model="trendDialogVisible" :title="`趋势图 - ${trendVarName}`" width="800px" @opened="initTrendChart" @closed="disposeTrendChart">
            <div ref="trendChartRef" style="width: 100%; height: 400px;"></div>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Warning } from '@element-plus/icons-vue'
import api from '../../api'
import DataDialog from './data_dialog.vue'
import { formatDataType, DataType, isNumericType } from '../../utils/datatype'
import * as echarts from 'echarts'

const props = defineProps({
    devId: {
        type: [String, Number],
        default: null
    }
})
const router = useRouter()
function goBack() {
    router.back()
}
const selectedDevID = ref(null)
const deviceOptions = ref([])
const variableList = ref([])
const loading = ref(false)
const showAllVariables = ref(false)
const activeTab = ref('production')
const selectedDevice = computed(() =>
    deviceOptions.value.find(dev => dev.id === selectedDevID.value)
)
const historyDialogVisible = ref(false)
const historyData = ref([])
let timer = null

// 搜索筛选
const searchQuery = ref('')
const filteredList = computed(() => {
    if (!searchQuery.value) return variableList.value
    const q = searchQuery.value.toLowerCase()
    return variableList.value.filter(v =>
        v.varName && v.varName.toLowerCase().includes(q)
    )
})

// 排序
const sortField = ref('')
const sortAsc = ref(true)
function getSortValue(row, field) {
    if (field === 'varName') return (row.varName || '').toLowerCase()
    if (field === 'dataType') return Number(row.dataType) || 0
    if (field === 'lasttime') {
        const t = row.lasttime || ''
        if (!t || t === '-') return ''
        try {
            const d = new Date(t.replace(/-/g, '/'))
            return isNaN(d.getTime()) ? t : d.getTime()
        } catch { return t }
    }
    if (field === 'data') {
        if (row._sortNum !== undefined) return row._sortNum
        const parsed = parseFloat(row.valueFloat ?? row.valueInt ?? row.data)
        return isNaN(parsed) ? (row.data || '') : parsed
    }
    return ''
}
const sortedList = computed(() => {
    const list = [...filteredList.value]
    if (!sortField.value) return list
    list.sort((a, b) => {
        const va = getSortValue(a, sortField.value)
        const vb = getSortValue(b, sortField.value)
        const bothNumeric = typeof va === 'number' && typeof vb === 'number'
        let cmp = 0
        if (bothNumeric) {
            cmp = va - vb
        } else {
            const sa = String(va).toLowerCase()
            const sb = String(vb).toLowerCase()
            if (sa < sb) cmp = -1
            if (sa > sb) cmp = 1
        }
        return sortAsc.value ? cmp : -cmp
    })
    return list
})

// 统计信息
const showStats = ref(false)
const stats = computed(() => {
    const list = filteredList.value
    const totalCount = list.length
    const numericVars = list.filter(v => isNumericType(v.dataType))
    const numericCount = numericVars.length
    const values = []
    numericVars.forEach(v => {
        const val = parseFloat(v.valueFloat ?? v.valueInt ?? v.data)
        if (!isNaN(val)) values.push(val)
    })
    const min = values.length > 0 ? Math.min(...values) : null
    const max = values.length > 0 ? Math.max(...values) : null
    const avg = values.length > 0 ? (values.reduce((s, v) => s + v, 0) / values.length).toFixed(2) : null
    const times = list.map(v => v.lasttime).filter(t => t && t !== '-')
    const lastUpdate = times.length > 0 ? times.sort().reverse()[0] : '-'
    return { totalCount, numericCount, min, max, avg, lastUpdate }
})

// 更新高亮
const updatedKeys = ref(new Set())
let prevDataMap = {}
function markUpdated(newList) {
    const newMap = {}
    const keys = new Set()
    newList.forEach(v => {
        const key = `${v.id || v.varName}_${v.modbusDevice}_${v.modbusAddr}`
        const val = v.data
        newMap[key] = val
        if (prevDataMap[key] !== undefined && prevDataMap[key] !== val) {
            keys.add(key)
        }
    })
    updatedKeys.value = keys
    prevDataMap = newMap
    setTimeout(() => {
        updatedKeys.value = new Set()
    }, 3000)
}
function isUpdated(row) {
    const key = `${row.id || row.varName}_${row.modbusDevice}_${row.modbusAddr}`
    return updatedKeys.value.has(key)
}
function rowClassName({ row }) {
    return isUpdated(row) ? 'row-updated' : ''
}

// 趋势图
const trendDialogVisible = ref(false)
const trendVarName = ref('')
const trendChartRef = ref(null)
let trendChartInstance = null
const trendVarData = ref(null)

async function showTrend(variable) {
    trendVarName.value = variable.varName
    trendVarData.value = variable
    trendDialogVisible.value = true
}

async function initTrendChart() {
    await nextTick()
    if (!trendChartRef.value || !trendVarData.value) return
    const v = trendVarData.value
    const params = {
        DevSerial: selectedDevice.value?.serial,
        SlaveAddr: v.modbusDevice,
        ModbusType: v.modbusType,
        DataAddr: v.modbusAddr
    }
    try {
        const res = await api.alldata(params)
        const data = res.data?.data || []
        const times = data.map(d => d.time || d.Time || '').reverse()
        const values = data.map(d => {
            const val = d.value ?? d.Value ?? d.Val ?? null
            if (val !== null) return parseFloat(val)
            if (d.valueFloat !== undefined && d.valueFloat !== null) return parseFloat(d.valueFloat)
            if (d.valueInt !== undefined && d.valueInt !== null) return parseInt(d.valueInt)
            return null
        }).reverse()
        if (trendChartInstance) trendChartInstance.dispose()
        trendChartInstance = echarts.init(trendChartRef.value)
        trendChartInstance.setOption({
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const p = params[0]
                    if (!p) return ''
                    return `${p.axisValue}<br/>${p.seriesName}: ${p.value}`
                }
            },
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
            xAxis: {
                type: 'category',
                data: times,
                axisLabel: { rotate: 45, fontSize: 11 }
            },
            yAxis: {
                type: 'value'
            },
            dataZoom: [
                { type: 'inside', start: 0, end: 100 },
                { type: 'slider', start: 0, end: 100, height: 24, bottom: 0 }
            ],
            series: [{
                name: v.varName,
                type: 'line',
                smooth: true,
                showSymbol: false,
                lineStyle: { width: 2, color: '#409EFF' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(64,158,255,0.3)' },
                        { offset: 1, color: 'rgba(64,158,255,0.05)' }
                    ])
                },
                data: values
            }]
        })
        trendChartInstance.resize()
    } catch (e) {
        console.error('获取趋势图数据失败', e)
    }
}

function disposeTrendChart() {
    if (trendChartInstance) {
        trendChartInstance.dispose()
        trendChartInstance = null
    }
}

// 导出TXT
function handleExport() {
    const list = filteredList.value
    if (list.length === 0) {
        ElMessage.warning('没有数据可导出')
        return
    }
    const now = new Date()
    const timestamp = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`
    let content = `# 数据导出 - ${timestamp}\n`
    content += `# 设备: ${selectedDevice.value?.name || ''} (${selectedDevice.value?.serial || ''})\n`
    content += `# 变量总数: ${list.length}\n`
    content += '# 格式: 变量名 | 数据类型 | 数据值 | 时间\n'
    content += '#\n'
    list.forEach(v => {
        const varName = v.varName || '-'
        const dtype = formatDataType(v.dataType)
        const value = formatDisplayValue(v)
        const time = v.lasttime || '-'
        content += `${varName} | ${dtype} | ${value} | ${time}\n`
    })
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `data_export_${selectedDevice.value?.serial || 'unknown'}_${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
}

// 读取当前设备的活跃变量ID列表
function getActiveVariableIds(deviceId) {
    if (!deviceId) return null
    try {
        const data = localStorage.getItem(`activeVariables_${deviceId}`)
        return data ? JSON.parse(data) : null
    } catch {
        return null
    }
}

const hasActiveVariables = computed(() => {
    if (!selectedDevID.value) return null
    const activeIds = getActiveVariableIds(selectedDevID.value)
    return activeIds !== null
})

function formatDisplayValue(row) {
    const dataType = String(row.dataType)
    if (dataType === DataType.BOOL && row.valueBool !== undefined && row.valueBool !== null) {
        return row.valueBool ? 'true' : 'false'
    }
    if (dataType === DataType.STRING && row.valueString) {
        return row.valueString
    }
    if ((dataType === DataType.FLOAT32 || dataType === DataType.FLOAT64) && 
        row.valueFloat !== undefined && row.valueFloat !== null) {
        const val = Number(row.valueFloat)
        if (!isNaN(val)) {
            if (Math.abs(val - Math.round(val)) < 0.0000001) {
                return Math.round(val)
            }
            return val.toFixed(6)
        }
        return row.valueFloat
    }
    if ((dataType === DataType.INT16 || dataType === DataType.INT32) && 
        row.valueInt !== undefined && row.valueInt !== null) {
        return row.valueInt
    }
    if (row.parsedValue !== undefined && row.parsedValue !== null) {
        return row.parsedValue
    }
    return row.data ?? '-'
}

async function refresh() {
    await fetchDeviceOptions()
    if (selectedDevID.value) {
        if (activeTab.value === 'sandbox') {
            await fetchSandboxData(selectedDevID.value)
        } else {
            await fetchVariableList(selectedDevID.value)
        }
    }
}

function getDeviceSerial(devID) {
    const dev = deviceOptions.value.find(d => d.id == devID)
    return dev?.serial || null
}

function getSandboxVariableIds(deviceId) {
    if (!deviceId) return []
    try {
        const data = localStorage.getItem(`importedVariables_${deviceId}`)
        return data ? JSON.parse(data) : []
    } catch {
        return []
    }
}

async function fetchSandboxData(devID) {
    if (!devID) {
        variableList.value = []
        return
    }
    loading.value = true
    try {
        const res = await api.getvariables({ devID })
        const allVariables = res.data?.data?.variables || []
        const sandboxVars = allVariables.filter(v => v.devID == devID && v.scope === 'sandbox')

        if (!sandboxVars.length) {
            variableList.value = []
            loading.value = false
            return
        }

        const groups = {}
        sandboxVars.forEach(v => {
            const slave = v.modbusDevice
            const dtype = v.modbusType
            const addr = v.modbusAddr
            const key = `${slave}_${dtype}`
            if (!groups[key]) groups[key] = { slave, dtype, addrs: new Set(), vars: [] }
            groups[key].addrs.add(Number(addr))
            groups[key].vars.push(v)
        })

        const DevSerial = getDeviceSerial(devID)
        if (!DevSerial) {
            variableList.value = sandboxVars.map(v => ({ ...v, lasttime: '-', data: '-' }))
            loading.value = false
            return
        }

        const latestDataMap = {}
        const groupKeys = Object.keys(groups)
        for (const gk of groupKeys) {
            const g = groups[gk]
            const params = {
                DevSerial,
                SlaveAddr: Number(g.slave),
                ModbusType: Number(g.dtype),
                DataAddrs: Array.from(g.addrs)
            }
            try {
                const queryRes = await api.sandboxDataQuery(params)
                const resp = queryRes.data
                let latestDataArr = []
                if (Array.isArray(resp)) latestDataArr = resp
                else if (Array.isArray(resp?.data)) latestDataArr = resp.data
                else latestDataArr = []

                latestDataArr.forEach((item) => {
                    let slave = Number(item.SlaveAddr ?? item.slaveAddr ?? item.slave_addr ?? params.SlaveAddr)
                    let dtype = Number(item.DataType ?? item.dataType ?? item.data_type ?? params.ModbusType)
                    let daddr = Number(item.DataAddr ?? item.dataAddr ?? item.data_addr ?? item.addr)
                    if (Number.isNaN(slave) || Number.isNaN(dtype) || Number.isNaN(daddr)) return
                    const key = `${slave}_${dtype}_${daddr}`
                    latestDataMap[key] = {
                        time: item.Time ?? item.time ?? '-',
                        value: item.Value ?? item.value ?? '-',
                        valueBool: item.ValueBool ?? item.valueBool,
                        valueInt: item.ValueInt ?? item.valueInt,
                        valueFloat: item.ValueFloat ?? item.valueFloat,
                        valueString: item.ValueString ?? item.valueString,
                        parsedValue: item.ParsedValue ?? item.parsedValue
                    }
                })
            } catch (err) {
                console.error('沙箱数据查询失败', gk, err)
            }
        }

        variableList.value = sandboxVars.map(v => {
            const key = `${Number(v.modbusDevice)}_${Number(v.modbusType)}_${Number(v.modbusAddr)}`
            const latest = latestDataMap[key] || {}
            return {
                ...v,
                lasttime: latest.time ?? '-',
                data: latest.value ?? '-',
                valueBool: latest.valueBool,
                valueInt: latest.valueInt,
                valueFloat: latest.valueFloat,
                valueString: latest.valueString,
                parsedValue: latest.parsedValue,
                _sortNum: parseFloat(latest.valueFloat ?? latest.valueInt ?? latest.value)
            }
        })
    } catch (e) {
        console.error('fetchSandboxData error', e)
        variableList.value = []
    }
    loading.value = false
}

function startAutoRefresh() {
    timer = setInterval(() => {
        if (selectedDevID.value && !loading.value) {
            if (activeTab.value === 'sandbox') {
                fetchSandboxData(selectedDevID.value)
            } else {
                fetchVariableList(selectedDevID.value)
            }
        }
    }, 3000)
}
function stopAutoRefresh() {
    if (timer) clearInterval(timer)
}

async function fetchDeviceOptions() {
    try {
        const res = await api.getDeviceList({})
        deviceOptions.value = res.data?.data?.devicelist || []
        if (props.devId && deviceOptions.value.some(dev => dev.id == props.devId)) {
            selectedDevID.value = props.devId
        } else if (deviceOptions.value.length > 0 && !selectedDevID.value) {
            selectedDevID.value = deviceOptions.value[0].id
        }
    } catch (e) {
        deviceOptions.value = []
    }
}

async function fetchVariableList(devID) {
    if (!devID) {
        variableList.value = []
        return
    }
    loading.value = true
    try {
        const res = await api.getvariables({ devID })
        const allVariables = res.data?.data?.variables || []
        let filteredVariables = allVariables.filter(v => v.devID == devID && v.scope !== 'sandbox')

        if (!showAllVariables.value) {
            const activeIds = getActiveVariableIds(devID)
            if (activeIds !== null) {
                filteredVariables = filteredVariables.filter(v => {
                    const match = activeIds.includes(String(v.id)) || activeIds.includes(String(v.iD))
                    return match
                })
            }
        }

        if (!filteredVariables.length) {
            variableList.value = []
            loading.value = false
            return
        }

        const groups = {}
        filteredVariables.forEach(v => {
            const slave = v.modbusDevice
            const dtype = v.modbusType
            const addr = v.modbusAddr
            const key = `${slave}_${dtype}`
            if (!groups[key]) groups[key] = { slave, dtype, addrs: new Set(), vars: [] }
            groups[key].addrs.add(Number(addr))
            groups[key].vars.push(v)
        })

        const DevSerial = selectedDevice.value?.serial
        const latestDataMap = {}

        const groupKeys = Object.keys(groups)
        for (const gk of groupKeys) {
            const g = groups[gk]
            const params = {
                DevSerial,
                SlaveAddr: Number(g.slave),
                ModbusType: Number(g.dtype),
                DataAddrs: Array.from(g.addrs)
            }
            try {
                const queryRes = await api.dataquery(params)
                const resp = queryRes.data
                let latestDataArr = []
                if (Array.isArray(resp)) latestDataArr = resp
                else if (Array.isArray(resp?.data)) latestDataArr = resp.data
                else latestDataArr = []

                const addrIndexMap = new Map()
                params.DataAddrs.forEach((addr, idx) => {
                    addrIndexMap.set(addr, idx)
                })
                
                latestDataArr.forEach((item, arrIdx) => {
                    let slave = Number(item.SlaveAddr ?? item.slaveAddr ?? item.slave_addr ?? params.SlaveAddr)
                    let dtype = Number(item.DataType ?? item.dataType ?? item.data_type ?? params.ModbusType)
                    let daddr = Number(item.DataAddr ?? item.dataAddr ?? item.data_addr ?? item.addr)
                    
                    if (Number.isNaN(daddr) && arrIdx < params.DataAddrs.length) {
                        daddr = params.DataAddrs[arrIdx]
                    }
                    
                    if (Number.isNaN(slave) || Number.isNaN(dtype) || Number.isNaN(daddr)) {
                        return
                    }
                    
                    const key = `${slave}_${dtype}_${daddr}`
                    latestDataMap[key] = {
                        time: item.Time ?? item.time ?? item.TimeStr ?? '-',
                        value: item.Value ?? item.value ?? item.Val ?? '-',
                        valueBool: item.ValueBool ?? item.valueBool ?? item.value_bool,
                        valueInt: item.ValueInt ?? item.valueInt ?? item.value_int,
                        valueFloat: item.ValueFloat ?? item.valueFloat ?? item.value_float,
                        valueString: item.ValueString ?? item.valueString ?? item.value_string,
                        parsedValue: item.ParsedValue ?? item.parsedValue
                    }
                })
            } catch (err) {
                console.error('按组查询失败', gk, err)
            }
        }

        const newList = filteredVariables.map(v => {
            const key = `${Number(v.modbusDevice)}_${Number(v.modbusType)}_${Number(v.modbusAddr)}`
            const latest = latestDataMap[key] || {}
            return {
                ...v,
                lasttime: latest.time ?? '-',
                data: latest.value ?? '-',
                valueBool: latest.valueBool,
                valueInt: latest.valueInt,
                valueFloat: latest.valueFloat,
                valueString: latest.valueString,
                parsedValue: latest.parsedValue,
                _sortNum: parseFloat(latest.valueFloat ?? latest.valueInt ?? latest.value)
            }
        })

        markUpdated(newList)
        variableList.value = newList
    } catch (e) {
        console.error('fetchVariableList error', e)
        variableList.value = []
    }
    loading.value = false
}

async function showHistory(variable) {
    historyDialogVisible.value = true
    const params = {
        DevSerial: selectedDevice.value.serial,
        SlaveAddr: variable.modbusDevice,
        ModbusType: variable.modbusType,
        DataAddr: variable.modbusAddr
    }
    const res = await api.alldata(params)
    historyData.value = res.data?.data || []
}

onMounted(() => {
    refresh()
    startAutoRefresh()
})
onUnmounted(stopAutoRefresh)
watch(() => props.devId, (newId) => {
    if (newId && deviceOptions.value.some(dev => dev.id == newId)) {
        selectedDevID.value = newId
        fetchVariableList(newId)
    }
})
watch(selectedDevID, (id) => {
    if (activeTab.value === 'sandbox') {
        fetchSandboxData(id)
    } else {
        fetchVariableList(id)
    }
})
watch(activeTab, () => {
    refresh()
})
</script>

<style scoped>
.row-updated {
    animation: highlightFade 3s ease-out;
}

@keyframes highlightFade {
    0% { background-color: #e6f7ff; }
    50% { background-color: #bae7ff; }
    100% { background-color: transparent; }
}

.value-updated {
    font-weight: bold;
    color: #1890ff;
}
</style>
