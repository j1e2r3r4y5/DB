<template>
    <div class="device-list-wrapper" style="position: relative; min-height: 400px; width: 100%;">
        <el-button-group style="float: right; margin-bottom: 16px;">
            <el-button :type="viewMode === 'card' ? 'primary' : 'default'" @click="viewMode = 'card'">卡片</el-button>
            <el-button :type="viewMode === 'table' ? 'primary' : 'default'" @click="viewMode = 'table'">列表</el-button>
        </el-button-group>
        <div style="clear: both;"></div>
        <div v-if="viewMode === 'table'">
            <el-table :data="pagedDeviceList" stripe style="width: 100%; background: #fff;"
                :header-cell-style="{ color: '#222', fontWeight: 'bold' }" :row-style="rowStyle"
                @selection-change="handleSelectionChange" ref="multipleTableRef" :row-key="row => row.id">
                <el-table-column type="selection" width="50" :reserve-selection="true" />
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
                <!-- <el-table-column prop="chengeFlag" label="修改标志" min-width="120" /> -->
                <el-table-column v-if="currentUserType !== 3" label="操作" width="100" fixed="right">
                    <template #default="scope">
                        <el-dropdown trigger="hover" placement="bottom-start">
                            <span class="op-dropdown-trigger">操作</span>
                            <template #dropdown>
                                <el-dropdown-menu>
                                    <!-- <el-dropdown-item @click="handleShowVars(scope.row)">数据</el-dropdown-item> -->
                                    <el-dropdown-item @click="handleShowVars(scope.row)">变量管理</el-dropdown-item>
                                    <el-dropdown-item @click="handleEditDevice(scope.row)">编辑设备</el-dropdown-item>
                                    <el-dropdown-item @click="handleDeleteDevice(scope.row)">删除设备</el-dropdown-item>
                                    <el-dropdown-item @click="handleDownPayload(scope.row)">配置下发</el-dropdown-item>
                                    <el-dropdown-item @click="handleUpdateDevice(scope.row)">更新设备</el-dropdown-item>
                                </el-dropdown-menu>
                            </template>
                        </el-dropdown>
                    </template>
                </el-table-column>
            </el-table>
        </div>
        <div v-else-if="viewMode === 'card'" class="device-card-list">
            <div class="device-card" v-for="device in pagedDeviceList" :key="device.id">
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
                    <!-- <div>修改标志：{{ device.chengeFlag }}</div> -->
                </div>
                <div class="device-card-actions" v-if="currentUserType !== 3">
                    <el-button-group>
                        <!-- <el-button size="small" @click="handleShowVars(device)">数据</el-button> -->
                        <el-button size="small" @click="handleShowVars(device)">变量管理</el-button>
                        <el-button size="small" @click="handleEditDevice(device)">编辑设备</el-button>
                        <el-button size="small" @click="handleDownPayload(device)">配置下发</el-button>
                        <el-button size="small" @click="handleUpdateDevice(device)">更新设备</el-button>
                        <el-button size="small" type="danger" @click="handleDeleteDevice(device)">删除设备</el-button>
                    </el-button-group>
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
    <!-- <VarBydevID v-model="varDialogVisible" :device-id="currentDeviceId" /> -->
    <!-- 下发配置弹窗 -->
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
const bytetypeMap = {
    '00': '0区',
    '01': '1区',
    '02': '2区',
    '03': '3区',
    '04': '4区'
}
import { ref, onMounted, computed, nextTick } from 'vue'
import api from '../api'
import DeviceDownDialog from './DeviceDownDialog.vue'
import Pagination from '../composables/Pagination.vue'
import { ElMessage } from 'element-plus'
const multipleTableRef = ref(null)
const selectedRows = ref([]) // 存储跨页选中的行
const viewMode = ref('card') // 默认展示卡片模式
// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [5, 10, 20, 50, 100]
function handlePageChange(page) {
    currentPage.value = page
    // 页面切换时，恢复已选中的行
    nextTick(() => {
        restoreSelectedRows()
    })
}

function handleSizeChange(size) {
    pageSize.value = size
    currentPage.value = 1 // 切换每页条数时回到第一页
    // 每页条数变化时，恢复已选中的行
    nextTick(() => {
        restoreSelectedRows()
    })
}

