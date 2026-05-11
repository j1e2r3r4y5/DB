<template>
    <div>
        <el-card shadow="never">
            <template #header><span style="font-weight: bold;">下发参数汇总</span></template>
            <el-row :gutter="16" style="margin-bottom: 16px;">
                <el-col :span="8">
                    <el-card shadow="never">
                        <div style="text-align: center; padding: 12px;">
                            <div style="font-size: 24px; font-weight: bold; color: #409EFF;">{{ deviceName || '-' }}</div>
                            <div style="font-size: 13px; color: #909399; margin-top: 4px;">目标设备</div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="8">
                    <el-card shadow="never">
                        <div style="text-align: center; padding: 12px;">
                            <div style="font-size: 24px; font-weight: bold; color: #67C23A;">{{ variableCount }}</div>
                            <div style="font-size: 13px; color: #909399; margin-top: 4px;">变量数量</div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="8">
                    <el-card shadow="never">
                        <div style="text-align: center; padding: 12px;">
                            <div style="font-size: 24px; font-weight: bold; color: #E6A23C;">{{ totalLength }} 字节</div>
                            <div style="font-size: 13px; color: #909399; margin-top: 4px;">总指令长度</div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
            <el-alert type="warning" show-icon :closable="false">请确认下发参数无误后，点击下方按钮进行下发操作。</el-alert>
            <div style="margin-top: 16px; text-align: right;">
                <el-button type="primary" @click="handleSend" :loading="sending">确认下发</el-button>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { computeAll } from '../../utils/modbus'

const route = useRoute()
const sending = ref(false)
const deviceName = ref('')
const variableCount = ref(0)
const totalLength = ref(0)
const devSerial = ref('')

async function loadData() {
    const devId = route.query.devId
    if (!devId) return
    try {
        const devRes = await api.getDeviceList({})
        let devList = devRes.data?.data?.devicelist || []
        const dev = devList.find(d => String(d.id) === String(devId))
        if (dev) { deviceName.value = dev.Devname || dev.name || ''; devSerial.value = dev.DevSerial || dev.serial || '' }
        const varRes = await api.getvariables({ devID: devId })
        let list = []
        if (varRes.data && varRes.data.data && varRes.data.data.variables) { list = varRes.data.data.variables }
        else if (varRes.data && Array.isArray(varRes.data.variables)) { list = varRes.data.variables }
        const vars = (list || []).map(item => ({
            id: item.iD ?? item.id ?? '', devID: item.devID ?? devId, varName: item.varName ?? '',
            dataType: item.dataType ?? '', modbusType: item.modbusType ?? '', modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '', data_len: item.data_len ?? 1, stringLen: item.stringLen ?? ''
        }))
        variableCount.value = vars.length
        totalLength.value = computeAll(vars).uploadLength
    } catch (e) { console.error('加载下发确认数据失败', e) }
}

async function handleSend() {
    if (!devSerial.value) { ElMessage.error('设备序列号不能为空'); return }
    sending.value = true
    try {
        const varRes = await api.getvariables({ devID: route.query.devId })
        let list = []
        if (varRes.data && varRes.data.data && varRes.data.data.variables) { list = varRes.data.data.variables }
        else if (varRes.data && Array.isArray(varRes.data.variables)) { list = varRes.data.variables }
        if (list.length === 0) {
            await api.downpayload({ serial: devSerial.value, code: '040003' })
        } else {
            const entries = list.map(v => ({
                SlaveAddr: Number(v.modbusDevice) || 1, DataType: Number(v.modbusType),
                StartAddr: Number(v.modbusAddr), Length: Number(v.data_len) || 1
            }))
            await api.sendDataConfig({ DevSerial: devSerial.value, scope: 'production', Entries: entries })
        }
        ElMessage.success('下发成功')
    } catch (e) { ElMessage.error('下发失败：' + (e.message || '接口异常')) }
    finally { sending.value = false }
}

onMounted(() => { loadData() })
</script>
