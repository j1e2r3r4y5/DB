<template>
    <el-dialog v-model="visible" title="下发功能" width="700px">
        <div style="margin-bottom: 16px;">
            <el-alert type="info" show-icon :closable="false">
                下发内容将按"相同站号+分区"合并为一条指令，拼成04功能码数据包。
            </el-alert>
        </div>
        <div v-if="isMixedSelection" style="margin-bottom: 16px;">
            <el-alert type="error" show-icon :closable="false">
                <strong>❌ 不能同时下发沙箱变量和真实变量</strong>
                <div style="margin-top: 4px; font-size: 13px;">请分开操作：先勾选真实变量下发，再勾选沙箱变量下发</div>
            </el-alert>
        </div>
        <div v-else-if="hasSandboxVars" style="margin-bottom: 16px;">
            <el-alert type="warning" show-icon :closable="false">
                <strong>⚠️ 包含沙箱变量</strong>，将下发到沙箱通道，不会影响真实设备。
            </el-alert>
        </div>
        <div v-if="localVariableList.length === 0" style="text-align: center; padding: 20px; color: #909399; margin-bottom: 16px;">
            <div style="font-size: 16px; font-weight: bold;">将下发空配置</div>
            <div style="margin-top: 8px; font-size: 14px;">设备将停止采集所有变量</div>
        </div>
        <el-table v-else :data="localVariableList" size="small" border style="margin-bottom: 16px;" height="250">
            <el-table-column prop="varName" label="变量名" />
            <el-table-column prop="modbusDevice" label="站号" width="80" />
            <el-table-column prop="modbusType" label="分区" width="140">
                <template #default="scope">
                    {{ getModbusTypeLabel(scope.row.modbusType) }}
                </template>
            </el-table-column>
            <el-table-column prop="modbusAddr" label="地址" width="80" />
            <el-table-column label="数量" width="100">
                <template #default="scope">
                    {{ scope.row.data_len }} {{ getQuantityUnit(scope.row.modbusType) }}
                </template>
            </el-table-column>
        </el-table>
        <div v-if="localVariableList.length === 0" style="margin-bottom: 12px;">
            <el-input v-model="hexResult" type="textarea" :rows="2" readonly placeholder="下发空配置的04功能码（HEX）" />
        </div>
        <div v-else style="margin-bottom: 12px;">
            <el-input v-model="hexResult" type="textarea" :rows="3" readonly placeholder="下发功能码（HEX）" />
        </div>
        <div v-if="localVariableList.length > 0" style="margin-bottom: 12px;">
            <el-alert type="success" show-icon :closable="false">
                <div style="font-weight: bold; margin-bottom: 8px;">
                    合并后05上报数据包长度（优化前基线）：<strong>{{ uploadLength }}</strong> 字节
                </div>
                <div style="font-size: 13px; line-height: 1.6;">
                    <div style="margin-bottom: 4px;">
                        <strong>• 基础长度</strong>：功能码(1) + 报文总长度(2) = {{ 1 + 2 }} 字节
                    </div>
                    <div v-for="(group, idx) in groupDetails" :key="idx" style="margin-bottom: 4px;">
                        <strong>• 分组{{ idx + 1 }}</strong>：{{ getModbusTypeLabel(group.type) }} 站{{ group.slaveAddr }}，地址{{ group.startAddr }}-{{ group.endAddr }}（{{ group.registerCount }} {{ getQuantityUnit(group.type) }}）
                        <div style="margin-left: 24px; color: #666; font-size: 12px;">
                            头部(6) + {{ group.dataBytes }} 字节数据 = {{ 6 + group.dataBytes }} 字节
                        </div>
                    </div>
                    <div v-if="groupDetails.length > 0" style="margin-top: 8px; border-top: 1px dashed #ddd; padding-top: 8px;">
                        <strong>• 计算总计</strong>：3 + {{ totalDataBytes }} = <strong>{{ uploadLength }}</strong> 字节
                    </div>
                </div>
            </el-alert>
        </div>
        <div v-if="localVariableList.length > 0" style="margin-bottom: 12px;">
            <el-alert type="warning" show-icon :closable="false">
                <div><strong>⚠️ 注意</strong></div>
                <div style="margin-top: 8px; font-size: 13px; line-height: 1.6;">
                    <div>• 同区同站的变量会被合并读取，范围从最小地址到最大地址</div>
                    <div>• 实际读取的寄存器数量：<strong>{{ totalRegisterCount }}</strong> 个（含中间地址）</div>
                    <div>• 实际需要的寄存器数量：<strong>{{ actualNeededCount }}</strong> 个</div>
                    <div v-if="overheadPercent > 0" style="color: #f56c6c; font-weight: bold;">
                        • 额外读取的寄存器：<strong>{{ totalRegisterCount - actualNeededCount }}</strong> 个（{{ overheadPercent }}% 浪费）</div>
                </div>
            </el-alert>
        </div>

        <div v-if="optimizationResult && optimizationResult.optimizerUsed" style="margin-bottom: 16px;">
            <el-alert type="success" show-icon :closable="false">
                <div style="font-weight: bold; margin-bottom: 12px;">
                    🎉 优化成功！使用优化器：<strong>{{ optimizationResult.optimizerUsed || '未知' }}</strong>
                    <span v-if="optimizationResult.executionTimeMs != null" style="font-weight: normal; color: #666; margin-left: 12px;">
                        耗时：{{ optimizationResult.executionTimeMs }}ms
                    </span>
                </div>
                <div style="font-size: 14px; line-height: 2;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #ddd; padding-bottom: 8px; margin-bottom: 8px;">
                        <span><strong>指标</strong></span>
                        <span><strong>优化前</strong></span>
                        <span><strong>优化后</strong></span>
                        <span><strong>节省</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Payload 大小</span>
                        <span>{{ optimizationResult.originalPayload ?? 0 }} 字节</span>
                        <span><strong>{{ optimizationResult.optimizedPayload ?? 0 }} 字节</strong></span>
                        <span style="color: #67c23a; font-weight: bold;">
                            -{{ optimizationResult.savedBytes ?? 0 }} 字节 ({{ (optimizationResult.savedPercent ?? 0).toFixed(2) }}%)
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between;" v-if="optimizationResult.originalSegments != null && optimizationResult.optimizedSegments != null">
                        <span>地址段数</span>
                        <span>{{ optimizationResult.originalSegments }} 段</span>
                        <span><strong>{{ optimizationResult.optimizedSegments }} 段</strong></span>
                        <span style="color: #67c23a; font-weight: bold;">
                            -{{ optimizationResult.originalSegments - optimizationResult.optimizedSegments }} 段
                        </span>
                    </div>
                </div>
            </el-alert>
        </div>

        <el-button type="primary" @click="handleSend" :loading="loading" :disabled="isMixedSelection">确认下发</el-button>
        <el-button type="success" @click="handleExportResult" 
            :disabled="!localVariableList.length || !groupDetails.length">
            导出结果
        </el-button>
        <el-button type="info" @click="handleQuery03" :loading="queryLoading">
            {{ isBatch ? '批量查询数据配置' : '查询数据配置' }}
        </el-button>
        <el-button @click="visible = false" style="margin-left: 8px;">取消</el-button>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed, markRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

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
const optimizationResult = ref(null)
const localVariableList = ref([])

