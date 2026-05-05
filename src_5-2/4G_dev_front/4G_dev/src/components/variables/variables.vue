<template>
    <div class="device-table-wrapper">
        <!-- <div style="font-size: 18px; font-weight: bold; margin-bottom: 12px;">变量表管理</div> -->
        <div class="action-buttons"
            style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
            <el-button type="default" @click="goBack">返回</el-button>
            <el-button type="primary" @click="dialogVisible = true">新建变量</el-button>
            <el-button type="primary" @click="fetchVariables">刷新</el-button>
            <el-button type="primary" @click="handleRecoveryVariable">撤销变更</el-button>
            <el-button type="primary" @click="showFeatures = true"
                :disabled="!(currentDevice && currentDevice.chengeFlag === 1)">下发</el-button>
            <!-- <el-button type="warning" @click="openRemoteWrite" :disabled="!currentDevice">远程置数</el-button> -->

        </div>

        <span v-if="currentDevice && currentDevice.chengeFlag === 1"
            style="color:#e53935;font-weight:bold;">有修改操作</span>
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span style="margin-right: 8px; font-size: 14px; color: #333;">请选择设备</span>
            <Screening v-model="selectedDevID" />
        </div>
        <el-table :data="filteredVariableList" style="width: 100%;" v-loading="loading" ref="tableRef"
            @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="55" />
            <el-table-column prop="varName" label="变量名" min-width="120"></el-table-column>
            <el-table-column prop="dataType" label="数据类型" min-width="100" :formatter="dataTypeFormatter" />
            <el-table-column prop="modbusType" label="数据分区" min-width="100" :formatter="dataTypeFormatter" />
            <el-table-column prop="modbusDevice" label="Modbus站号" min-width="100"></el-table-column>
            <el-table-column prop="modbusAddr" label="数据地址" min-width="100"></el-table-column>
            <el-table-column prop="stringLen" label="字符串长度" min-width="100">
                <template #default="scope">
                    {{ (!scope.row.stringLen && scope.row.stringLen !== 0) ? '-' : (scope.row.stringLen === 0 ? '-' :
                        scope.row.stringLen) }}
                </template>
            </el-table-column>
            <el-table-column prop="decimalDigits" label="小数位数" min-width="100">
                <template #default="scope">
                    {{ (!scope.row.decimalDigits && scope.row.decimalDigits !== 0) ? '-' : (scope.row.decimalDigits ===
                        0
                        ? '-' : scope.row.decimalDigits) }}
                </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
                <template #default="scope">
                    <el-button link class="el-btn" @click="handleEditVariable(scope.row)">编辑</el-button>
                    <el-button link class="el-btn" @click="handleDeleteClick(scope.row)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <Features v-model="showFeatures" :device-id="selectedDevID" :device-sn="currentDevice?.sn"
            :variable-list="filteredVariableList" @success="fetchVariables" />
        <RemoteWriteDialog v-model:visible="showRemoteWrite" :device-id="selectedDevID" :device-sn="currentDevice?.sn"
            @success="fetchVariables" />
        <Editingvar v-model="editDialogVisible" :variable="editRow" @success="fetchVariables" />
        <AddVariables v-model="dialogVisible" @success="fetchVariables" :default-dev-id="selectedDevID" />
        <el-dialog v-model="deleteDialogVisible" title="确认删除" width="320px">
            <div style="font-size:16px;">确定要删除该变量吗？</div>
            <template #footer>
                <el-button @click="deleteDialogVisible = false">取消</el-button>
                <el-button type="danger" @click="confirmDelete">删除</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, inject, watch } from 'vue'
const props = defineProps({ initDevId: [String, Number] })
const emit = defineEmits(['back-to-device'])

