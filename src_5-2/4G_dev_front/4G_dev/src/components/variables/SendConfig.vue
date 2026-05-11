<template>
    <div>
        <el-breadcrumb style="margin-bottom: 16px;">
            <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
            <el-breadcrumb-item>下发配置</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card shadow="never">
            <div v-if="deviceInfo" style="margin-bottom: 16px; padding: 12px; background: #f5f7fa; border-radius: 4px;">
                <span style="font-weight: bold; margin-right: 8px;">设备信息：</span>
                <span>{{ deviceInfo.name }}</span>
                <span style="margin-left: 16px; color: #909399;">SN: {{ deviceInfo.sn }}</span>
            </div>
            <el-steps :active="activeStep" align-center style="margin-bottom: 24px;">
                <el-step title="①优化分组" description="查看分组和优化" />
                <el-step title="②HEX码" description="指令码展示" />
                <el-step title="③确认下发" description="确认并下发" />
            </el-steps>
            <el-tabs v-model="activeTab" @tab-change="onTabChange" style="margin-bottom: 16px;">
                <el-tab-pane label="优化分组" name="optimize" />
                <el-tab-pane label="HEX码" name="hex" />
                <el-tab-pane label="确认下发" name="confirm" />
                <el-tab-pane label="批量查询" name="query" />
            </el-tabs>
            <router-view />
        </el-card>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'

const router = useRouter()
const route = useRoute()

const deviceInfo = ref(null)
const activeTab = ref('optimize')

const activeStep = computed(() => {
    const path = route.path
    if (path.includes('/send/optimize')) return 0
    if (path.includes('/send/hex')) return 1
    if (path.includes('/send/confirm')) return 2
    return 0
})

function onTabChange(tab) {
    router.push({ path: `/home/variables/send/${tab}`, query: { devId: route.query.devId } })
}

async function loadDeviceInfo() {
    const devId = route.query.devId
    if (!devId) return
    try {
        const res = await api.getDeviceList({})
        let list = res.data?.data?.devicelist || []
        const dev = list.find(d => String(d.id) === String(devId))
        if (dev) {
            deviceInfo.value = { name: dev.Devname || dev.name || '', sn: dev.DevSerial || dev.serial || '' }
        }
    } catch (e) { console.error('获取设备信息失败', e) }
}

onMounted(() => { loadDeviceInfo() })
</script>