const hasSandboxVars = computed(() => {
    return localVariableList.value.some(v => v.scope === 'sandbox')
})

const hasProductionVars = computed(() => {
    return localVariableList.value.some(v => !v.scope || v.scope === 'production')
})

const isMixedSelection = computed(() => {
    return hasSandboxVars.value && hasProductionVars.value
})

// 静态映射
const modbusTypeMap = markRaw({
    0: '线圈',
    1: '离散输入',
    3: '输入寄存器',
    4: '保持寄存器'
})

function getModbusTypeLabel(type) {
    const numType = Number(type)
    return modbusTypeMap[numType] || type
}

function getQuantityUnit(type) {
    const numType = Number(type)
    if (numType === 0) return '个线圈'
    if (numType === 1) return '个离散输入'
    return '个寄存器'
}

// 一次性计算所有结果
let _cachedKey = ''
let _cachedResult = null

function computeAll(vars) {
    const currentKey = vars.map(v => v.id).join(',')
    if (currentKey === _cachedKey && _cachedResult) {
        return _cachedResult
    }

    const groups = getGroupDetails(vars)
    let actualNeeded = 0
    vars.forEach(v => {
        actualNeeded += Number(v.data_len) || 1
    })

    const totalRegisters = groups.reduce((sum, g) => sum + g.registerCount, 0)
    const totalDataBytes = groups.reduce((sum, g) => sum + 6 + g.dataBytes, 0)

    // 构建指令字节
    let hexBytes = [0x04] // 功能码
    // 计算报文总长度：1(功能码) + 2(长度) + groups.length*6
    const totalLen = 3 + groups.length * 6
    hexBytes.push((totalLen >> 8) & 0xFF)
    hexBytes.push(totalLen & 0xFF)

    groups.forEach(group => {
        hexBytes.push(group.slaveAddr & 0xFF)
        hexBytes.push(group.type & 0xFF)
        hexBytes.push((group.startAddr >> 8) & 0xFF)
        hexBytes.push(group.startAddr & 0xFF)
        hexBytes.push((group.registerCount >> 8) & 0xFF)
        hexBytes.push(group.registerCount & 0xFF)
    })

    const result = {
        groupDetails: groups,
        totalRegisterCount: totalRegisters,
        actualNeededCount: actualNeeded,
        overheadPercent: totalRegisters > 0 ? Math.round(((totalRegisters - actualNeeded) / totalRegisters) * 100) : 0,
        uploadLength: 3 + totalDataBytes,
        totalDataBytes,
        hexBytes
    }

    _cachedKey = currentKey
    _cachedResult = result
    return result
}

