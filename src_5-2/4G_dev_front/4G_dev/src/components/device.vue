<template>
    <div class="device-list-wrapper" style="position: relative; min-height: 400px; width: 100%;">
        <el-alert
            v-if="activeOp"
            :title="`${opLabels[activeOp] || activeOp} 模式`"
            type="warning"
            show-icon
            :closable="true"
            @close="exitOpMode"
            style="margin-bottom: 16px;">
            <template #default>
                <span>点击列表中任意设备即可{{ opLabels[activeOp] || activeOp }}（可连续操作，关闭此提示退出模式）</span>
            </template>
        </el-alert>
        <el-button-group style="float: right; margin-bottom: 16px;">
            <el-button :type="viewMode === 'card' ? 'primary' : 'default'" @click="viewMode = 'card'">卡片</el-button>
            <el-button :type="viewMode === 'table' ? 'primary' : 'default'" @click="viewMode = 'table'">列表</el-button>
        </el-button-group>
        <div style="clear: both;"></div>
        <div v-if="viewMode === 'table'">
            <el-table :data="pagedDeviceList" stripe style="width: 100%; background: #fff;"
                :header-cell-style="{ color: '#222', fontWeight: 'bold' }" :row-style="rowStyle"
                @row-click="handleRowClick" ref="multipleTableRef" :row-key="row => row.id">
                <el-table-column prop="name" label="设备名称" min-width="150" />
                <el-table-column prop="sn" label="设备序列号" min-width="150" />
                <el-table-column prop="location" label="设备位置" min-width="150" />
                <el-table-column prop="status" label="设备状态" min-width="120">
                    <template #default="scope">
                        <span :style="{ color: scope.row.status === '离线' ? 'red' : 'green' }">{{ scope.row.status
                        }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="lastOnline" label="最后在线时间" min-width="180" />
                <el-table-column prop="sendmodel" label="发送模式" min-width="120" />
                <el-table-column prop="config" label="数据配置" min-width="120" />
                <el-table-column prop="baud" label="波特率" min-width="120">
                    <template #default="scope">
                        {{ baudMap[scope.row.baud] || scope.row.baud }}
                    </template>
                </el-table-column>
                <el-table-column v-if="currentUserType !== 3" label="编辑设备" min-width="80" align="center">
                    <template #default="scope">
                        <span class="action-link" @click.stop="handleEditDevice(scope.row)">编辑设备</span>
                    </template>
                </el-table-column>
                <el-table-column v-if="currentUserType !== 3" label="配置下发" min-width="80" align="center">
                    <template #default="scope">
                        <span class="action-link" @click.stop="handleDownPayload(scope.row)">配置下发</span>
                    </template>
                </el-table-column>
                <el-table-column v-if="currentUserType !== 3" label="更新设备" min-width="80" align="center">
                    <template #default="scope">
                        <span class="action-link" @click.stop="handleUpdateDevice(scope.row)">更新设备</span>
                    </template>
                </el-table-column>
                <el-table-column v-if="currentUserType !== 3" label="删除设备" min-width="80" align="center">
                    <template #default="scope">
                        <span class="action-link danger" @click.stop="handleDeleteDevice(scope.row)">删除设备</span>
                    </template>
                </el-table-column>
            </el-table>
        </div>
        <div v-else-if="viewMode === 'card'" class="device-card-list">
            <div class="device-card" v-for="device in pagedDeviceList" :key="device.id" @click="handleCardClick(device)" style="cursor: pointer;">
                <div class="device-card-header">
                    <span class="device-card-title">{{ device.name }}</span>
                    <span class="device-card-status" :style="{ color: device.status === '离线' ? 'red' : 'green' }">{{
                        device.status }}</span>
                </div>
                <div class="device-card-body">
                    <div>序列号：{{ device.sn }}</div>
                    <div>位置：{{ device.location }}</div>
                    <div>最后在线：{{ device.lastOnline }}</div>
                    <div>发送模式：{{ device.sendmodel }}</div>
                    <div>{{ device.sendmodel === '00' ? '定时发送' : '触发地址' }}：{{ device.config }}</div>
                    <div>波特率：{{ baudMap[device.baud] || device.baud }}</div>
                </div>
            </div>
        </div>
    </div>
    <div class="pagination-bottom">
        <Pagination :total="deviceList.length" :page-size="pageSize" :current-page="currentPage" :page-sizes="pageSizes"
            @size-change="handleSizeChange" @current-change="handlePageChange" />
    </div>
    <el-dialog v-model="editDialogVisible" title="编辑设备" width="460px">
        <el-form :model="editForm" label-width="120px">
            <el-form-item label="设备名称">
                <el-input v-model="editForm.name" />
            </el-form-item>
            <el-form-item label="序列号">
                <el-input v-model="editForm.sn" />
            </el-form-item>
            <el-form-item label="位置">
                <el-input v-model="editForm.location" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleSaveEdit">保存</el-button>
        </template>
    </el-dialog>
    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="320px">
        <div style="font-size:16px;">确定要删除该设备吗？</div>
        <template #footer>
            <el-button @click="deleteDialogVisible = false">取消</el-button>
            <el-button type="danger" @click="confirmDeleteDevice">删除</el-button>
        </template>
    </el-dialog>
    <DeviceDownDialog v-model="downDialogVisible" :row="downRow" @success="handleDownSuccess" />
</template>

<script setup>
const baudMap = {
    '00': '300',
    '01': '600',
    '02': '1200',
    '03': '2400',
    '04': '4800',
    '05': '9600',
    '06': '14400',
    '07': '19200',
    '08': '28800',
    '09': '38400',
    '0A': '57600',
    '0B': '76800',
    '0C': '115200',
    '0D': '230400',
    '0E': '460800',
    '0F': '921600'
}
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import DeviceDownDialog from './DeviceDownDialog.vue'
import Pagination from '../composables/Pagination.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
const multipleTableRef = ref(null)
const viewMode = ref('card')
const route = useRoute()
const router = useRouter()

const activeOp = ref('')
const opLabels = {
  edit: '编辑设备',
  config: '配置下发',
  update: '更新设备',
  delete: '删除设备'
}

function exitOpMode() {
  activeOp.value = ''
  router.replace('/home/devices')
}

watch(() => route.query.op, (op) => {
  activeOp.value = op || ''
  if (op) {
    ElMessage.info({
      message: `已进入「${opLabels[op] || op}」模式，点击列表中或卡片任意设备即可${opLabels[op] || op}（可连续操作）`,
      duration: 4000
    })
  }
}, { immediate: true })

function handleRowClick(row) {
  if (!activeOp.value) return
  const op = activeOp.value
  executeOperation(op, row)
}

function handleCardClick(row) {
  handleRowClick(row)
}

function executeOperation(op, row) {
  if (op === 'edit') {
    handleEditDevice(row)
  } else if (op === 'config') {
    handleDownPayload(row)
  } else if (op === 'update') {
    ElMessage.info(`正在更新设备「${row.name}」...`)
    handleUpdateDevice(row)
  } else if (op === 'delete') {
    deleteTarget.value = row
    deleteDialogVisible.value = true
  }
}

const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [5, 10, 20, 50, 100]
function handlePageChange(page) {
    currentPage.value = page
}

function handleSizeChange(size) {
    pageSize.value = size
    currentPage.value = 1
}

const pagedDeviceList = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return deviceList.value.slice(start, end)
})

