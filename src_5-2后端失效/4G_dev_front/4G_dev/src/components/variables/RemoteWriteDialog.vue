<template>
    <el-dialog v-model:visible="localVisible" title="远程置数" width="560px">
        <el-form :model="form" label-width="120px">
            <el-form-item label="功能码">
                <el-select v-model="form.func" placeholder="选择功能码">
                    <el-option label="06 单寄存器写" :value="6" />
                </el-select>
            </el-form-item>
            <el-form-item label="类型">
                <el-select v-model="form.type" placeholder="选择类型">
                    <!-- 标准 Modbus 协议分区定义 -->
                    <!-- 0区: 线圈 (Coils) - 功能码 0x05 (写单个线圈) -->
                    <el-option label="0区 线圈 (Coils)" :value="0" />
                    <!-- 4区: 保持寄存器 (Holding Registers) - 功能码 0x06 (写单个寄存器) -->
                    <el-option label="4区 保持寄存器 (Holding Registers)" :value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="起始地址">
                <el-input-number v-model="form.startAddr" :min="0" />
            </el-form-item>
            <el-form-item label="数量">
                <el-input-number v-model="form.count" :min="1" />
            </el-form-item>
            <el-form-item label="数据 (逗号分隔)">
                <el-input type="textarea" v-model="form.dataStr" placeholder="例如: 1,0,1 或 100,200" rows="4" />
                <div style="font-size:12px;color:#999;margin-top:6px;">
                    说明：如果类型为 0 区，每个数据为 0/1；如果为 4 区，每个数据为 0-65535（2 字节）。
                </div>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="cancel">取消</el-button>
            <el-button type="primary" @click="submit">下发</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'  // 【新增】导入ElMessage
import api from '../../api'
const props = defineProps({
    visible: Boolean,
    deviceId: [String, Number],
    deviceSn: String
})
const emit = defineEmits(['update:visible', 'success'])

const form = ref({ func: 6, type: 4, startAddr: 0, count: 1, dataStr: '' })
// 本地可写的 visible
const localVisible = ref(props.visible)
watch(() => props.visible, v => (localVisible.value = v))
watch(localVisible, v => emit('update:visible', v))
watch(() => props.visible, v => console.log('RemoteWriteDialog: props.visible ->', v))
watch(localVisible, v => console.log('RemoteWriteDialog: localVisible ->', v))

function cancel() {
    emit('update:visible', false)
}

function parseData() {
    const parts = (form.value.dataStr || '').split(',').map(s => s.trim()).filter(s => s !== '')
    if (form.value.type === 0) {
        // 位，接受 0/1
        const bits = parts.map(p => (p === '1' ? 1 : 0))
        return bits
    }
    // 4区，16位无符号
    const words = parts.map(p => {
        const n = Number(p)
        return Number.isFinite(n) ? (n & 0xffff) : 0
    })
    return words
}

async function submit() {
    if (!props.deviceId && !props.deviceSn) {
        ElMessage.error('未选择设备')
        return
    }
    const dataArr = parseData()
    if (dataArr.length === 0) {
        ElMessage.warning('请输入要下发的数据')
        return
    }
    // 校验长度
    if (dataArr.length !== form.value.count) {
        ElMessage.warning('数据数量需等于指定的数量')
        return
    }

    // 构造values字节数组
    const values = []
    if (form.value.type === 0) {
        // 每个数据按位打包，补齐到字节
        let byte = 0
        let bitIndex = 0
        for (let i = 0; i < dataArr.length; i++) {
            const bit = dataArr[i] ? 1 : 0
            byte |= (bit << bitIndex)
            bitIndex++
            if (bitIndex === 8) {
                values.push(byte)
                byte = 0
                bitIndex = 0
            }
        }
        if (bitIndex > 0) values.push(byte)
    } else {
        // 每个数据 2 字节
        dataArr.forEach(n => {
            values.push((n >> 8) & 0xff)
            values.push(n & 0xff)
        })
    }

    try {
        await api.remoteWrite({
            devSerial: props.deviceSn,
            dataType: form.value.type,
            startAddr: form.value.startAddr,
            quantity: form.value.count,
            values: values
        })
        ElMessage.success('下发成功')
        emit('success')
        emit('update:visible', false)
    } catch (e) {
        ElMessage.error('下发失败：' + (e.message || '接口异常'))
    }
}
</script>