// 计算属性，全部复用缓存结果
const computedResult = computed(() => computeAll(localVariableList.value))
const groupDetails = computed(() => computedResult.value.groupDetails)
const totalRegisterCount = computed(() => computedResult.value.totalRegisterCount)
const actualNeededCount = computed(() => computedResult.value.actualNeededCount)
const overheadPercent = computed(() => computedResult.value.overheadPercent)
const uploadLength = computed(() => computedResult.value.uploadLength)
const totalDataBytes = computed(() => computedResult.value.groupDetails.map(g => 6 + g.dataBytes).join(' + '))
const hexResult = computed(() => {
    return Array.from(computedResult.value.hexBytes)
        .map(b => b.toString(16).padStart(2, '0'))
        .join(' ')
        .toUpperCase()
})

watch(() => props.modelValue, (v) => {
    console.log('弹窗打开:', v)
    visible.value = v
    if (v) {
        optimizationResult.value = null
        _cachedKey = ''
        localVariableList.value = [...(props.variableList || [])]
        console.log('变量列表:', localVariableList.value)
        if (!localVariableList.value || localVariableList.value.length === 0) {
            ElMessage.warning('请先选择要下发的变量')
        } else {
            console.log('准备调用后端优化')
            // 调用后端优化
            callBackendOptimization()
        }
    }
})
watch(visible, v => emit('update:modelValue', v))

