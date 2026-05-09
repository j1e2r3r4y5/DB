<template>
    <el-dialog v-model="visible" title="下发功能" width="600px">
        <div style="margin-bottom: 16px;">
            <el-alert type="info" show-icon :closable="false">
                下发内容将按“相同站号+分区”合并为一条指令，拼成04功能码数据包。
            </el-alert>
        </div>
        <div v-if="variableList.length === 0" style="text-align: center; padding: 20px; color: #909399; margin-bottom: 16px;">
            <div style="font-size: 16px; font-weight: bold;">将下发空配置</div>
            <div style="margin-top: 8px; font-size: 14px;">设备将停止采集所有变量</div>
        </div>
        <el-table v-else :data="variableList" size="small" border style="margin-bottom: 16px;">
            <el-table-column prop="varName" label="变量名" />
            <el-table-column prop="modbusDevice" label="站号" />
            <el-table-column prop="modbusType" label="分区">
                <template #default="{ row }">
                    {{ getModbusTypeLabel(row.modbusType) }}
                </template>
            </el-table-column>
            <el-table-column prop="modbusAddr" label="地址" />
            <el-table-column label="数量">
                <template #default="{ row }">
                    {{ row.data_len }} {{ getQuantityUnit(row.modbusType) }}
                </template>
            </el-table-column>
        </el-table>
        <div v-if="variableList.length === 0" style="margin-bottom: 12px;">
            <el-input v-model="hexResult" type="textarea" :rows="2" readonly placeholder="下发空配置的04功能码（HEX）" />
        </div>
        <div v-else style="margin-bottom: 12px;">
            <el-input v-model="hexResult" type="textarea" :rows="3" readonly placeholder="下发功能码（HEX）" />
        </div>
        <div v-if="variableList.length > 0" style="margin-bottom: 12px;">
            <el-alert type="success" show-icon :closable="false">
                <div style="font-weight: bold; margin-bottom: 8px;">
                    未来05上报数据包预计长度：<strong>{{ uploadLength }}</strong> 字节
                </div>
                <div style="font-size: 13px; line-height: 1.6;">
                    <div style="margin-bottom: 4px;">
                        <strong>• 基础长度</strong>：功能码(1) + 数据组数(2) = {{ 1 + 2 }} 字节
                    </div>
                    <div v-for="(group, idx) in groupDetails" :key="idx" style="margin-bottom: 4px;">
                        <strong>• 分组{{ idx + 1 }}</strong>：{{ getModbusTypeLabel(group.type) }} 站{{ group.slaveAddr }}，地址{{ group.startAddr }}-{{ group.endAddr }}（{{ group.registerCount }} {{ getQuantityUnit(group.type) }}）
                        <div style="margin-left: 24px; color: #666; font-size: 12px;">
                            头部(6) + {{ group.dataBytes }} 字节数据 = {{ 6 + group.dataBytes }} 字节
                        </div>
                    </div>
                    <div v-if="groupDetails.length > 0" style="margin-top: 8px; border-top: 1px dashed #ddd; padding-top: 8px;">
                        <strong>• 计算总计</strong>：3 + {{ groupDetails.map(g => 6 + g.dataBytes).join(' + ') }} = <strong>{{ uploadLength }}</strong> 字节
                    </div>
                </div>
            </el-alert>
        </div>
        <div v-if="variableList.length > 0" style="margin-bottom: 12px;">
            <el-alert type="warning" show-icon :closable="false">
                <div><strong>⚠️ 注意：</strong></div>
                <div style="margin-top: 8px; font-size: 13px; line-height: 1.6;">
                    <div>• 同区同站的变量会被合并读取，范围从最小地址到最大地址</div>
                    <div>• 实际读取的寄存器数量：<strong>{{ totalRegisterCount }}</strong> 个（含中间地址）</div>
                    <div>• 实际需要的寄存器数量：<strong>{{ actualNeededCount }}</strong> 个</div>
                    <div v-if="overheadPercent > 0" style="color: #f56c6c; font-weight: bold;">
                        • 额外读取的寄存器：<strong>{{ totalRegisterCount - actualNeededCount }}</strong> 个（{{ overheadPercent }}% 浪费）</div>
                </div>
            </el-alert>
        </div>

        <el-button type="primary" @click="handleSend" :loading="loading">确认下发</el-button>
        <el-button type="info" @click="handleQuery03" :loading="queryLoading">
            {{ isBatch ? '批量查询数据配置' : '查询数据配置' }}
        </el-button>
        <el-button @click="visible = false" style="margin-left: 8px;">取消</el-button>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import { calculateRegisterNum } from '../../utils/datatype'

