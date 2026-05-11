<template>
    <div>
        <el-breadcrumb style="margin-bottom: 16px;">
            <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
            <el-breadcrumb-item>批量删除</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card shadow="never">
            <template #header><span style="font-weight: 600; font-size: 16px;">批量删除变量</span></template>
            <div v-if="!selectedDevID" style="text-align: center; padding: 20px; color: #909399;">
                请先在变量列表页中选择设备和要删除的变量
            </div>
            <template v-else>
                <div style="margin-bottom: 16px;">
                    <span style="font-weight: bold;">当前设备：</span>
                    <Screening v-model="selectedDevID" @update:model-value="fetchVariables" />
                </div>
                <el-table :data="displayList" style="width: 100%;" v-loading="loading" ref="tableRef"
                    @selection-change="handleSelectionChange" row-key="id" height="450" virtual :item-size="50">
                    <el-table-column type="selection" width="55" reserve-selection />
                    <el-table-column prop="varName" label="变量名" min-width="160" />
                    <el-table-column prop="dataType" label="数据类型" min-width="100" />
                    <el-table-column prop="modbusType" label="数据分区" min-width="100" />
                    <el-table-column prop="modbusDevice" label="Modbus站号" min-width="100" />
                    <el-table-column prop="modbusAddr" label="数据地址" min-width="100" />
                </el-table>
                <div style="margin-top: 16px; display: flex; align-items: center; gap: 12px;">
                    <span>已选中 <strong style="color: #f56c6c;">{{ selectedIds.size }}</strong> 个变量</span>
                    <el-button type="danger" @click="handleBatchDelete" :disabled="selectedIds.size === 0" :loading="deleting">
                        删除选中的 {{ selectedIds.size }} 个变量
                    </el-button>
                    <el-progress v-if="deleting" :percentage="deleteProgress" style="width: 200px;" />
                </div>
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
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
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
const tableRef = ref(null)
const deleteResult = ref(null)

async function fetchVariables() {
    if (!selectedDevID.value) { displayList.value = []; return }
    loading.value = true
    try {
        const res = await api.getvarbydeviceid({ deviceId: selectedDevID.value })
        let list = []
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            list = res.data.data.variables
        } else if (res.data && Array.isArray(res.data.variables)) {
            list = res.data.variables
        }
        displayList.value = (list || []).map(item => ({
            id: item.iD ?? item.id ?? '',
            devID: item.devID ?? selectedDevID.value,
            varName: item.varName ?? '',
            dataType: item.dataType ?? '',
            modbusType: item.modbusType ?? '',
            modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '',
            data_len: item.data_len ?? item.dataLen ?? '',
            stringLen: item.stringLen ?? ''
        }))
    } catch (e) { console.error('获取变量列表失败', e) }
    loading.value = false
}

function handleSelectionChange(val) {
    selectedIds.clear()
    val.forEach(v => selectedIds.add(String(v.id)))
}

async function handleBatchDelete() {
    if (selectedIds.size === 0) return
    deleting.value = true; deleteProgress.value = 0; deleteResult.value = null
    const rows = displayList.value.filter(r => selectedIds.has(String(r.id)))
    let successCount = 0; let failCount = 0
    const concurrency = 10
    try {
        for (let i = 0; i < rows.length; i += concurrency) {
            const batch = rows.slice(i, i + concurrency)
            const promises = batch.map(async (variable) => {
                try {
                    await api.deletevariable({
                        In: { id: variable.id, devID: variable.devID, varName: variable.varName,
                            dataType: variable.dataType, modbusType: variable.modbusType,
                            modbusDevice: variable.modbusDevice, modbusAddr: variable.modbusAddr,
                            data_len: variable.data_len, stringLen: variable.stringLen }
                    })
                    return { success: true }
                } catch (e) { return { success: false } }
            })
            const results = await Promise.all(promises)
            results.forEach(r => { if (r.success) successCount++; else failCount++ })
            deleteProgress.value = Math.round(((i + concurrency) / rows.length) * 100)
        }
        deleteResult.value = { successCount, failCount }
        if (failCount === 0) ElMessage.success(`批量删除成功：共 ${successCount} 个变量`)
        else ElMessage.warning(`批量删除完成：成功 ${successCount} 个，失败 ${failCount} 个`)
    } finally { deleting.value = false }
}

onMounted(() => { if (selectedDevID.value) fetchVariables() })
watch(selectedDevID, (val) => { if (val) fetchVariables() })
</script>
