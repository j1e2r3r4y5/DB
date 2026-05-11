<template>
    <div>
        <el-breadcrumb style="margin-bottom: 16px;">
            <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
            <el-breadcrumb-item>远程置数</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card shadow="never" style="max-width: 560px;">
            <template #header><span style="font-weight: 600; font-size: 16px;">远程置数</span></template>
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <span style="font-weight: bold;">设备：</span>
                <Screening v-model="deviceId" @update:model-value="onDeviceChange" />
                <span v-if="!deviceId" style="color: #f56c6c; font-size: 13px;">请先选择设备</span>
            </div>
            <el-form :model="form" label-width="120px">
                <el-form-item label="功能码">
                    <el-select v-model="form.func">
                        <el-option label="06 写单个寄存器" :value="6" />
                        <el-option label="15 写多个线圈" :value="15" />
                        <el-option label="16 写多个寄存器" :value="16" />
                    </el-select>
                </el-form-item>
                <el-form-item label="类型">
                    <el-select v-model="form.type">
                        <el-option label="0区 线圈" :value="0" />
                        <el-option label="4区 保持寄存器" :value="4" />
                    </el-select>
                </el-form-item>
                <el-form-item label="起始地址">
                    <el-input-number v-model="form.startAddr" :min="0" />
                </el-form-item>
                <el-form-item label="数量">
                    <el-input-number v-model="form.count" :min="1" />
                </el-form-item>
                <el-form-item label="数据（逗号分隔）">
                    <el-input type="textarea" v-model="form.dataStr" placeholder="例如: 1,0,1 或 100,200" :rows="4" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="submit" :loading="loading" :disabled="!deviceId">下发</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import Screening from './Screening.vue'
import api from '../../api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const deviceId = ref(route.query.devId || '')

const form = ref({ func: 6, type: 4, startAddr: 0, count: 1, dataStr: '' })

function onDeviceChange() {
    router.replace({ query: { ...route.query, devId: deviceId.value } })
}

async function submit() {
    if (!deviceId.value) { ElMessage.error('请先选择设备'); return }
    const parts = (form.value.dataStr || '').split(',').map(s => s.trim()).filter(s => s !== '')
    if (parts.length !== form.value.count) { ElMessage.warning('数据数量需等于指定的数量'); return }
    let values = []
    if (form.value.type === 0) {
        let byte = 0; let bitIndex = 0
        for (const p of parts) {
            const bit = (p === '1' || p.toLowerCase() === 'true') ? 1 : 0
            byte |= (bit << bitIndex); bitIndex++
            if (bitIndex === 8) { values.push(byte); byte = 0; bitIndex = 0 }
        }
        if (bitIndex > 0) values.push(byte)
    } else {
        for (const p of parts) {
            const n = Number(p)
            if (!Number.isFinite(n)) { ElMessage.warning(`无效的数字: ${p}`); return }
            values.push((n >> 8) & 0xff); values.push(n & 0xff)
        }
    }
    loading.value = true
    try {
        await api.remoteWrite({
            devId: deviceId.value, func: form.value.func, dataType: form.value.type,
            startAddr: form.value.startAddr, quantity: form.value.count, values
        })
        ElMessage.success('下发成功')
    } catch (e) { ElMessage.error('下发失败：' + (e.message || '接口异常')) }
    finally { loading.value = false }
}
</script>
