<template>
    <div class="device-table-wrapper">
        <div class="action-buttons"
            style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
            <el-button type="default" @click="goBack">返回</el-button>
            <el-button type="primary" @click="dialogVisible = true">新建变量</el-button>
            <el-button type="primary" @click="fetchVariables(selectedDevID.value)">刷新</el-button>
            <el-button type="primary" @click="handleRecoveryVariable">撤销变更</el-button>
            <el-button type="primary" @click="showFeatures = true"
                :disabled="!currentDevice">
                下发</el-button>
            <el-button type="success" @click="showImportDialog = true" :disabled="!currentDevice">
                导入变量</el-button>
            <el-button type="danger" @click="handleBatchDelete" :disabled="selectedIds.size === 0">
                批量删除{{ selectedIds.size > 0 ? `(${selectedIds.size})` : '' }}</el-button>
            <el-checkbox v-model="selectAllAcrossPages" :indeterminate="isIndeterminate" @change="toggleSelectAll" style="margin-left: 8px;">
                全选所有变量{{ displayList.length > 0 ? ` (${selectedIds.size}/${displayList.length})` : '' }}
            </el-checkbox>
        </div>

        <span v-if="currentDevice && _hasChanged"
            style="color:#e53935;font-weight:bold;">
            {{ selectedIds.size === 0 ? '将下发空配置' : '有修改操作' }}
        </span>
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span style="margin-right: 8px; font-size: 14px; color: #333;">请选择设备</span>
            <Screening v-model="selectedDevID" />
        </div>

        <!-- 虚拟滚动表格：10000+ 变量也秒开！ -->
        <el-table 
            :data="displayList" 
            style="width: 100%;" 
            v-loading="loading" 
            ref="tableRef"
            @selection-change="handleSelectionChange"
            row-key="id"
            height="550"
            virtual
            :item-size="50"
        >
            <el-table-column type="selection" width="55" reserve-selection />
            <el-table-column prop="varName" label="变量名" min-width="160">
                <template #default="scope">
                    <span>{{ scope.row.varName }}</span>
                    <el-tag v-if="scope.row.scope === 'sandbox'" size="small" type="warning" style="margin-left: 6px;">沙箱</el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="dataType" label="数据类型" min-width="100">
                <template #default="scope">
                    {{ getDataTypeLabel(scope.row.dataType) }}
                </template>
            </el-table-column>
            <el-table-column prop="modbusType" label="数据分区" min-width="100">
                <template #default="scope">
                    {{ getModbusTypeLabel(scope.row.modbusType) }}
                </template>
            </el-table-column>
            <el-table-column prop="modbusDevice" label="Modbus站号" min-width="100" />
            <el-table-column prop="modbusAddr" label="数据地址" min-width="100" />
            <el-table-column prop="stringLen" label="字符串长度" min-width="100">
                <template #default="scope">
                    {{ (!scope.row.stringLen && scope.row.stringLen !== 0) ? '-' : scope.row.stringLen }}
                </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
                <template #default="scope">
                    <el-button link class="el-btn" @click="handleEditVariable(scope.row)">编辑</el-button>
                    <el-button link class="el-btn" @click="handleDeleteClick(scope.row)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>

        <Features v-model="showFeatures" :device-id="selectedDevID" :device-sn="currentDevice?.sn"
            :variable-list="selectedRowsArray" @success="handleFeaturesSuccess" />
        <ImportVariablesDialog v-model="showImportDialog" :device-id="selectedDevID" :device-sn="currentDevice?.sn"
            @success="fetchVariables" />
        <RemoteWriteDialog v-model:visible="showRemoteWrite" :device-id="selectedDevID" :device-sn="currentDevice?.sn"
            @success="fetchVariables" />
        <Editingvar v-model="editDialogVisible" :variable="editRow" @success="fetchVariables" />
        <AddVariables v-model="dialogVisible" @success="fetchVariables" :default-dev-id="selectedDevID" />
        <el-dialog v-model="deleteDialogVisible" title="确认删除" width="320px">
            <div style="font-size:16px;">确定要删除该变量吗？</div>
            <template #footer>
                <el-button @click="deleteDialogVisible = false">取消</el-button>
                <el-button type="danger" @click="confirmDelete">删除</el-button>
            </template>
        </el-dialog>
        <el-dialog v-model="batchDeleteDialogVisible" title="确认批量删除" width="450px">
            <div v-if="!batchDeleteLoading" style="font-size: 16px;">
                确定要删除选中的 <strong style="color:#f56c6c;">{{ selectedIds.size }}</strong> 个变量吗？
            </div>
            <div v-else style="font-size: 16px;">
                正在删除... <strong>{{ batchDeleteProgress }}/{{ batchDeleteTotal }}</strong>
                <el-progress :percentage="Math.round((batchDeleteProgress / batchDeleteTotal) * 100)" style="margin-top:12px;" />
            </div>
            <div style="font-size: 13px; color:#909399; margin-top:8px;">此操作不可撤销</div>
            <template #footer>
                <el-button @click="batchDeleteDialogVisible = false" :disabled="batchDeleteLoading">取消</el-button>
                <el-button type="danger" @click="confirmBatchDelete" :loading="batchDeleteLoading" :disabled="batchDeleteLoading">
                    {{ batchDeleteLoading ? '删除中...' : '删除' }}
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, inject, watch, markRaw, nextTick } from 'vue'
const props = defineProps({ initDevId: [String, Number] })
const emit = defineEmits(['back-to-device'])