// 调用后端优化
async function callBackendOptimization() {
    console.log('📞 callBackendOptimization 开始')
    console.log('props.deviceSn:', props.deviceSn)
    console.log('localVariableList.value.length:', localVariableList.value.length)
    if (!props.deviceSn || !localVariableList.value.length) {
        console.log('❌ 缺少参数，返回')
        return
    }
    try {
        const entries = localVariableList.value.map(v => ({
            SlaveAddr: Number(v.modbusDevice) || 1,
            DataType: Number(v.modbusType),
            StartAddr: Number(v.modbusAddr),
            Length: Number(v.data_len) || 1
        }))
        console.log('📤 准备发送的数据:', entries)
        
        const res = await api.sendDataConfig({
            DevSerial: props.deviceSn,
            scope: hasSandboxVars.value ? 'sandbox' : 'production',
            Entries: entries
        })
        
        console.log('📥 后端返回:', res)
        console.log('📋 res.data 完整内容:', JSON.stringify(res.data, null, 2))
        const responseData = res.data.data
        if (res && responseData) {
            console.log('✅ 设置优化结果')
            console.log('  responseData.optimizerUsed:', responseData.optimizerUsed)
            console.log('  responseData.originalPayload:', responseData.originalPayload)
            console.log('  responseData.optimizedPayload:', responseData.optimizedPayload)
            console.log('  responseData.savedBytes:', responseData.savedBytes)
            console.log('  responseData.savedPercent:', responseData.savedPercent)
            console.log('  responseData.originalSegments:', responseData.originalSegments)
            console.log('  responseData.optimizedSegments:', responseData.optimizedSegments)
            console.log('  responseData.executionTimeMs:', responseData.executionTimeMs)
            
            optimizationResult.value = {
                optimizerUsed: responseData.optimizerUsed || 'DefaultOptimizer',
                originalPayload: responseData.originalPayload,
                optimizedPayload: responseData.optimizedPayload,
                savedBytes: responseData.savedBytes,
                savedPercent: responseData.savedPercent,
                originalSegments: responseData.originalSegments,
                optimizedSegments: responseData.optimizedSegments,
                executionTimeMs: responseData.executionTimeMs
            }
            console.log('✨ optimizationResult.value:', optimizationResult.value)
        } else {
            console.log('❌ res 或 responseData 为空')
        }
    } catch (e) {
        console.error('❌ 调用优化失败', e)
        // 失败回退到前端简单合并
        calculateOptimizationResult()
    }
}

// 计算优化结果（保留作为回退）
function calculateOptimizationResult() {
    console.log('🔙 calculateOptimizationResult 被调用（走了回退分支）')
    if (!localVariableList.value || localVariableList.value.length === 0) {
        optimizationResult.value = null
        return
    }
    const startTime = Date.now()
    const groups = getGroupDetails(localVariableList.value)
    const originalPayload = calculate04Length(localVariableList.value)
    const endTime = Date.now()
    console.log('计算结果 - 原始Payload:', originalPayload, '分组数:', groups.length)
    optimizationResult.value = {
        optimizerUsed: 'AddressMerger',
        executionTimeMs: endTime - startTime,
        originalPayload,
        optimizedPayload: originalPayload,
        savedBytes: 0,
        savedPercent: 0,
        originalSegments: groups.length,
        optimizedSegments: groups.length
    }
    console.log('设置 optimizationResult.value:', optimizationResult.value)
}

// 计算原始分组详情
function getGroupDetails(vars) {
    const groupMap = new Map()
    vars.forEach(v => {
        const key = `${v.modbusDevice}_${v.modbusType}`
        if (!groupMap.has(key)) {
            groupMap.set(key, {
                slaveAddr: Number(v.modbusDevice) || 1,
                type: Number(v.modbusType),
                items: []
            })
        }
        groupMap.get(key).items.push(v)
    })
    const result = []
    groupMap.forEach(group => {
        let minAddr = Infinity
        let maxAddr = -Infinity
        group.items.forEach(v => {
            const addr = Number(v.modbusAddr) || 0
            const len = Number(v.data_len) || 1
            minAddr = Math.min(minAddr, addr)
            maxAddr = Math.max(maxAddr, addr + len - 1)
        })
        const registerCount = maxAddr - minAddr + 1
        let dataBytes
        if (group.type === 0 || group.type === 1) {
            dataBytes = Math.ceil(registerCount / 8)
        } else {
            dataBytes = registerCount * 2
        }
        result.push({
            ...group,
            startAddr: minAddr,
            endAddr: maxAddr,
            registerCount,
            dataBytes
        })
    })
    return result
}

