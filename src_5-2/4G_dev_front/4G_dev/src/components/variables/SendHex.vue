<template>
    <div>
        <el-card shadow="never">
            <template #header><span style="font-weight: bold;">HEX 指令码</span></template>
            <el-input v-model="hexString" type="textarea" :rows="8" readonly placeholder="暂无HEX指令码，请先在优化分组页面加载变量" />
            <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: flex-end;">
                <el-button type="primary" @click="handleCopy" :disabled="!hexString">复制</el-button>
                <el-button type="success" @click="handleExport" :disabled="!hexString">导出TXT</el-button>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { computeAll, hexBytesToString } from '../../utils/modbus'

const route = useRoute()
const hexString = ref('')

async function loadHex() {
    const devId = route.query.devId
    if (!devId) return
    try {
        const res = await api.getvariables({ devID: devId })
        let list = []
        if (res.data && res.data.data && res.data.data.variables) { list = res.data.data.variables }
        else if (res.data && Array.isArray(res.data.variables)) { list = res.data.variables }
        const vars = (list || []).map(item => ({
            id: item.iD ?? item.id ?? '', devID: item.devID ?? devId, varName: item.varName ?? '',
            dataType: item.dataType ?? '', modbusType: item.modbusType ?? '', modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '', data_len: item.data_len ?? 1, stringLen: item.stringLen ?? ''
        }))
        const calc = computeAll(vars)
        hexString.value = hexBytesToString(calc.hexBytes)
    } catch (e) { console.error('获取HEX码失败', e) }
}

async function handleCopy() {
    try { await navigator.clipboard.writeText(hexString.value); ElMessage.success('已复制到剪贴板') }
    catch (e) { ElMessage.error('复制失败') }
}

function handleExport() {
    try {
        const blob = new Blob([hexString.value], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a'); link.href = url
        link.download = `HEX指令_${route.query.devId || 'unknown'}.txt`
        link.click(); URL.revokeObjectURL(url); ElMessage.success('导出成功')
    } catch (e) { ElMessage.error('导出失败') }
}

onMounted(() => { loadHex() })
</script>