function goBack() {
    emit('back-to-device')
}
import Screening from './Screening.vue'
import api from '../../api'
import AddVariables from './addvariables.vue'
import Editingvar from './Editingvar.vue'
import Features from './Features.vue'
import RemoteWriteDialog from './RemoteWriteDialog.vue'
const showFeatures = ref(false)
const showRemoteWrite = ref(false)
const deviceList = inject('deviceList', ref([]))
const currentDevice = computed(() =>
    deviceList.value.find(d => String(d.id) === String(selectedDevID.value))
)
const selectedDevID = ref('1') // 默认1
const filteredVariableList = computed(() =>
    allVariableList.value
        .filter(v => String(v.devID) === String(selectedDevID.value))
        .sort((a, b) => {
            // 1. 先按 modbusDevice（站号）升序
            const deviceA = Number(a.modbusDevice) || 0
            const deviceB = Number(b.modbusDevice) || 0
            if (deviceA !== deviceB) return deviceA - deviceB

            // 2. 再按 modbusType（数据分区）升序
            const typeA = Number(a.modbusType) || 0
            const typeB = Number(b.modbusType) || 0
            if (typeA !== typeB) return typeA - typeB

            // 3. 最后按 modbusAddr（数据地址）升序
            const addrA = Number(a.modbusAddr) || 0
            const addrB = Number(b.modbusAddr) || 0
            return addrA - addrB
        })
)
const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)
// const configDialogVisible = ref(false)
// const configRow = ref(null)
const dataTypeMap = {
		'0': '布尔值',
		'1': 'int16',
		'2': 'int32',
		'3': 'float32',
		'4': 'float64',
		'5': '字符串'
	}

function dataTypeFormatter(row, column, cellValue) {
    if (column.property === 'dataType') {
        // 先检查是否有新类型映射
        if (dataTypeMap[cellValue]) {
            return dataTypeMap[cellValue];
        }
        // 兼容旧数据类型的显示（给用户提示这是旧格式）
        const oldTypeMap = {
            '1': '整数 (旧)',
            '2': '浮点数 (旧)',
            '3': '定点数 (旧)',
            '4': '字符串 (旧)'
        };
        return oldTypeMap[cellValue] || cellValue || '-';
    }
    if (column.property === 'modbusType') {
        // 标准 Modbus 协议分区定义
        const modbusTypeMap = {
            '0': '0区 线圈 (Coils)',
            '1': '1区 离散输入 (Discrete Inputs)',
            '3': '3区 输入寄存器 (Input Registers)',
            '4': '4区 保持寄存器 (Holding Registers)'
        };
        return modbusTypeMap[cellValue] || cellValue || '-';
    }
    return cellValue || '-';
}
async function confirmDelete() {
    if (!deleteTarget.value) return
    try {
        await api.deletevariable({
            In: {
                id: deleteTarget.value.id,
                devID: deleteTarget.value.devID,
                varName: deleteTarget.value.varName,
                dataType: deleteTarget.value.dataType,
                modbusType: deleteTarget.value.modbusType,
                modbusDevice: deleteTarget.value.modbusDevice,
                modbusAddr: deleteTarget.value.modbusAddr,
                data_len: deleteTarget.value.data_len,
                stringLen: deleteTarget.value.stringLen,
            }
        })
        if (window.ElMessage) window.ElMessage.success('删除成功')
        fetchVariables()
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('删除失败')
    }
    deleteDialogVisible.value = false
    deleteTarget.value = null
}
const editDialogVisible = ref(false)
const editRow = ref(null)

function handleEditVariable(row) {
    editRow.value = { ...row }
    editDialogVisible.value = true
}

function handleDeleteClick(row) {
    deleteTarget.value = row
    deleteDialogVisible.value = true
}

function openRemoteWrite() {
    console.log('openRemoteWrite clicked, currentDevice=', currentDevice.value)
    showRemoteWrite.value = true
    console.log('showRemoteWrite after set =', showRemoteWrite.value)
}

const variableList = ref([])
const allVariableList = ref([])
const loading = ref(false)
const dialogVisible = ref(false) // 控制新建变量对话框的显示
async function fetchVariables() {
    loading.value = true
    try {
        // 先获取变量列表
        const res = await api.getvariables({})
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            const list = res.data.data.variables.map(item => ({
                id: item.iD ?? item.id ?? '',
                devID: item.devID ?? '',
                varName: item.varName ?? '',
                dataType: item.dataType ?? '',
                modbusType: item.modbusType ?? '',
                modbusDevice: item.modbusDevice ?? '',
                modbusAddr: item.modbusAddr ?? '',
                data_len: item.data_len ?? item.dataLen ?? '',
                stringLen: item.stringLen ?? '',
                decimalDigits: item.decimalDigits ?? ''
            }))
            allVariableList.value = list
            variableList.value = list
        } else {
            allVariableList.value = []
            variableList.value = []
        }

        // 只获取设备的修改标志和成功标志
        const deviceRes = await api.getDeviceList()
        let rawList = []
        if (deviceRes.data && deviceRes.data.data && Array.isArray(deviceRes.data.data.devicelist)) {
            rawList = deviceRes.data.data.devicelist
        } else if (deviceRes.data && Array.isArray(deviceRes.data.devicelist)) {
            rawList = deviceRes.data.devicelist
        }
        deviceList.value = rawList.map(item => ({
            id: item.id,
            sn: item.DevSerial || item.serial || '',
            chengeFlag: item.chengeFlag ?? 0,
            successFlag: item.successFlag ?? 0
        }))
    } catch (e) {
        allVariableList.value = []
        variableList.value = []
    }
    loading.value = false
}

