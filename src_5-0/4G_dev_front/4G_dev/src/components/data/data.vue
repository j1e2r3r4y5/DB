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
        <el-table :data="variableList" style="width: 100%;" :header-cell-style="{ color: '#000', fontWeight: 'bold' }">
            <el-table-column prop="varName" label="变量名" min-width="120"></el-table-column>
            <el-table-column prop="data" label="数据值" min-width="100"></el-table-column>
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
import api from '../../api'
import DataDialog from './data_dialog.vue'
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
const selectedDevice = computed(() =>
    deviceOptions.value.find(dev => dev.id === selectedDevID.value)
)
const historyDialogVisible = ref(false)
const historyData = ref([])
let timer = null

// 刷新方法
async function refresh() {
    await fetchDeviceOptions()
    if (selectedDevID.value) {
        await fetchVariableList(selectedDevID.value)
    }
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
        const filteredVariables = allVariables.filter(v => v.devID == devID)

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
        console.log('fetchVariableList 分组信息:', { DevSerial, groups })

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

                latestDataArr.forEach(item => {
                    const slave = Number(item.SlaveAddr ?? item.slaveAddr ?? item.slave_addr ?? params.SlaveAddr)
                    const dtype = Number(item.DataType ?? item.dataType ?? item.data_type ?? params.ModbusType)
                    const daddr = Number(item.DataAddr ?? item.dataAddr ?? item.data_addr ?? item.addr)
                    if (Number.isNaN(slave) || Number.isNaN(dtype) || Number.isNaN(daddr)) {
                        console.warn('跳过无法解析的记录:', item)
                        return
                    }
                    const key = `${slave}_${dtype}_${daddr}`
                    latestDataMap[key] = {
                        time: item.Time ?? item.time ?? item.TimeStr ?? '-',
                        value: item.Value ?? item.value ?? item.Val ?? '-'
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
                data: latest.value ?? '-'
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
    fetchVariableList(id)
})
</script>