// 计算04长度
function calculate04Length(vars) {
    if (!vars || vars.length === 0) return 0
    const groups = getGroupDetails(vars)
    let totalDataBytes = 0
    groups.forEach(g => {
        totalDataBytes += 6 + g.dataBytes
    })
    return 3 + totalDataBytes
}

async function handleSend() {
    if (!props.deviceSn) {
        ElMessage.error('设备序列号不能为空')
        return
    }

    if (isMixedSelection.value) {
        ElMessage.warning('不能同时下发沙箱变量和真实变量，请分开操作')
        return
    }

    if (localVariableList.value.length === 0) {
        try {
            await ElMessageBox.confirm(
                '确定要清空所有数据配置吗？设备将停止采集和上报数据。',
                '清空配置确认',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )
        } catch (e) {
            return
        }
    }

    loading.value = true
    try {
        // 如果是空配置
        if (localVariableList.value.length === 0) {
            // 清空配置特殊处理
            const hexStr = '040003'
            await api.downpayload({
                serial: props.deviceSn,
                code: hexStr
            })
            ElMessage.success('配置已清空')
            emit('success', [])
            return
        }

        // 用新接口下发（带优化）
        const entries = localVariableList.value.map(v => ({
            SlaveAddr: Number(v.modbusDevice) || 1,
            DataType: Number(v.modbusType),
            StartAddr: Number(v.modbusAddr),
            Length: Number(v.data_len) || 1
        }))
        
        const res = await api.sendDataConfig({
            DevSerial: props.deviceSn,
            scope: hasSandboxVars.value ? 'sandbox' : 'production',
            Entries: entries
        })
        
        // 更新优化结果显示
        const responseData = res.data.data
        if (res && responseData) {
            optimizationResult.value = {
                optimizerUsed: responseData.optimizerUsed || 'DefaultOptimizer',
                originalPayload: responseData.originalPayload,
                optimizedPayload: responseData.optimizedPayload,
                savedBytes: responseData.savedBytes,
                savedPercent: responseData.savedPercent,
                originalSegments: responseData.originalSegments,
                optimizedSegments: responseData.optimizedSegments,
                executionTimeMs: responseData.executionTimeMs
            }
        }
        
        ElMessage.success('下发成功')
        emit('success', localVariableList.value)
    } catch (e) {
        console.error('[04功能码下发] 完整错误信息：', e)
        ElMessage.error('下发失败：' + (e.message || '接口异常'))
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
            }
            ElMessage.success(`批量查询命令已下发，共 ${props.rows.length} 个设备`)
        } catch (e) {
            ElMessage.error('批量查询失败：' + (e.message || '接口异常'))
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
        } finally {
            queryLoading.value = false
        }
    }
}

// 导出优化结果
function handleExportResult() {
    if (!localVariableList.value.length) {
        ElMessage.warning('没有可导出的数据')
        return
    }
    
    try {
        // 导出当前的分组
        const exportGroups = groupDetails.value.map((group, index) => ({
            idx: index + 1,
            partition: group.type,
            address: group.startAddr,
            length: group.registerCount
        }))
        
        // 按导入格式构建：idx partition address length
        const lines = exportGroups.map(g => 
            `${g.idx} ${g.partition} ${g.address} ${g.length}`
        )
        
        const content = lines.join('\n')
        
        // 创建下载
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        
        // 文件名：优化结果_设备SN_时间.txt
        const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
        const safeSn = (props.deviceSn || 'unknown').replace(/[<>:"/\\|?*]/g, '_')
        link.download = `优化结果_${safeSn}_${dateStr}.txt`
        link.href = url
        link.click()
        
        URL.revokeObjectURL(url)
        ElMessage.success('导出成功')
    } catch (e) {
        ElMessage.error('导出失败：' + (e.message || '未知错误'))
    }
}
</script>