const props = defineProps({
    modelValue: Boolean,
    deviceId: [String, Number],
    deviceSn: String,
    variableList: {
        type: Array,
        default: () => []
    },
    isBatch: {
        type: Boolean,
        default: false
    },
    rows: {
        type: Array,
        default: () => []
    }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const loading = ref(false)
const queryLoading = ref(false)

watch(() => props.modelValue, (v) => {
    visible.value = v
    if (v) {
        if (!props.variableList || props.variableList.length === 0) {
            ElMessage.warning('请先选择要下发的变量')
        }
    }
})
watch(visible, v => emit('update:modelValue', v))

const hexResult = computed(() => {
    const arr = build04FunctionCode(props.variableList)
    return Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join(' ').toUpperCase()
})

const groupDetails = computed(() => getGroupDetails(props.variableList))

const uploadLength = computed(() => calculate05UploadLength(props.variableList))

const totalRegisterCount = computed(() => {
    if (!props.variableList || props.variableList.length === 0) return 0
    
    const groupMap = {}
    props.variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })
    
    let total = 0
    Object.values(groupMap).forEach(group => {
        // 计算每个变量的起始和结束地址
        const addrRanges = group.map(v => {
            const startAddr = parseInt(v.modbusAddr, 10)
            const dataLen = parseInt(v.data_len, 10) || 1
            if (isNaN(startAddr) || startAddr < 0) return null
            return {
                start: startAddr,
                end: startAddr + dataLen - 1
            }
        }).filter(Boolean)

        if (addrRanges.length === 0) return

        // 找到最小和最大地址
        const minAddr = Math.min(...addrRanges.map(r => r.start))
        const maxAddr = Math.max(...addrRanges.map(r => r.end))
        total += maxAddr - minAddr + 1
    })
    return total
})

const actualNeededCount = computed(() => {
    if (!props.variableList || props.variableList.length === 0) return 0
    return props.variableList.reduce((sum, v) => sum + (Number(v.data_len) || 1), 0)
})

const overheadPercent = computed(() => {
    if (totalRegisterCount.value <= 0 || actualNeededCount.value <= 0) return 0
    const overhead = totalRegisterCount.value - actualNeededCount.value
    if (overhead <= 0) return 0
    return Math.round((overhead / totalRegisterCount.value) * 100)
})

function getGroupDetails(variableList) {
    if (!variableList || variableList.length === 0) return []

    const groupMap = {}
    variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })

    return Object.values(groupMap).map(group => {
        // 计算每个变量的起始和结束地址
        const addrRanges = group.map(v => {
            const startAddr = parseInt(v.modbusAddr, 10)
            const dataLen = parseInt(v.data_len, 10) || 1
            if (isNaN(startAddr) || startAddr < 0) return null
            return {
                start: startAddr,
                end: startAddr + dataLen - 1
            }
        }).filter(Boolean)

        if (addrRanges.length === 0) return null

        // 找到最小和最大地址
        const minAddr = Math.min(...addrRanges.map(r => r.start))
        const maxAddr = Math.max(...addrRanges.map(r => r.end))
        const registerCount = maxAddr - minAddr + 1
        const modbusType = Number(group[0].modbusType)

        let dataBytes
        if (modbusType === 0 || modbusType === 1) {
            dataBytes = Math.ceil(registerCount / 8)
        } else {
            dataBytes = registerCount * 2
        }

        return {
            slaveAddr: Number(group[0].modbusDevice) || 1,
            type: modbusType,
            startAddr: minAddr,
            endAddr: maxAddr,
            registerCount,
            dataBytes
        }
    }).filter(Boolean)
}

function calculate05UploadLength(variableList) {
    if (!variableList || variableList.length === 0) return 0
    
    const groups = getGroupDetails(variableList)
    
    // 基础长度：功能码1字节 + 数据组数2字节
    let totalLength = 1 + 2
    
    groups.forEach(group => {
        // 每组：头部6字节 + 数据字节数
        totalLength += 6 + group.dataBytes
    })
    
    return totalLength
}