// 处理表格选中项改变
function handleSelectionChange(selection) {
    // 更新当前页选中项到全局选中数组
    updateSelectedRows(selection)
    // 向父组件发出事件，保持原有功能
    emit('selection-change', selectedRows.value)
}

// 更新全局选中数组
function updateSelectedRows(selection) {
    // 先从全局选中数组中移除当前页的所有行
    const currentPageIds = new Set(pagedDeviceList.value.map(row => row.id))
    selectedRows.value = selectedRows.value.filter(row => !currentPageIds.has(row.id))

    // 添加当前选中的行到全局选中数组
    selection.forEach(row => {
        if (!selectedRows.value.find(item => item.id === row.id)) {
            selectedRows.value.push(row)
        }
    })
}
function handleUpdateDevice(row) {
    ElMessage.info('正在查询设备配置...')
    api.downpayload({
        Serial: row.sn,
        Code: '01'
    }).then(() => {
        ElMessage.success('更新命令已下发')
        fetchDeviceList()
    }).catch(() => {
        ElMessage.error('下发失败')
    })
}
function restoreSelectedRows() {
    if (!multipleTableRef.value) return

    // 清除表格当前选中状态
    multipleTableRef.value.clearSelection()

    // 对当前页的每一行，如果在全局选中数组中存在，则选中
    pagedDeviceList.value.forEach(row => {
        if (selectedRows.value.find(item => item.id === row.id)) {
            multipleTableRef.value.toggleRowSelection(row, true)
        }
    })
}

// 计算分页后的数据
const pagedDeviceList = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return deviceList.value.slice(start, end)
})
// import { defineExpose } from 'vue'
const editDialogVisible = ref(false)
const emit = defineEmits(['selection-change', 'open-variables'])

// 点击变量按钮时，发出事件让父组件切换到变量页并传入设备 ID
function handleShowVars(row) {
    emit('open-variables', row.id)
}
const editForm = ref({
    id: '',
    name: '',
    sn: '',
    location: '',
    sendmodel: '',
    configdata: '',
    baud: '',
})
defineExpose({ fetchDeviceList })
const deviceList = ref([])
function rowStyle() { return { height: '56px' } }

// 获取当前用户类型
let currentUserType = 0
try {
    currentUserType = Number(localStorage.getItem('userType')) || 0
} catch (e) { }
// 保留弹窗用的 handleDownPayload，已删除旧的直接下发版本
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
            config: item.Config || item.config || item.configdata || '',
            baud: item.Baud || item.baud || '',
            chengeFlag: item.chengeFlag ?? 0,
            successFlag: item.successFlag ?? 0,
        }))
        // console.log('设备列表:', deviceList.value)
        // 刷新后恢复复选框状态
        nextTick(() => {
            restoreSelectedRows()
        })
    } catch (e) {
        deviceList.value = []
    }
}
// 编辑按钮点击
function handleEditDevice(row) {
    editDialogVisible.value = true
    editForm.value = { ...row } // 填充当前设备信息
}
const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)
// 删除按钮点击
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
    // 初始页面加载后，设置页面内容
    nextTick(() => {
        restoreSelectedRows()
    })
})
// 新建按钮示例（如有新建按钮请加 v-if="currentUserType !== 3"）
</script>
<style scoped>
/* 防止侧边栏折叠时内容横向溢出 */
.device-list-wrapper {
    box-sizing: border-box;
    overflow-x: hidden;
    width: 100%;
}

.device-list-wrapper>* {
    min-width: 0;
}

/* 卡片模式美化：改为 grid 布局，避免行尾空白 */
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

.device-card-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

.device-card-actions .el-button-group {
    gap: 0;
}

.op-dropdown-trigger {
    color: #409EFF;
    font-weight: bold;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background 0.2s;
}

.op-dropdown-trigger:hover {
    background: #f0f7ff;
}

::v-deep(.el-dropdown-menu__item) {
    color: #409EFF !important;
    font-weight: bold;
}

::v-deep(.el-dropdown-menu__item:hover) {
    background: #f0f7ff;
    color: #1765c1 !important;
}

.device-table-scroll {
    flex: 1 1 auto;
    overflow-y: auto;
    min-height: 0;
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