function goBack() {
    emit('back-to-device')
}
import Screening from './Screening.vue'
import api from '../../api'
import AddVariables from './addvariables.vue'
import Editingvar from './Editingvar.vue'
import Features from './Features.vue'
import RemoteWriteDialog from './RemoteWriteDialog.vue'
import ImportVariablesDialog from './ImportVariablesDialog.vue'

const showFeatures = ref(false)
const showRemoteWrite = ref(false)
const showImportDialog = ref(false)
const deviceList = inject('deviceList', ref([]))
const currentDevice = computed(() =>
    deviceList.value.find(d => String(d.id) === String(selectedDevID.value))
)
const selectedDevID = ref('1')

// 简化数据结构，减少响应式开销
let _allData = []
const displayList = ref([])

const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)
const batchDeleteDialogVisible = ref(false)
const batchDeleteLoading = ref(false)
const batchDeleteProgress = ref(0)
const batchDeleteTotal = ref(0)

// 全选跨页
const selectAllAcrossPages = ref(false)
const isIndeterminate = ref(false)
function toggleSelectAll(checked) {
    if (checked) {
        displayList.value.forEach(row => selectedIds.add(row.id))
        selectedRowsArray.value = displayList.value
        isIndeterminate.value = false
    } else {
        selectedIds.clear()
        selectedRowsArray.value = []
        isIndeterminate.value = false
    }
    // 同步表格UI
    nextTick(() => {
        if (tableRef.value) {
            pagedList.value.forEach(row => {
                tableRef.value.toggleRowSelection(row, selectedIds.has(row.id), false)
            })
        }
    })
}

// 全选逻辑优化（虚拟滚动）
function onSelectionChange() {
    nextTick(() => {
        if (tableRef.value && selectedIds.size > 0) {
            // 保持选择状态（虚拟滚动需要）
        }
    })
}

// 静态映射，避免每次都重新创建
const dataTypeMap = markRaw({
    '0': '布尔值',
    '1': 'int16',
    '2': 'int32',
    '3': 'float32',
    '4': 'float64',
    '5': '字符串'
})
const modbusTypeMap = markRaw({
    '0': '0区 线圈 (Coils)',
    '1': '1区 离散输入 (Discrete Inputs)',
    '3': '3区 输入寄存器 (Input Registers)',
    '4': '4区 保持寄存器 (Holding Registers)'
})

// 简单的格式化函数
function getDataTypeLabel(val) {
    return dataTypeMap[val] || val || '-'
}
function getModbusTypeLabel(val) {
    return modbusTypeMap[val] || val || '-'
}