async function handleSend() {
    if (!props.deviceSn) {
        ElMessage.error('设备序列号不能为空')
        return
    }
    
    // 使用同样的分组逻辑
    const groupMap = {}
    props.variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })

    const entries = []
    Object.values(groupMap).forEach(group => {
        // 计算每个变量的起始和结束地址
        const addrRanges = group.map(v => {
            const startAddr = parseInt(v.modbusAddr, 10)
            const dataLen = parseInt(v.data_len, 10) || 1
            if (isNaN(startAddr) || startAddr < 0) return null
            return {
                start: startAddr,
                end: startAddr + dataLen - 1
            }
        }).filter(Boolean)

        if (addrRanges.length === 0) return

        // 找到最小和最大地址
        const minAddr = Math.min(...addrRanges.map(r => r.start))
        const maxAddr = Math.max(...addrRanges.map(r => r.end))
        const len = maxAddr - minAddr + 1
        const { modbusDevice, modbusType } = group[0]
        
        entries.push({
            slaveAddr: Number(modbusDevice) || 1,
            dataType: Number(modbusType) || 0,
            startAddr: minAddr,
            length: len
        })
    })
    
    console.log('[Features] 准备下发配置', {
        variableList: props.variableList,
        entries: entries,
        entriesCount: entries.length
    })
    
    // 如果是空配置，给用户二次确认
    if (entries.length === 0) {
        try {
            console.log('[Features] 显示空配置确认弹窗')
            await ElMessageBox.confirm(
                '确定要清空所有数据配置吗？设备将停止采集和上报数据。',
                '清空配置确认',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )
            console.log('[Features] 用户点击了确定')
        } catch (e) {
            console.log('[Features] 用户取消了空配置', e)
            // 用户取消
            return
        }
    }
    
    loading.value = true
    try {
        console.log('[Features] 发送 API 请求', {
            devSerial: props.deviceSn,
            entries: entries
        })
        await api.sendDataConfig({
            devSerial: props.deviceSn,
            entries: entries
        })
        console.log('[Features] API 请求成功')
        ElMessage.success(entries.length === 0 ? '配置已清空' : '下发成功')
        emit('success', props.variableList)
        visible.value = false
    } catch (e) {
        ElMessage.error('下发失败：' + (e.message || '接口异常'))
        console.error('[04功能码下发] 错误：', e)
    } finally {
        loading.value = false
    }
}

async function handleQuery03() {
    if (props.isBatch && props.rows && props.rows.length > 0) {
        queryLoading.value = true
        try {
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

function getModbusTypeLabel(type) {
    const numType = Number(type)
    const typeMap = {
        0: '线圈',
        1: '离散输入',
        3: '输入寄存器',
        4: '保持寄存器'
    }
    return typeMap[numType] || type
}

function getQuantityUnit(type) {
    const numType = Number(type)
    if (numType === 0) {
        return '个线圈'
    }
    if (numType === 1) {
        return '个离散输入'
    }
    return '个寄存器'
}

function build04FunctionCode(variableList) {
    if (!variableList || variableList.length === 0) return new Uint8Array([])

    const groupMap = {}
    variableList.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap[key]) groupMap[key] = []
        groupMap[key].push(v)
    })

    const instructions = []
    Object.values(groupMap).forEach(group => {
        // 计算每个变量的起始和结束地址
        const addrRanges = group.map(v => {
            const startAddr = parseInt(v.modbusAddr, 10)
            const dataLen = parseInt(v.data_len, 10) || 1
            if (isNaN(startAddr) || startAddr < 0) return null
            return {
                start: startAddr,
                end: startAddr + dataLen - 1
            }
        }).filter(Boolean)

        if (addrRanges.length === 0) return

        // 找到最小和最大地址
        const minAddr = Math.min(...addrRanges.map(r => r.start))
        const maxAddr = Math.max(...addrRanges.map(r => r.end))
        const len = maxAddr - minAddr + 1
        const { modbusDevice, modbusType } = group[0]
        instructions.push({ device: Number(modbusDevice)||1, type: Number(modbusType)||0, addr: minAddr, len: len })
    })
    if (instructions.length === 0) return new Uint8Array([])

    const buffer = []
    buffer.push(0x04)

    const dataCount = instructions.length
    buffer.push((dataCount >> 8) & 0xFF)
    buffer.push(dataCount & 0xFF)

    instructions.forEach(ins => {
        buffer.push(ins.device & 0xFF)
        buffer.push(ins.type & 0xFF)
        buffer.push((ins.addr >> 8) & 0xFF)
        buffer.push(ins.addr & 0xFF)
        buffer.push((ins.len >> 8) & 0xFF)
        buffer.push(ins.len & 0xFF)
    })

    return new Uint8Array(buffer)
}
</script>
