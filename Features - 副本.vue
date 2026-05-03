<template>
    <el-dialog v-model="visible" title="下发功能" width="500px">
        <div style="margin-bottom: 16px;">
            <el-alert type="info" show-icon :closable="false">
                <template #title>
                    <!-- 下发内容将按“相同站号+分区”合并为一条指令，拼成04功能码数据包。 -->
                </template>
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
        <el-button type="primary" @click="handleSend">确认下发</el-button>
        <el-button @click="visible = false" style="margin-left: 8px;">取消</el-button>
    </el-dialog>
</template>

// ...existing code...
<script setup>
import { ref, watch, computed } from 'vue'
import api from '../../api'
const props = defineProps({
    modelValue: Boolean,
    deviceId: [String, Number],
    deviceSn: String, // 新增
    variableList: Array
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

// 计算HEX字符串用于展示
const hexResult = computed(() => {
    const arr = build04FunctionCode(props.variableList)
    return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join(' ').toUpperCase()
})

async function handleSend() {
    try {
        // 调试：打印传入的变量列表和 deviceSn
        console.log('[Features] handleSend variableList:', props.variableList)
        console.log('[Features] deviceSn:', props.deviceSn)

        const code = build04FunctionCode(props.variableList)
        // 调试：打印最终字节数组
        console.log('[Features] built code bytes:', Array.from(code))

        const hexStr = Array.from(code).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase()
        // 输出序列号和HEX字符串
        await api.downpayload({
            Serial: props.deviceSn, // 使用序列号
            code: hexStr
        })
        if (window.ElMessage) window.ElMessage.success('下发成功')
        emit('success')
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('下发失败')
        console.error('[Features] handleSend error', e)
    }
    visible.value = false
}
function build04FunctionCode(variableList) {
    if (!Array.isArray(variableList) || variableList.length === 0) return new Uint8Array([])

    // 1. 按站号+分区分组
    const groupMap = {}
    variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })

    // 2. 组装每条指令
    const instructions = []
    Object.values(groupMap).forEach(group => {
        const addrs = group.map(v => parseInt(v.modbusAddr, 10)).filter(n => !Number.isNaN(n)).sort((a, b) => a - b)
        const minAddr = addrs[0]
        const maxAddr = addrs[addrs.length - 1]
        let len = (maxAddr - minAddr) + 1
        const { modbusDevice, modbusType } = group[0]

        instructions.push({
            device: Number(modbusDevice),
            type: Number(modbusType),
            addr: minAddr,
            len: len,
            rawAddrs: addrs
        })
    })

    // 调试：打印每条 instruction 的细节
    console.log('[Features] instructions:', instructions)

    // 3. 拼接数据包
    const funcCode = 0x04
    const dataBlockBytes = instructions.length * 6 // 每个数据块6字节
    const totalBytes = 1 + 2 + dataBlockBytes

    const buffer = []
    buffer.push(funcCode)
    buffer.push((totalBytes >> 8) & 0xff) // 高字节
    buffer.push(totalBytes & 0xff)        // 低字节

    instructions.forEach(ins => {
        // 调试：打印单条指令要写入的 addr/len
        console.log('[Features] writing ins:', ins)
        buffer.push(ins.device & 0xff)
        buffer.push(ins.type & 0xff)
        buffer.push((ins.addr >> 8) & 0xff)
        buffer.push(ins.addr & 0xff)
        buffer.push((ins.len >> 8) & 0xff)
        buffer.push(ins.len & 0xff)
    })

    return new Uint8Array(buffer)
}
</script>