// 删除相关
async function confirmDelete() {
    if (!deleteTarget.value) return
    try {
        await api.deletevariable({
            In: {
                id: deleteTarget.value.id,
                devID: deleteTarget.value.devID,
                varName: deleteTarget.value.varName,
                dataType: deleteTarget.value.dataType,
                modbusType: deleteTarget.value.modbusType,
                modbusDevice: deleteTarget.value.modbusDevice,
                modbusAddr: deleteTarget.value.modbusAddr,
                data_len: deleteTarget.value.data_len,
                stringLen: deleteTarget.value.stringLen,
            }
        })
        if (window.ElMessage) window.ElMessage.success('删除成功')
        fetchVariables()
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('删除失败')
    }
    deleteDialogVisible.value = false
    deleteTarget.value = null
}

const editDialogVisible = ref(false)
const editRow = ref(null)

function handleEditVariable(row) {
    editRow.value = { ...row }
    editDialogVisible.value = true
}

function handleDeleteClick(row) {
    deleteTarget.value = row
    deleteDialogVisible.value = true
}

function handleBatchDelete() {
    if (selectedIds.size === 0) return
    batchDeleteDialogVisible.value = true
}

async function confirmBatchDelete() {
    if (selectedIds.size === 0) return
    
    const rows = displayList.value.filter(r => selectedIds.has(r.id))
    batchDeleteTotal.value = rows.length
    batchDeleteProgress.value = 0
    batchDeleteLoading.value = true
    
    let successCount = 0
    let failCount = 0
    const concurrency = 10 // 增大并发数，提高速度
    
    try {
        // 并发删除，带进度更新
        for (let i = 0; i < rows.length; i += concurrency) {
            const batch = rows.slice(i, i + concurrency)
            const promises = batch.map(async (variable) => {
                try {
                    await api.deletevariable({
                        In: {
                            id: variable.id,
                            devID: variable.devID,
                            varName: variable.varName,
                            dataType: variable.dataType,
                            modbusType: variable.modbusType,
                            modbusDevice: variable.modbusDevice,
                            modbusAddr: variable.modbusAddr,
                            data_len: variable.data_len,
                            stringLen: variable.stringLen,
                        }
                    })
                    return { success: true }
                } catch (e) {
                    return { success: false }
                }
            })
            
            const results = await Promise.all(promises)
            results.forEach(r => {
                if (r.success) successCount++
                else failCount++
            })
            
            // 减少UI更新频率
            batchDeleteProgress.value = Math.min(i + concurrency, rows.length)
        }
        
        if (failCount === 0) {
            if (window.ElMessage) window.ElMessage.success(`批量删除成功：共 ${successCount} 个变量`)
        } else {
            if (window.ElMessage) window.ElMessage.warning(`批量删除完成：成功 ${successCount} 个，失败 ${failCount} 个`)
        }
        
        // 清空选中状态
        selectedIds.clear()
        selectedRowsArray.value = []
        fetchVariables()
    } finally {
        batchDeleteLoading.value = false
        batchDeleteDialogVisible.value = false
    }
}

// 数据加载
const loading = ref(false)
const dialogVisible = ref(false)
let deviceListFetched = false

async function fetchDeviceListOnce() {
    if (deviceListFetched && deviceList.value && deviceList.value.length > 0) {
        return
    }
    try {
        const deviceRes = await api.getDeviceList()
        let rawList = []
        if (deviceRes.data && deviceRes.data.data && Array.isArray(deviceRes.data.data.devicelist)) {
            rawList = deviceRes.data.data.devicelist
        } else if (deviceRes.data && Array.isArray(deviceRes.data.devicelist)) {
            rawList = deviceRes.data.devicelist
        }
        deviceList.value = rawList.map(item => ({
            id: item.id,
            sn: item.DevSerial || item.serial || '',
            chengeFlag: item.chengeFlag ?? 0,
            successFlag: item.successFlag ?? 0
        }))
        deviceListFetched = true
    } catch (e) {
        console.error('获取设备列表失败:', e)
    }
}

