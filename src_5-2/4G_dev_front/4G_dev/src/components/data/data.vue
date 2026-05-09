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

        <el-table :data="variableList" style="width: 100%;" :header-cell-style="{ color: '#000', fontWeight: 'bold' }">
            <el-table-column label="变量名" min-width="160">
                <template #default="scope">
                    <span>{{ scope.row.varName }}</span>
                    <el-tag v-if="scope.row.scope === 'sandbox' || activeTab === 'sandbox'" size="small" type="warning" style="margin-left: 6px;">🧪 沙箱</el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="dataType" label="数据类型" min-width="100">
                <template #default="scope">
                    {{ formatDataType(scope.row.dataType) }}
                </template>
            </el-table-column>
            <el-table-column label="数据值" min-width="150">
                <template #default="scope">
                    {{ formatDisplayValue(scope.row) }}
                </template>
            </el-table-column>
            <el-table-column prop="lasttime" label="最新上传时间" min-width="100"></el-table-column>
            <el-table-column label="操作" min-width="100">
                <template #default="scope">
                    <el-button type="primary" size="small" @click="showHistory(scope.row)">
                        历史数据
                    </el-button>
                </template>
            </el-table-column>
        </el-table>
        <data-dialog v-model="historyDialogVisible" :history-data="historyData" />
    </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import api from '../../api'
import DataDialog from './data_dialog.vue'
import { formatDataType, DataType } from '../../utils/datatype'
const props = defineProps({
    devId: {
        type: [String, Number],
        default: null
    }
})
const emit = defineEmits(['back-to-devlist'])
function goBack() {
    emit('back-to-devlist')
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

// 判断是否有活跃变量
const hasActiveVariables = computed(() => {
    if (!selectedDevID.value) return null
    const activeIds = getActiveVariableIds(selectedDevID.value)
    return activeIds !== null
})

// 格式化显示值
function formatDisplayValue(row) {
    const dataType = String(row.dataType)
    
    // 优先使用解析后的值
    if (dataType === DataType.BOOL && row.valueBool !== undefined && row.valueBool !== null) {
        return row.valueBool ? 'true' : 'false'
    }
    if (dataType === DataType.STRING && row.valueString) {
        return row.valueString
    }
    if ((dataType === DataType.FLOAT32 || dataType === DataType.FLOAT64) && 
        row.valueFloat !== undefined && row.valueFloat !== null) {
        // 修复浮点数显示问题 - 格式化浮点数
        const val = Number(row.valueFloat)
        if (!isNaN(val)) {
            // 检查是否接近整数
            if (Math.abs(val - Math.round(val)) < 0.0000001) {
                return Math.round(val)
            }
            // 固定显示6位小数
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
    
    // 回退到原始值
    return row.data ?? '-'
}

// 刷新方法
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

// 获取设备序列号
function getDeviceSerial(devID) {
    const dev = deviceOptions.value.find(d => d.id == devID)
    return dev?.serial || null
}

// 获取沙箱变量ID列表
function getSandboxVariableIds(deviceId) {
    if (!deviceId) return []
    try {
        const data = localStorage.getItem(`importedVariables_${deviceId}`)
        return data ? JSON.parse(data) : []
    } catch {
        return []
    }
}

// 获取沙箱变量数据
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
                parsedValue: latest.parsedValue
            }
        })
    } catch (e) {
        console.error('fetchSandboxData error', e)
        variableList.value = []
    }
    loading.value = false
}

// 自动刷新
function startAutoRefresh() {
    timer = setInterval(() => {
        refresh()
    }, 5000) // 5秒
}
function stopAutoRefresh() {
    if (timer) clearInterval(timer)
}

// 获取设备列表
async function fetchDeviceOptions() {
    try {
        const res = await api.getDeviceList({})
        deviceOptions.value = res.data?.data?.devicelist || []
        // 外部传入devId时自动选中
        if (props.devId && deviceOptions.value.some(dev => dev.id == props.devId)) {
            selectedDevID.value = props.devId
        } else if (deviceOptions.value.length > 0 && !selectedDevID.value) {
            selectedDevID.value = deviceOptions.value[0].id
        }
    } catch (e) {
        deviceOptions.value = []
    }
}

// 获取变量列表并查最新数据（按 SlaveAddr+ModbusType 分组，批量传 DataAddrs）
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

        // 如果不是显示所有变量，过滤出活跃变量
        if (!showAllVariables.value) {
            const activeIds = getActiveVariableIds(devID)
            console.log('[数据管理] 过滤变量:', {
                devID,
                allVariablesCount: filteredVariables.length,
                activeIds,
                allVariableIds: filteredVariables.map(v => ({ id: v.id, iD: v.iD, name: v.varName }))
            })
            if (activeIds !== null) {
                filteredVariables = filteredVariables.filter(v => {
                    const match = activeIds.includes(String(v.id)) || activeIds.includes(String(v.iD))
                    return match
                })
            }
            console.log('[数据管理] 过滤后变量数:', filteredVariables.length)
        }

        if (!filteredVariables.length) {
            variableList.value = []
            loading.value = false
            return
        }

        // 按 slave+type 分组，收集每组的地址列表
        const groups = {} // key => { slave, type, addrs: Set, vars: [variable] }
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
        console.log('fetchVariableList 分组信息:', { DevSerial, groups, showAll: showAllVariables.value })

        // 存放所有返回的最新数据，key = slave_type_addr
        const latestDataMap = {}

        // 顺序请求每组（可以并行，但保持简单可靠）
        const groupKeys = Object.keys(groups)
        for (const gk of groupKeys) {
            const g = groups[gk]
            const params = {
                DevSerial,
                SlaveAddr: Number(g.slave),
                ModbusType: Number(g.dtype),
                DataAddrs: Array.from(g.addrs)
            }
            console.log('按组批量查询参数:', params)
            try {
                const queryRes = await api.dataquery(params)
                const resp = queryRes.data
                // 兼容后端返回：{code,msg,data: [...] } 或直接数组
                let latestDataArr = []
                if (Array.isArray(resp)) latestDataArr = resp
                else if (Array.isArray(resp?.data)) latestDataArr = resp.data
                else latestDataArr = []
                console.log('组查询返回:', gk, latestDataArr)

                // 先按照请求的数据地址顺序建立映射
                const addrIndexMap = new Map()
                params.DataAddrs.forEach((addr, idx) => {
                    addrIndexMap.set(addr, idx)
                })
                
                latestDataArr.forEach((item, arrIdx) => {
                    let slave = Number(item.SlaveAddr ?? item.slaveAddr ?? item.slave_addr ?? params.SlaveAddr)
                    let dtype = Number(item.DataType ?? item.dataType ?? item.data_type ?? params.ModbusType)
                    let daddr = Number(item.DataAddr ?? item.dataAddr ?? item.data_addr ?? item.addr)
                    
                    // 如果 daddr 是 NaN，尝试根据返回顺序匹配请求的 DataAddrs
                    if (Number.isNaN(daddr) && arrIdx < params.DataAddrs.length) {
                        daddr = params.DataAddrs[arrIdx]
                        console.warn('数据缺少地址字段，尝试根据返回顺序匹配:', item, '→', daddr)
                    }
                    
                    if (Number.isNaN(slave) || Number.isNaN(dtype) || Number.isNaN(daddr)) {
                        console.warn('跳过无法解析的记录:', item)
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

        // 将 latestDataMap 映射回变量列表
        variableList.value = filteredVariables.map(v => {
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
                parsedValue: latest.parsedValue
            }
        })
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
// 监听外部devId变化，自动切换设备并刷新
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