<template>
    <div>
        <el-breadcrumb style="margin-bottom: 16px;">
            <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
            <el-breadcrumb-item>批量删除</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card shadow="never">
            <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 16px;">批量删除变量</span>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <span style="font-weight: bold;">设备：</span>
                        <Screening v-model="selectedDevID" @update:model-value="fetchVariables" />
                    </div>
                </div>
            </template>
            <div v-if="!selectedDevID" style="text-align: center; padding: 40px; color: #909399;">
                <div style="font-size: 16px;">请先选择设备</div>
            </div>
            <template v-else>
                <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center;">
                    <el-checkbox v-model="selectAll" :indeterminate="isIndeterminate" @change="handleSelectAll">
                        全选所有变量（{{ displayList.length }} 个）
                    </el-checkbox>
                    <el-button type="danger" @click="handleBatchDelete" :disabled="selectedIds.size === 0" :loading="deleting">
                        删除选中的 {{ selectedIds.size }} 个变量
                    </el-button>
                    <el-progress v-if="deleting" :percentage="deleteProgress" style="width: 200px;" />
                </div>
                <el-table 
                    :data="displayList" 
                    style="width: 100%;" 
                    v-loading="loading" 
                    ref="tableRef"
                    @selection-change="handleSelectionChange"
                    row-key="id"
                    height="600"
                    border
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
                    <el-table-column label="操作" width="100" fixed="right">
                        <template #default="scope">
                            <el-button link type="danger" @click="handleDeleteSingle(scope.row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <div v-if="deleteResult" style="margin-top: 16px;">
                    <el-alert :type="deleteResult.failCount === 0 ? 'success' : 'warning'" show-icon :closable="false">
                        删除完成：成功 {{ deleteResult.successCount }} 个，失败 {{ deleteResult.failCount }} 个
                    </el-alert>
                </div>
            </template>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Screening from './Screening.vue'
import api from '../../api'

const router = useRouter()
const route = useRoute()

const selectedDevID = ref(route.query.devId || '')
const displayList = ref([])
const loading = ref(false)
const deleting = ref(false)
const deleteProgress = ref(0)
const selectedIds = new Set()
const selectedRowsArray = ref([])
const tableRef = ref(null)
const deleteResult = ref(null)
const selectAll = ref(false)
const isIndeterminate = ref(false)

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

function getDataTypeLabel(val) {
    return dataTypeMap[val] || val || '-'
}
function getModbusTypeLabel(val) {
    return modbusTypeMap[val] || val || '-'
}

async function fetchVariables() {
    if (!selectedDevID.value) {
        displayList.value = []
        return
    }
    loading.value = true
    try {
        const res = await api.getvarbydeviceid({ deviceId: selectedDevID.value })
        let list = []
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            list = res.data.data.variables
        } else if (res.data && Array.isArray(res.data.variables)) {
            list = res.data.variables
        }
        displayList.value = (list || []).map(item => markRaw({
            id: item.iD ?? item.id ?? '',
            devID: item.devID ?? selectedDevID.value,
            varName: item.varName ?? '',
            dataType: item.dataType ?? '',
            modbusType: item.modbusType ?? '',
            modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '',
            data_len: item.data_len ?? item.dataLen ?? '',
            stringLen: item.stringLen ?? '',
            scope: item.scope ?? 'production'
        })).sort((a, b) => {
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
        // 清空选择状态
        selectedIds.clear()
        selectedRowsArray.value = []
        selectAll.value = false
        isIndeterminate.value = false
        deleteResult.value = null
    } catch (e) {
        console.error('获取变量列表失败', e)
        ElMessage.error('获取变量列表失败')
    } finally {
        loading.value = false
    }
}

function handleSelectionChange(val) {
    selectedRowsArray.value = val
    selectedIds.clear()
    val.forEach(v => selectedIds.add(String(v.id)))
    
    const total = displayList.value.length
    const selected = selectedIds.size
    selectAll.value = total > 0 && selected === total
    isIndeterminate.value = selected > 0 && selected < total
}

function handleSelectAll(checked) {
    if (checked) {
        displayList.value.forEach(row => selectedIds.add(String(row.id)))
        selectedRowsArray.value = [...displayList.value]
        selectAll.value = true
        isIndeterminate.value = false
    } else {
        selectedIds.clear()
        selectedRowsArray.value = []
        selectAll.value = false
        isIndeterminate.value = false
    }
}

async function handleDeleteSingle(row) {
    try {
        await ElMessageBox.confirm(
            `确定要删除变量 "${row.varName}" 吗？`,
            '确认删除',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }
        )
        await api.deletevariable({
            In: {
                id: row.id,
                devID: row.devID,
                varName: row.varName,
                dataType: row.dataType,
                modbusType: row.modbusType,
                modbusDevice: row.modbusDevice,
                modbusAddr: row.modbusAddr,
                data_len: row.data_len,
                stringLen: row.stringLen,
            }
        })
        ElMessage.success('删除成功')
        fetchVariables()
    } catch (e) {
        if (e !== 'cancel') {
            ElMessage.error('删除失败')
        }
    }
}

async function handleBatchDelete() {
    if (selectedIds.size === 0) {
        ElMessage.warning('请先选择要删除的变量')
        return
    }
    
    try {
        await ElMessageBox.confirm(
            `确定要删除选中的 ${selectedIds.size} 个变量吗？此操作不可撤销。`,
            '确认批量删除',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }
        )
    } catch (e) {
        return
    }
    
    deleting.value = true
    deleteProgress.value = 0
    deleteResult.value = null
    
    const rows = displayList.value.filter(r => selectedIds.has(String(r.id)))
    let successCount = 0
    let failCount = 0
    const concurrency = 10
    
    try {
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
            deleteProgress.value = Math.round(((i + concurrency) / rows.length) * 100)
        }
        
        deleteResult.value = { successCount, failCount }
        
        if (failCount === 0) {
            ElMessage.success(`批量删除成功：共 ${successCount} 个变量`)
        } else {
            ElMessage.warning(`批量删除完成：成功 ${successCount} 个，失败 ${failCount} 个`)
        }
        
        // 刷新列表
        fetchVariables()
    } catch (e) {
        console.error('批量删除失败', e)
        ElMessage.error('批量删除失败')
    } finally {
        deleting.value = false
    }
}

onMounted(() => {
    if (selectedDevID.value) {
        fetchVariables()
    }
})

watch(selectedDevID, (val) => {
    if (val) {
        fetchVariables()
    } else {
        displayList.value = []
        selectedIds.clear()
        selectedRowsArray.value = []
    }
})
</script>