async function fetchVariables(devId) {
    loading.value = true
    try {
        let res
        if (devId) {
            res = await api.getvarbydeviceid({ deviceId: devId })
        } else {
            res = await api.getvariables({})
        }
        let list = []
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            list = res.data.data.variables
        } else if (res.data && Array.isArray(res.data.variables)) {
            list = res.data.variables
        }
        if (devId) {
            _allData = (list || []).map(item => markRaw({
                id: item.iD ?? item.id ?? '',
                devID: item.devID ?? devId,
                varName: item.varName ?? '',
                dataType: item.dataType ?? '',
                modbusType: item.modbusType ?? '',
                modbusDevice: item.modbusDevice ?? '',
                modbusAddr: item.modbusAddr ?? '',
                data_len: item.data_len ?? item.dataLen ?? '',
                stringLen: item.stringLen ?? '',
                decimalDigits: item.decimalDigits ?? '',
                scope: item.scope ?? 'production'
            }))
        } else {
            _allData = (list || []).map(item => markRaw({
                id: item.iD ?? item.id ?? '',
                devID: item.devID ?? '',
                varName: item.varName ?? '',
                dataType: item.dataType ?? '',
                modbusType: item.modbusType ?? '',
                modbusDevice: item.modbusDevice ?? '',
                modbusAddr: item.modbusAddr ?? '',
                data_len: item.data_len ?? item.dataLen ?? '',
                stringLen: item.stringLen ?? '',
                decimalDigits: item.decimalDigits ?? '',
                scope: item.scope ?? 'production'
            }))
        }
        updateDisplayList()
        await fetchDeviceListOnce()
    } catch (e) {
        _allData = []
        updateDisplayList()
        console.error('获取变量列表失败:', e)
    }
    loading.value = false
}

async function fetchVariablesByDevId(devId) {
    if (!devId) {
        _allData = []
        updateDisplayList()
        return
    }
    loading.value = true
    try {
        const res = await api.getvarbydeviceid({ deviceId: devId })
        let list = []
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            list = res.data.data.variables
        } else if (res.data && Array.isArray(res.data.variables)) {
            list = res.data.variables
        }
        _allData = (list || []).map(item => markRaw({
            id: item.iD ?? item.id ?? '',
            devID: item.devID ?? devId,
            varName: item.varName ?? '',
            dataType: item.dataType ?? '',
            modbusType: item.modbusType ?? '',
            modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '',
            data_len: item.data_len ?? item.dataLen ?? '',
            stringLen: item.stringLen ?? '',
            decimalDigits: item.decimalDigits ?? '',
            scope: item.scope ?? 'production'
        }))
        updateDisplayList()
        await fetchDeviceListOnce()
    } catch (e) {
        _allData = []
        updateDisplayList()
        console.error('获取变量列表失败:', e)
    }
    loading.value = false
}

// 更新显示列表，只在必要时重新计算
function updateDisplayList() {
    const filtered = _allData.filter(v => String(v.devID) === String(selectedDevID.value))
    filtered.sort((a, b) => {
        // 正常变量排前面，沙箱变量排后面
        const scopeA = a.scope === 'sandbox' ? 1 : 0
        const scopeB = b.scope === 'sandbox' ? 1 : 0
        if (scopeA !== scopeB) return scopeA - scopeB
        const deviceA = Number(a.modbusDevice) || 0
        const deviceB = Number(b.modbusDevice) || 0
        if (deviceA !== deviceB) return deviceA - deviceB
        const typeA = Number(a.modbusType) || 0
        const typeB = Number(b.modbusType) || 0
        if (typeA !== typeB) return typeA - typeB
        const addrA = Number(a.modbusAddr) || 0
        const addrB = Number(b.modbusAddr) || 0
        return addrA - addrB
    })
    displayList.value = filtered
    page.value = 1
}

// 选择管理：用 Set 代替数组，速度更快
const selectedIds = new Set()
const selectedRowsArray = ref([])
const tableRef = ref(null)
let selectionTimeout = null

// 防抖处理选择变化，跨分页维护选中状态
function handleSelectionChange(val) {
    if (selectionTimeout) {
        clearTimeout(selectionTimeout)
    }
    selectionTimeout = setTimeout(() => {
        // 获取当前页所有行的ID
        const currentPageIds = new Set(pagedList.value.map(r => r.id))
        // 移除当前页中所有已选的
        for (const id of currentPageIds) {
            selectedIds.delete(id)
        }
        // 重新添加当前页勾选的
        val.forEach(v => selectedIds.add(v.id))
        selectedRowsArray.value = val
        // 同步全选状态
        const total = displayList.value.length
        const selected = selectedIds.size
        selectAllAcrossPages.value = total > 0 && selected === total
        isIndeterminate.value = selected > 0 && selected < total
    }, 50)
}