const editDialogVisible = ref(false)

const editForm = ref({
    id: '',
    name: '',
    sn: '',
    location: '',
    sendmodel: '',
    configdata: '',
    baud: '',
})
const deviceList = ref([])
function rowStyle() { return { height: '56px' } }

let currentUserType = 0
try {
    currentUserType = Number(localStorage.getItem('userType')) || 0
} catch (e) { }

async function fetchDeviceList() {
    try {
        const res = await api.getDeviceList()
        let list = []
        if (res.data && res.data.code === 0) {
            if (res.data.data && res.data.data.devicelist) {
                list = res.data.data.devicelist
            } else if (res.data.devicelist) {
                list = res.data.devicelist
            }
        }
        deviceList.value = (list || []).map((item, idx) => ({
            id: item.id || idx,
            name: item.Devname || item.name || '',
            sn: item.DevSerial || item.serial || '',
            location: item.DevLocation || item.location || '',
            status: item.DevStatus === 1 || item.DevStatus === '1' || item.status === 1 || item.status === '1' ? '在线' : '离线',
            lastOnline: item.LatestOnline || item.latest_online || '无记录',
            sendmodel: item.Sendmodel || item.sendmodel || item.send_model || '',
            config: item.Config || item.config || item.configdata ?
                (item.configdata || item.config) : '',
            baud: item.Baud || item.baud || '',
            chengeFlag: item.chengeFlag ?? 0,
            successFlag: item.successFlag ?? 0,
        }))
    } catch (e) {
        deviceList.value = []
    }
}

