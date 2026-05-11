<template>
    <div>
        <el-card shadow="never">
            <template #header><span style="font-weight: bold;">批量查询</span></template>
            <el-alert type="info" show-icon :closable="false" style="margin-bottom: 16px;">
                查询设备的数据配置状态，可对单个设备查询或对所有设备批量查询。
            </el-alert>
            <div style="display: flex; gap: 12px;">
                <el-button type="primary" @click="handleSingleQuery" :loading="singleLoading">查询数据配置</el-button>
                <el-button type="success" @click="handleBatchQuery" :loading="batchLoading">批量查询所有设备</el-button>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'

const route = useRoute()
const singleLoading = ref(false)
const batchLoading = ref(false)

async function handleSingleQuery() {
    const devId = route.query.devId
    if (!devId) { ElMessage.warning('请先选择设备'); return }
    singleLoading.value = true
    try {
        const res = await api.getDeviceList({})
        let list = res.data?.data?.devicelist || []
        const dev = list.find(d => String(d.id) === String(devId))
        const devSerial = dev ? (dev.DevSerial || dev.serial || '') : ''
        if (!devSerial) { ElMessage.error('未找到设备序列号'); return }
        await api.queryDataConfig({ devSerial })
        ElMessage.success('查询命令已下发')
    } catch (e) { ElMessage.error('查询失败：' + (e.message || '接口异常')) }
    finally { singleLoading.value = false }
}

async function handleBatchQuery() {
    batchLoading.value = true
    try {
        const res = await api.getDeviceList({})
        let list = res.data?.data?.devicelist || []
        let successCount = 0; let failCount = 0
        for (const dev of list) {
            const sn = dev.DevSerial || dev.serial || ''
            try { await api.queryDataConfig({ devSerial: sn }); successCount++ }
            catch (e) { failCount++ }
        }
        ElMessage.success(`批量查询完成：成功 ${successCount} 个，失败 ${failCount} 个`)
    } catch (e) { ElMessage.error('批量查询失败：' + (e.message || '接口异常')) }
    finally { batchLoading.value = false }
}
</script>
