<template>
    <div>
        <el-card shadow="never" style="margin-bottom: 16px;">
            <template #header><span style="font-weight: bold;">变量列表</span></template>
            <el-table :data="variableList" style="width: 100%;" v-loading="loading" border max-height="300">
                <el-table-column prop="varName" label="变量名" min-width="140" />
                <el-table-column prop="modbusDevice" label="站号" width="80" />
                <el-table-column label="分区" width="120">
                    <template #default="scope">{{ getModbusTypeLabel(scope.row.modbusType) }}</template>
                </el-table-column>
                <el-table-column prop="modbusAddr" label="地址" width="80" />
                <el-table-column label="数量" width="80">
                    <template #default="scope">{{ scope.row.data_len || 1 }} {{ getQuantityUnit(scope.row.modbusType) }}</template>
                </el-table-column>
            </el-table>
        </el-card>
        <el-card shadow="never" style="margin-bottom: 16px;" v-if="result">
            <template #header><span style="font-weight: bold;">优化前后对比</span></template>
            <el-alert type="success" show-icon :closable="false">
                <div style="font-size: 14px; line-height: 1.8;">
                    <div>分组总数：<strong>{{ result.groupDetails.length }}</strong></div>
                    <div>寄存器总数：<strong>{{ result.totalRegisterCount }}</strong></div>
                    <div>实际需要寄存器：<strong>{{ result.actualNeededCount }}</strong></div>
                    <div v-if="result.overheadPercent > 0" style="color: #f56c6c;">额外读取比例：<strong>{{ result.overheadPercent }}%</strong></div>
                    <div>上传报文长度：<strong>{{ result.uploadLength }}</strong> 字节</div>
                </div>
            </el-alert>
            <div v-if="optimizationResult" style="margin-top: 16px;">
                <el-alert type="info" show-icon :closable="false">
                    <div>优化器：<strong>{{ optimizationResult.optimizerUsed }}</strong></div>
                    <div v-if="optimizationResult.executionTimeMs != null">耗时：<strong>{{ optimizationResult.executionTimeMs }}ms</strong></div>
                </el-alert>
            </div>
        </el-card>
        <div style="margin-top: 16px; text-align: right;">
            <el-button type="primary" @click="handleOptimize" :loading="optimizing">开始优化</el-button>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api'
import { computeAll, getModbusTypeLabel, getQuantityUnit, hexBytesToString } from '../../utils/modbus'

const route = useRoute()
const variableList = ref([])
const loading = ref(false)
const optimizing = ref(false)
const result = ref(null)
const optimizationResult = ref(null)

async function loadVariables() {
    const devId = route.query.devId
    if (!devId) return
    loading.value = true
    try {
        const res = await api.getvariables({ devID: devId })
        let list = []
        if (res.data && res.data.data && res.data.data.variables) { list = res.data.data.variables }
        else if (res.data && Array.isArray(res.data.variables)) { list = res.data.variables }
        variableList.value = (list || []).map(item => ({
            id: item.iD ?? item.id ?? '', devID: item.devID ?? devId, varName: item.varName ?? '',
            dataType: item.dataType ?? '', modbusType: item.modbusType ?? '', modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '', data_len: item.data_len ?? 1, stringLen: item.stringLen ?? ''
        }))
        result.value = computeAll(variableList.value)
    } catch (e) { console.error('获取变量列表失败', e) }
    finally { loading.value = false }
}

async function handleOptimize() {
    const devId = route.query.devId
    if (!devId || !variableList.value.length) return
    optimizing.value = true
    try {
        const res = await api.getDeviceList({})
        let list = res.data?.data?.devicelist || []
        const dev = list.find(d => String(d.id) === String(devId))
        const devSerial = dev ? (dev.DevSerial || dev.serial || '') : ''
        const entries = variableList.value.map(v => ({
            SlaveAddr: Number(v.modbusDevice) || 1, DataType: Number(v.modbusType),
            StartAddr: Number(v.modbusAddr), Length: Number(v.data_len) || 1
        }))
        const optRes = await api.sendDataConfig({ DevSerial: devSerial, scope: 'production', Entries: entries })
        const respData = optRes.data && optRes.data.data ? optRes.data.data : null
        if (respData) {
            optimizationResult.value = { optimizerUsed: respData.optimizerUsed || 'DefaultOptimizer', executionTimeMs: respData.executionTimeMs }
        }
    } catch (e) { console.error('优化失败', e) }
    finally { optimizing.value = false }
}

onMounted(() => { loadVariables() })
</script>
