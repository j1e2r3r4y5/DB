<template>
    <el-dialog v-model="visible" title="下发功能" width="500px">
        <div style="margin-bottom: 16px;">
            <el-alert type="info" show-icon :closable="false">
                下发内容将按“相同站号+分区”合并为一条指令，拼成04功能码数据包。
            </el-alert>
        </div>
        <el-table :data="variableList" size="small" border style="margin-bottom: 16px;">
            <el-table-column prop="varName" label="变量名" />
            <el-table-column prop="modbusDevice" label="站号" />
            <el-table-column prop="modbusType" label="分区" />
            <el-table-column prop="modbusAddr" label="地址" />
        </el-table>
        <div style="margin-bottom: 12px;">
            <el-input v-model="hexResult" type="textarea" :rows="3" readonly placeholder="下发功能码（HEX）" />
        </div>
        <el-button type="primary" @click="handleSend" :loading="loading">确认下发</el-button>
        <el-button @click="visible = false" style="margin-left: 8px;">取消</el-button>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import api from '../../api'
const props = defineProps({
    modelValue: Boolean,
    deviceId: [String, Number],
    deviceSn: String,
    variableList: {
        type: Array,
        default: () => []
    }
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const loading = ref(false) // 下发加载状态

// 双向绑定弹窗显隐
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

// 实时计算预览HEX指令
const hexResult = computed(() => {
    const arr = build04FunctionCode(props.variableList)
    return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join(' ').toUpperCase()
})

// 下发执行
async function handleSend() {
    // 基础校验
    if (!props.deviceSn) {
        ElMessage.error('设备序列号不能为空')
        return
    }
    if (props.variableList.length === 0) {
        ElMessage.error('请选择需要下发的变量')
        return
    }

    loading.value = true
    try {
        const code = build04FunctionCode(props.variableList)
        const hexStr = Array.from(code).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase()
        
        // 调用下发接口
        await api.downpayload({
            Serial: props.deviceSn,
            code: hexStr
        })
        
        ElMessage.success('下发成功')
        emit('success')
        visible.value = false
    } catch (e) {
        ElMessage.error('下发失败：' + (e.message || '接口异常'))
        console.error('[04功能码下发] 错误：', e)
    } finally {
        loading.value = false
    }
}

// ===================== 【适配新协议】核心组装函数 =====================
function build04FunctionCode(variableList) {
    if (!variableList || variableList.length === 0) return new Uint8Array([])

    // 1. 按【站号+分区】分组（相同站号+分区合并为一组）
    const groupMap = {}
    variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })

    // 2. 计算每组：起始地址、数据长度
    const instructions = []
    Object.values(groupMap).forEach(group => {
        // 过滤有效地址
        const addrs = group.map(v => parseInt(v.modbusAddr, 10)).filter(n => !isNaN(n) && n >= 0)
        if (addrs.length === 0) return

        addrs.sort((a, b) => a - b)
        const minAddr = addrs[0]
        const maxAddr = addrs.at(-1)
        const len = maxAddr - minAddr + 1
        const { modbusDevice, modbusType } = group[0]

        instructions.push({
            device: Number(modbusDevice) || 1,   // 从站地址
            type: Number(modbusType) || 0,       // 分区类型
            addr: minAddr,                       // 起始地址
            len: len                             // 数据长度
        })
    })

    if (instructions.length === 0) return new Uint8Array([])

    // 3. 【新协议】拼接数据包
    const buffer = []
    // ① 1字节 功能码：0x04
    buffer.push(0x04)
    // ② 2字节 数据组数（大端模式）
    const dataCount = instructions.length
    buffer.push((dataCount >> 8) & 0xFF)  // 高字节
    buffer.push(dataCount & 0xFF)         // 低字节
    // ③ N组 数据单元（每组6字节）
    instructions.forEach(ins => {
        buffer.push(ins.device & 0xFF)      // 1字节 从站地址
        buffer.push(ins.type & 0xFF)        // 1字节 分区类型
        buffer.push((ins.addr >> 8) & 0xFF) // 2字节 地址(高字节)
        buffer.push(ins.addr & 0xFF)        // 2字节 地址(低字节)
        buffer.push((ins.len >> 8) & 0xFF)  // 2字节 长度(高字节)
        buffer.push(ins.len & 0xFF)         // 2字节 长度(低字节)
    })

    return new Uint8Array(buffer)
}
</script>