// Payload 变化检测 - 极度简化
let _lastSavedIds = null
let _lastDeviceId = null
const _hasChanged = ref(false)

function loadLastSavedIds(deviceId) {
    if (_lastDeviceId === deviceId && _lastSavedIds !== null) {
        return _lastSavedIds
    }
    try {
        const data = localStorage.getItem(`activeVariables_${deviceId}`)
        _lastSavedIds = data ? new Set(JSON.parse(data)) : new Set()
    } catch {
        _lastSavedIds = new Set()
    }
    _lastDeviceId = deviceId
    return _lastSavedIds
}

function saveSelectedIds(deviceId, ids) {
    try {
        const idArr = Array.from(ids)
        localStorage.setItem(`activeVariables_${deviceId}`, JSON.stringify(idArr))
        _lastSavedIds = ids
        _lastDeviceId = deviceId
    } catch {
    }
}

// 比较两个 Set 是否相等
function setsEqual(a, b) {
    if (a.size !== b.size) return false
    for (const id of a) {
        if (!b.has(id)) return false
    }
    return true
}

// 计算变化 - 监听响应式的 selectedRowsArray
watch([selectedDevID, selectedRowsArray], () => {
    if (!currentDevice.value) {
        _hasChanged.value = false
        return
    }
    const last = loadLastSavedIds(currentDevice.value.id)
    const current = new Set(selectedRowsArray.value.map(v => String(v.id)))
    _hasChanged.value = !setsEqual(last, current)
}, { immediate: true })

// 下发成功处理
async function handleFeaturesSuccess(variables) {
    await fetchVariables(selectedDevID.value)
    if (currentDevice.value) {
        const ids = new Set((variables || []).map(v => String(v.id)))
        saveSelectedIds(currentDevice.value.id, ids)
        _hasChanged.value = false
        // 恢复选择状态
        if (tableRef.value && tableRef.value.toggleRowSelection) {
            displayList.value.forEach(row => {
                if (ids.has(row.id)) {
                    tableRef.value.toggleRowSelection(row, true)
                }
            })
        }
    }
}

// 回溯变量
async function handleRecoveryVariable() {
    if (!currentDevice.value) {
        if (window.ElMessage) window.ElMessage.warning('请先选择设备')
        return
    }
    try {
        await api.recoveryvariable({
            devID: currentDevice.value.id,
        })
        if (window.ElMessage) window.ElMessage.success('回溯成功')
        fetchVariables(selectedDevID.value)
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('回溯失败')
    }
}

// 设备切换处理 - 简化，避免重复请求
let isLoading = false
let lastInitDevId = null

watch(
    () => props.initDevId,
    (val) => {
        if (val && val !== lastInitDevId && !isLoading) {
            lastInitDevId = val
            selectedDevID.value = String(val)
            isLoading = true
            fetchVariablesByDevId(val).finally(() => {
                isLoading = false
            })
        }
    }
)

watch(selectedDevID, (val, oldVal) => {
    if (!val || val === oldVal || isLoading) return
    isLoading = true
    fetchVariables(val).finally(() => {
        isLoading = false
    })
})

onMounted(() => {
    if (!isLoading) {
        isLoading = true
        if (props.initDevId) {
            lastInitDevId = props.initDevId
            selectedDevID.value = String(props.initDevId)
            fetchVariables(props.initDevId).finally(() => {
                isLoading = false
            })
        } else if (deviceList.value.length > 0) {
            selectedDevID.value = String(deviceList.value[0].id)
            fetchVariables(deviceList.value[0].id).finally(() => {
                isLoading = false
            })
        } else {
            isLoading = false
        }
    }
})
</script>

<style scoped>
.el-btn {
    color: #409EFF !important;
    font-weight: bold;
}
</style>
