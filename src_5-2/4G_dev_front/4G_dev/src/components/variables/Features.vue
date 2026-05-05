<template>
    <!-- ===================== 模板部分：无核心UI改动，仅优化按钮加载态 ===================== -->
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

        <!-- 【改动1】模板新增：按钮绑定loading状态，防止重复点击（老代码无此属性） -->
        <el-button type="primary" @click="handleSend" :loading="loading">确认下发</el-button>
        <!-- 【新增】0x03查询按钮：下发03功能码查询数据配置，支持单设备/批量模式 -->
        <el-button type="info" @click="handleQuery03" :loading="queryLoading">
            {{ isBatch ? '批量查询数据配置' : '查询数据配置' }}
        </el-button>
        <el-button @click="visible = false" style="margin-left: 8px;">取消</el-button>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { calculateRegisterNum } from '../../utils/datatype'

// ===================== Props参数部分：【改动2】优化参数默认值，支持批量模式 =====================
const props = defineProps({
    modelValue: Boolean,
    deviceId: [String, Number],
    deviceSn: String,
    variableList: {
        type: Array,
        default: () => []
    },
    isBatch: {  // 【新增】批量模式标识，参考DeviceDownDialog.vue
        type: Boolean,
        default: false
    },
    rows: {  // 【新增】批量模式下选中的设备列表
        type: Array,
        default: () => []
    }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
// 【改动3】全局新增：下发和查询加载状态变量，老代码无此变量
const loading = ref(false)
const queryLoading = ref(false)  // 【新增】0x03查询按钮的加载状态

// ===================== 监听逻辑：【无任何改动】完全保留老代码 =====================
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

// ===================== HEX预览计算：【无任何改动】完全保留老代码 =====================
const hexResult = computed(() => {
    const arr = build04FunctionCode(props.variableList)
    return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join(' ').toUpperCase()
})

// ===================== 下发函数：【迁移到方案2】使用 JSON接口 =====================
async function handleSend() {
    if (!props.deviceSn) {
        ElMessage.error('设备序列号不能为空')
        return
    }
    if (props.variableList.length === 0) {
        ElMessage.error('请选择需要下发的变量')
        return
    }
    
    // 构造方案2数据格式
    const entries = props.variableList.map(v => {
        // 先按站号+分区分组计算起始地址和长度（与build04FunctionCode保持一致）
        const addrs = props.variableList
            .filter(item => item.modbusDevice === v.modbusDevice && item.modbusType === v.modbusType)
            .map(item => parseInt(item.modbusAddr, 10))
            .filter(n => !isNaN(n) && n >= 0)
        if (addrs.length === 0) return null
        
        addrs.sort((a, b) => a - b)
        const minAddr = addrs[0]
        const maxAddr = addrs.at(-1)
        const len = maxAddr - minAddr + 1
        
        return {
            slaveAddr: Number(v.modbusDevice) || 1,
            dataType: Number(v.modbusType) || 0,
            startAddr: minAddr,
            length: len
        }
    }).filter(Boolean)
    
    // 去重（相同站号+分区只留一个）
    const uniqueEntries = []
    const seen = new Set()
    for (const entry of entries) {
        const key = `${entry.slaveAddr}_${entry.dataType}`
        if (!seen.has(key)) {
            seen.add(key)
            uniqueEntries.push(entry)
        }
    }
    
    loading.value = true
    try {
        await api.sendDataConfig({
            devSerial: props.deviceSn,
            entries: uniqueEntries
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

// ===================== 03功能码查询：【迁移到方案2】使用 JSON接口 =====================
async function handleQuery03() {
    if (props.isBatch && props.rows && props.rows.length > 0) {
        // ==================== 批量查询模式 ====================
        queryLoading.value = true
        try {
            // 遍历所有选中设备，对每个设备下发03查询指令
            for (const dev of props.rows) {
                await api.queryDataConfig({ devSerial: dev.sn })
                console.log(`[批量03查询] 设备: ${dev.sn} 查询指令已下发`)
            }
            ElMessage.success(`批量查询命令已下发，共 ${props.rows.length} 个设备`)
        } catch (e) {
            ElMessage.error('批量查询失败：' + (e.message || '接口异常'))
            console.error('[批量03功能码查询] 错误：', e)
        } finally {
            queryLoading.value = false
        }
    } else {
        // ==================== 单设备查询模式 ====================
        if (!props.deviceSn) {
            ElMessage.error('设备序列号不能为空')
            return
        }
        queryLoading.value = true
        try {
            await api.queryDataConfig({ devSerial: props.deviceSn })
            ElMessage.success('查询命令已下发')
        } catch (e) {
            ElMessage.error('查询失败：' + (e.message || '接口异常'))
            console.error('[03功能码查询] 错误：', e)
        } finally {
            queryLoading.value = false
        }
    }
}

// ===================== 核心协议函数：【改动5】全量适配新协议，核心变更区域 =====================
function build04FunctionCode(variableList) {
    if (!variableList || variableList.length === 0) return new Uint8Array([])

    // 1. 按站号+分区分组：【无任何改动】完全保留老代码逻辑
    const groupMap = {}
    variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })

    // 2. 计算起始地址/长度：【无任何改动】完全保留老代码逻辑
    const instructions = []
    Object.values(groupMap).forEach(group => {
        const addrs = group.map(v => parseInt(v.modbusAddr, 10)).filter(n => !isNaN(n) && n >= 0)
        if (addrs.length === 0) return
        addrs.sort((a, b) => a - b)
        const minAddr = addrs[0]
        const maxAddr = addrs.at(-1)
        const len = maxAddr - minAddr + 1
        const { modbusDevice, modbusType } = group[0]
        instructions.push({ device: Number(modbusDevice)||1, type: Number(modbusType)||0, addr: minAddr, len: len })
    })
    if (instructions.length === 0) return new Uint8Array([])

    // 3. 数据包拼接：【⚠️ 核心协议变更，老代码全部删除重构】
    const buffer = []
    // 功能码：无改动，固定0x04
    buffer.push(0x04)

    // -------------------------------------------------------------------------
    // 【⚠️ 重大改动1】老代码：写入 2字节 总长度字段
    // 【⚠️ 新协议】：删除总长度，替换为 2字节 数据组数（大端模式）
    // 老代码删除行：
    // const dataBlockBytes = instructions.length * 6
    // const totalBytes = 1 + 2 + dataBlockBytes
    // buffer.push((totalBytes >> 8) & 0xff)
    // buffer.push(totalBytes & 0xff)
    // -------------------------------------------------------------------------
    const dataCount = instructions.length
    buffer.push((dataCount >> 8) & 0xFF) // 数据组数 高字节
    buffer.push(dataCount & 0xFF)        // 数据组数 低字节

    // 4. 写入每组数据：【无改动】每组6字节格式保持不变
    instructions.forEach(ins => {
        buffer.push(ins.device & 0xFF)      // 1字节 从站地址
        buffer.push(ins.type & 0xFF)        // 1字节 分区类型
        buffer.push((ins.addr >> 8) & 0xFF) // 2字节 地址(大端)
        buffer.push(ins.addr & 0xFF)        
        buffer.push((ins.len >> 8) & 0xFF)  // 2字节 长度(大端)
        buffer.push(ins.len & 0xFF)        
    })

    // 【⚠️ 重大改动2】删除老代码中所有「总长度计算」的冗余逻辑
    return new Uint8Array(buffer)
}
</script>