// 根据设备ID拉取变量（使用按设备ID的接口）
async function fetchVariablesByDevId(devId) {
    if (!devId) {
        allVariableList.value = []
        variableList.value = []
        return
    }
    loading.value = true
    try {
        const res = await api.getvarbydeviceid({ deviceId: devId })
        let list = []
        if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
            list = res.data.data.variables
        } else if (res.data && Array.isArray(res.data.variables)) {
            list = res.data.variables
        }
        const mapped = (list || []).map(item => ({
            id: item.iD ?? item.id ?? '',
            devID: item.devID ?? devId,
            varName: item.varName ?? '',
            dataType: item.dataType ?? '',
            modbusType: item.modbusType ?? '',
            modbusDevice: item.modbusDevice ?? '',
            modbusAddr: item.modbusAddr ?? '',
            data_len: item.data_len ?? item.dataLen ?? '',
            stringLen: item.stringLen ?? '',
            decimalDigits: item.decimalDigits ?? ''
        }))
        allVariableList.value = mapped
        variableList.value = mapped

        // 更新设备的 chengeFlag / successFlag，类似原 fetchVariables 中的做法
        const deviceRes = await api.getDeviceList()
        let rawList = []
        if (deviceRes.data && deviceRes.data.data && Array.isArray(deviceRes.data.data.devicelist)) {
            rawList = deviceRes.data.data.devicelist
        } else if (deviceRes.data && Array.isArray(deviceRes.data.devicelist)) {
            rawList = deviceRes.data.devicelist
        }
        deviceList.value = rawList.map(item => ({
            id: item.id,
            sn: item.DevSerial || item.serial || '',
            chengeFlag: item.chengeFlag ?? 0,
            successFlag: item.successFlag ?? 0
        }))
    } catch (e) {
        allVariableList.value = []
        variableList.value = []
    }
    loading.value = false
}

const tableRef = ref(null)
const selectedRows = ref([])
function handleSelectionChange(val) {
    selectedRows.value = val
}
// 回溯变量
async function handleRecoveryVariable() {
    if (!currentDevice.value) {
        if (window.ElMessage) window.ElMessage.warning('请先选择设备')
        return
    }
    try {
        // 这里假设回溯所有变量，如需单个变量可调整参数
        await api.recoveryvariable({
            devID: currentDevice.value.id,
            // varName: ,
        })
        if (window.ElMessage) window.ElMessage.success('回溯成功')
        fetchVariables()
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('回溯失败')
    }
}

// 当 props.initDevId 被传入时，优先使用按设备ID接口拉取变量
watch(
    () => props.initDevId,
    (val) => {
        if (val) {
            selectedDevID.value = String(val)
            fetchVariablesByDevId(val)
        }
    },
    { immediate: true }
)

// 当用户在页面选择设备时，使用回退逻辑或按设备接口拉取
watch(selectedDevID, (val) => {
    if (!val) return
    // 如果传入了 initDevId 并且等于当前选择的ID，优先走按id接口
    if (props.initDevId && String(props.initDevId) === String(val)) {
        fetchVariablesByDevId(val)
    } else {
        // 默认仍然使用 getvariables 全量接口并本地过滤（保持兼容）
        fetchVariables()
    }
})

onMounted(() => {
    if (props.initDevId) {
        selectedDevID.value = String(props.initDevId)
        fetchVariablesByDevId(props.initDevId)
    } else {
        fetchVariables()
    }
})
</script>
<style scoped>
.el-btn {
    color: #409EFF !important;
    font-weight: bold;
}
</style>