function handleEditDevice(row) {
    editDialogVisible.value = true
    editForm.value = { ...row }
}
const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)
function handleDeleteDevice(row) {
    deleteTarget.value = row
    deleteDialogVisible.value = true
}
async function confirmDeleteDevice() {
    if (!deleteTarget.value) return
    const res = await api.DeleteDevice({ Idlist: [deleteTarget.value.id] })
    if (res.data && res.data.code === 0) {
        fetchDeviceList()
    }
    deleteDialogVisible.value = false
    deleteTarget.value = null
}
async function handleSaveEdit() {
    const data = {
        ID: editForm.value.id,
        Devname: editForm.value.name,
        DevSerial: editForm.value.sn,
        DevLocation: editForm.value.location,
        Sendmodel: editForm.value.sendmodel,
        Configdata: editForm.value.config,
        Baud: editForm.value.baud,
    }
    const res = await api.ModifyDevice(data)
    if (res.data && res.data.code === 0) {
        editDialogVisible.value = false
        fetchDeviceList()
    }
}
function handleUpdateDevice(row) {
    api.downpayload({
        serial: row.sn,
        code: '01'
    }).then(() => {
        ElMessage.success('更新命令已下发')
    }).catch(() => {
        ElMessage.error('下发失败')
    })
}
const downDialogVisible = ref(false)
const downRow = ref(null)
function handleDownPayload(row) {
    downRow.value = row
    downDialogVisible.value = true
}
function handleDownSuccess() {
    fetchDeviceList()
}
onMounted(() => {
    fetchDeviceList()
})
</script>
<style scoped>
.device-list-wrapper {
    box-sizing: border-box;
    overflow-x: hidden;
    width: 100%;
}

.device-list-wrapper>* {
    min-width: 0;
}

.device-card-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    padding: 12px;
    box-sizing: border-box;
    width: 100%;
    min-height: 140px;
}

.device-card {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
    border: 1px solid #e5e6eb;
    padding: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: box-shadow 0.2s;
    box-sizing: border-box;
    width: 100%;
    min-height: 140px;
}

.device-card:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.16);
    border-color: #409eff;
}

.device-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.device-card-title {
    font-size: 15px;
    font-weight: bold;
    color: #222;
}

.device-card-status {
    font-size: 13px;
    font-weight: bold;
}

.device-card-body {
    font-size: 13px;
    color: #555;
    margin-bottom: 8px;
    line-height: 1.6;
}

.action-link {
    color: #409EFF;
    cursor: pointer;
    font-size: 13px;
    white-space: nowrap;
    padding: 2px 4px;
    border-radius: 3px;
    transition: all 0.2s;
    user-select: none;
}

.action-link:hover {
    background: #ecf5ff;
    color: #2a7de1;
}

.action-link.danger {
    color: #f56c6c;
}

.action-link.danger:hover {
    background: #fef0f0;
    color: #d94a4a;
}

.pagination-bottom {
    width: 100%;
    display: flex;
    justify-content: center;
    background: transparent;
    margin-top: auto;
    padding: 12px 0 8px 0;
}
</style>
