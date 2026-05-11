<template>
    <div>
        <el-breadcrumb style="margin-bottom: 16px;">
            <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
            <el-breadcrumb-item>下发配置</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card shadow="never">
            <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 16px;">下发配置</span>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <span style="font-weight: bold;">设备：</span>
                        <Screening v-model="selectedDevID" @update:model-value="onDeviceChange" />
                        <span v-if="currentDevice" style="color: #909399;">SN: {{ currentDevice.DevSerial || currentDevice.serial || '' }}</span>
                    </div>
                </div>
            </template>
            <div v-if="!selectedDevID" style="text-align: center; padding: 40px; color: #909399;">
                <div style="font-size: 16px;">请先选择设备</div>
            </div>
            <template v-else>
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
                <div v-else-if="hasSandboxVars && selectedIds.size > 0" style="margin-bottom: 16px;">
                    <el-alert type="warning" show-icon :closable="false">
                        <strong>⚠️ 包含沙箱变量</strong>，将下发到沙箱通道，不会影响真实设备。
                    </el-alert>
                </div>
                
                <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center;">
                    <el-checkbox v-model="selectAll" :indeterminate="isIndeterminate" @change="handleSelectAll">
                        全选所有变量（{{ displayList.length }} 个）
                    </el-checkbox>
                    <div style="flex: 1;"></div>
                    <span>已选中 <strong>{{ selectedIds.size }}</strong> 个变量</span>
                </div>
                
                <el-table 
                    :data="displayList" 
                    style="width: 100%;" 
                    v-loading="loading" 
                    ref="tableRef"
                    @selection-change="handleSelectionChange"
                    row-key="id"
                    height="400"
                    border
                >
                    <el-table-column type="selection" width="55" reserve-selection />
                    <el-table-column prop="varName" label="变量名" min-width="160">
                        <template #default="scope">
                            <span>{{ scope.row.varName }}</span>
                            <el-tag v-if="scope.row.scope === 'sandbox'" size="small" type="warning" style="margin-left: 6px;">沙箱</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="dataType" label="数据类型" min-width="100">
                        <template #default="scope">
                            {{ getDataTypeLabel(scope.row.dataType) }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="modbusType" label="数据分区" min-width="100">
                        <template #default="scope">
                            {{ getModbusTypeLabel(scope.row.modbusType) }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="modbusDevice" label="Modbus站号" min-width="100" />
                    <el-table-column prop="modbusAddr" label="数据地址" min-width="100" />
                    <el-table-column label="长度" width="100">
                        <template #default="scope">
                            {{ scope.row.data_len }}
                        </template>
                    </el-table-column>
                </el-table>
                
                <div v-if="selectedIds.size > 0" style="margin-top: 16px;">
                    <el-divider>优化预览</el-divider>
                    <div style="margin-bottom: 12px;">
                        <el-alert type="success" show-icon :closable="false">
                            <div style="font-weight: bold; margin-bottom: 8px;">
                                合并后05上报数据包长度：<strong>{{ uploadLength }}</strong> 字节
                            </div>
                            <div style="font-size: 13px; line-height: 1.6;">
                                <div style="margin-bottom: 4px;">
                                    <strong>• 基础长度</strong>：功能码(1) + 报文总长度(2) = 3 字节
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
                    <div style="margin-bottom: 12px;">
                        <el-alert type="warning" show-icon :closable="false">
                            <div><strong>⚠️ 注意</strong></div>
                            <div style="margin-top: 8px; font-size: 13px; line-height: 1.6;">
                                <div>• 同区同站的变量会被合并读取，范围从最小地址到最大地址</div>
                                <div>• 实际读取的寄存器数量：<strong>{{ totalRegisterCount }}</strong> 个（含中间地址）</div>
                                <div>• 实际需要的寄存器数量：<strong>{{ actualNeededCount }}</strong> 个</div>
                                <div v-if="overheadPercent > 0" style="color: #f56c6c; font-weight: bold;">
                                    • 额外读取的寄存器：<strong>{{ totalRegisterCount - actualNeededCount }}</strong> 个（{{ overheadPercent }}% 浪费）
                                </div>
                            </div>
                        </el-alert>
                    </div>
                    <div v-if="optimizationResult && optimizationResult.optimizerUsed" style="margin-bottom: 12px;">
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
                </div>
                
                <div style="margin-top: 16px; display: flex; gap: 12px;">
                    <el-button type="primary" @click="handleSend" :loading="sending" :disabled="isMixedSelection || selectedIds.size === 0">
                        {{ selectedIds.size === 0 ? '清空配置' : '确认下发' }}
                    </el-button>
                    <el-button type="success" @click="handleExportResult" :disabled="selectedIds.size === 0">
                        导出结果
                    </el-button>
                    <el-button type="info" @click="handleQueryConfig" :loading="queryLoading">
                        查询数据配置
                    </el-button>
                    <el-button @click="goBack">返回</el-button>
                </div>
            </template>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Screening from './Screening.vue'
import api from '../../api'
import { useDeviceStore } from '../../stores'

const router = useRouter()
const route = useRoute()
const deviceStore = useDeviceStore()

const selectedDevID = ref(route.query.devId || '')
const displayList = ref([])
const loading = ref(false)
const sending = ref(false)
const queryLoading = ref(false)
const selectedIds = new Set()
const selectedRowsArray = ref([])
const tableRef = ref(null)
const selectAll = ref(false)
const isIndeterminate = ref(false)
const optimizationResult = ref(null)

const deviceList = computed(() => deviceStore.deviceList || [])
const currentDevice = computed(() => 
    deviceList.value.find(d => String(d.id) === String(selectedDevID.value))
)

const dataTypeMap = markRaw({
    '0': '布尔值',
    '1': 'int16',
    '2': 'int32',
    '3': 'float32',
    '4': 'float64',
    '5': '字符串'
})
const modbusTypeMap = markRaw({
    '0': '线圈',
    '1': '离散输入',
    '3': '输入寄存器',
    '4': '保持寄存器'
})

function getDataTypeLabel(val) {
    return dataTypeMap[val] || val || '-'
}
function getModbusTypeLabel(val) {
    const numType = Number(val)
    return modbusTypeMap[numType] || val
}
function getQuantityUnit(type) {
    const numType = Number(type)
    if (numType === 0 || numType === 1) return '个'
    return '个寄存器'
}

const selectedVariables = computed(() => 
    displayList.value.filter(row => selectedIds.has(String(row.id)))
)

const hasSandboxVars = computed(() => 
    selectedVariables.value.some(v => v.scope === 'sandbox')
)

const hasProductionVars = computed(() => 
    selectedVariables.value.some(v => !v.scope || v.scope === 'production')
)

const isMixedSelection = computed(() => 
    hasSandboxVars.value && hasProductionVars.value
)

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

    let hexBytes = [0x04]
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

const computedResult = computed(() => computeAll(selectedVariables.value))
const groupDetails = computed(() => computedResult.value.groupDetails)
const totalRegisterCount = computed(() => computedResult.value.totalRegisterCount)
const actualNeededCount = computed(() => computedResult.value.actualNeededCount)
const overheadPercent = computed(() => computedResult.value.overheadPercent)
const uploadLength = computed(() => computedResult.value.uploadLength)
const totalDataBytes = computed(() => 
    computedResult.value.groupDetails.map(g => 6 + g.dataBytes).reduce((a, b) => a + b, 0)
)

async function fetchVariables() {
    if (!selectedDevID.value) {
        displayList.value = []
        return
    }
    loading.value = true
    try {
        const res = await api.getvarbydeviceid({ deviceId: selectedDevID.value })
        let list = []
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            list = res.data.data.variables
        } else if (res.data && Array.isArray(res.data.variables)) {
            list = res.data.variables
        }
        displayList.value = (list || []).map(item => markRaw({
            id: item.iD ?? item.id ?? '',
            devID: item.devID ?? selectedDevID.value,
            varName: item.varName ?? '',
            dataType: item.dataType ?? '',
            modbusType: item.modbusType ?? '',
            modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '',
            data_len: item.data_len ?? item.dataLen ?? '',
            stringLen: item.stringLen ?? '',
            scope: item.scope ?? 'production'
        })).sort((a, b) => {
            const scopeA = a.scope === 'sandbox' ? 1 : 0
            const scopeB = b.scope === 'sandbox' ? 1 : 0
            if (scopeA !== scopeB) return scopeA - scopeB
            const deviceA = Number(a.modbusDevice) || 0
            const deviceB = Number(b.modbusDevice) || 0
            if (deviceA !== deviceB) return deviceA - deviceB
            const typeA = Number(a.modbusType) || 0
            const typeB = Number(b.modbusType) || 0
            if (typeA !== typeB) return typeA - typeB
            const addrA = Number(a.modbusAddr) || 0
            const addrB = Number(b.modbusAddr) || 0
            return addrA - addrB
        })
        
        // 如果有选中的变量ID（从路由参数传来），恢复选中状态
        const selectedIdsFromQuery = route.query.selectedIds ? route.query.selectedIds.split(',') : []
        if (selectedIdsFromQuery.length > 0) {
            selectedIdsFromQuery.forEach(id => selectedIds.add(id))
            selectedRowsArray.value = displayList.value.filter(row => selectedIds.has(String(row.id)))
        } else {
            selectedIds.clear()
            selectedRowsArray.value = []
        }
        
        selectAll.value = displayList.value.length > 0 && selectedIds.size === displayList.value.length
        isIndeterminate.value = selectedIds.size > 0 && selectedIds.size < displayList.value.length
        optimizationResult.value = null
        _cachedKey = ''
        
        // 如果有选中的变量，自动调用优化
        if (selectedIds.size > 0 && currentDevice.value) {
            callBackendOptimization()
        }
    } catch (e) {
        console.error('获取变量列表失败', e)
        ElMessage.error('获取变量列表失败')
    } finally {
        loading.value = false
    }
}

function onDeviceChange() {
    router.replace({ query: { ...route.query, devId: selectedDevID.value, selectedIds: undefined } })
    fetchVariables()
}

function handleSelectionChange(val) {
    selectedRowsArray.value = val
    selectedIds.clear()
    val.forEach(v => selectedIds.add(String(v.id)))
    
    const total = displayList.value.length
    const selected = selectedIds.size
    selectAll.value = total > 0 && selected === total
    isIndeterminate.value = selected > 0 && selected < total
    
    // 重新计算优化
    optimizationResult.value = null
    _cachedKey = ''
    if (selectedIds.size > 0 && currentDevice.value) {
        callBackendOptimization()
    }
}

function handleSelectAll(checked) {
    if (checked) {
        displayList.value.forEach(row => selectedIds.add(String(row.id)))
        selectedRowsArray.value = [...displayList.value]
        selectAll.value = true
        isIndeterminate.value = false
    } else {
        selectedIds.clear()
        selectedRowsArray.value = []
        selectAll.value = false
        isIndeterminate.value = false
    }
    optimizationResult.value = null
    _cachedKey = ''
    if (selectedIds.size > 0 && currentDevice.value) {
        callBackendOptimization()
    }
}

async function callBackendOptimization() {
    if (!currentDevice.value || !currentDevice.value.DevSerial || !currentDevice.value.serial) {
        return
    }
    const deviceSn = currentDevice.value.DevSerial || currentDevice.value.serial
    const vars = selectedVariables.value
    if (!vars.length) {
        return
    }
    try {
        const entries = vars.map(v => ({
            SlaveAddr: Number(v.modbusDevice) || 1,
            DataType: Number(v.modbusType),
            StartAddr: Number(v.modbusAddr),
            Length: Number(v.data_len) || 1
        }))
        const res = await api.sendDataConfig({
            DevSerial: deviceSn,
            scope: hasSandboxVars.value ? 'sandbox' : 'production',
            Entries: entries
        })
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
    } catch (e) {
        console.error('调用优化失败', e)
    }
}

async function handleSend() {
    if (!currentDevice.value) {
        ElMessage.error('请先选择设备')
        return
    }
    const deviceSn = currentDevice.value.DevSerial || currentDevice.value.serial
    if (!deviceSn) {
        ElMessage.error('设备序列号不能为空')
        return
    }

    if (isMixedSelection.value) {
        ElMessage.warning('不能同时下发沙箱变量和真实变量，请分开操作')
        return
    }

    if (selectedIds.size === 0) {
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

    sending.value = true
    try {
        if (selectedIds.size === 0) {
            const hexStr = '040003'
            await api.downpayload({
                serial: deviceSn,
                code: hexStr
            })
            ElMessage.success('配置已清空')
        } else {
            const entries = selectedVariables.value.map(v => ({
                SlaveAddr: Number(v.modbusDevice) || 1,
                DataType: Number(v.modbusType),
                StartAddr: Number(v.modbusAddr),
                Length: Number(v.data_len) || 1
            }))
            
            const res = await api.sendDataConfig({
                DevSerial: deviceSn,
                scope: hasSandboxVars.value ? 'sandbox' : 'production',
                Entries: entries
            })
            
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
        }
    } catch (e) {
        console.error('下发失败', e)
        ElMessage.error('下发失败：' + (e.message || '接口异常'))
    } finally {
        sending.value = false
    }
}

async function handleQueryConfig() {
    if (!currentDevice.value) {
        ElMessage.error('请先选择设备')
        return
    }
    const deviceSn = currentDevice.value.DevSerial || currentDevice.value.serial
    if (!deviceSn) {
        ElMessage.error('设备序列号不能为空')
        return
    }
    queryLoading.value = true
    try {
        await api.queryDataConfig({ devSerial: deviceSn })
        ElMessage.success('查询命令已下发')
    } catch (e) {
        ElMessage.error('查询失败：' + (e.message || '接口异常'))
    } finally {
        queryLoading.value = false
    }
}

function handleExportResult() {
    if (selectedIds.size === 0) {
        ElMessage.warning('没有可导出的数据')
        return
    }
    
    try {
        const exportGroups = groupDetails.value.map((group, index) => ({
            idx: index + 1,
            partition: group.type,
            address: group.startAddr,
            length: group.registerCount
        }))
        
        const lines = exportGroups.map(g => 
            `${g.idx} ${g.partition} ${g.address} ${g.length}`
        )
        
        const content = lines.join('\n')
        
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        
        const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
        const safeSn = (currentDevice.value?.DevSerial || currentDevice.value?.serial || 'unknown').replace(/[<>:"/\\|?*]/g, '_')
        link.download = `优化结果_${safeSn}_${dateStr}.txt`
        link.href = url
        link.click()
        
        URL.revokeObjectURL(url)
        ElMessage.success('导出成功')
    } catch (e) {
        ElMessage.error('导出失败：' + (e.message || '未知错误'))
    }
}

function goBack() {
    router.push({ path: '/home/variables', query: { devId: selectedDevID.value } })
}

onMounted(() => {
    if (selectedDevID.value) {
        fetchVariables()
    }
    if (deviceList.value.length === 0) {
        deviceStore.fetchDevices().catch(() => {})
    }
})

watch(selectedDevID, (val) => {
    if (val) {
        fetchVariables()
    } else {
        displayList.value = []
        selectedIds.clear()
        selectedRowsArray.value = []
    }
})
</script>
