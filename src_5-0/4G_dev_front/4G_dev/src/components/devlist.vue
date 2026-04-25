<template>
    <div class="device-list-wrapper">
        <el-button-group style="float: right; margin-bottom: 12px;">
            <el-button :type="viewMode === 'card' ? 'primary' : 'default'" @click="viewMode = 'card'">卡片</el-button>
            <el-button :type="viewMode === 'table' ? 'primary' : 'default'" @click="viewMode = 'table'">列表</el-button>
        </el-button-group>
        <div style="clear: both;"></div>
        <div class="device-table-scroll">
            <div v-if="viewMode === 'table'">
                <el-table :data="pagedDeviceList" stripe style="width: 100%; background: #fff;"
                    :header-cell-style="{ color: '#222', fontWeight: 'bold' }" :row-style="rowStyle"
                    ref="multipleTableRef" :row-key="row => row.id">
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
                    <el-table-column v-if="currentUserType !== 3" label="操作" width="100" fixed="right">
                        <template #default="scope">
                            <el-button size="small" type="primary"
                                @click="handleGotoDataList(scope.row.id)">数据列表</el-button>
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
                    </div>
                    <div class="device-card-actions">
                        <el-button-group>
                            <el-button size="small" type="primary"
                                @click="handleGotoDataList(device.id)">数据列表</el-button>
                        </el-button-group>
                    </div>
                </div>
            </div>
        </div>
        <div class="pagination-bottom">
            <Pagination :total="deviceList.length" :page-size="pageSize" :current-page="currentPage"
                :page-sizes="pageSizes" @size-change="handleSizeChange" @current-change="handlePageChange" />
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import Pagination from '../composables/Pagination.vue'
const baudMap = {
    '00': '300', '01': '600', '02': '1200', '03': '2400', '04': '4800', '05': '9600',
    '06': '14400', '07': '19200', '08': '28800', '09': '38400', '0A': '57600',
    '0B': '76800', '0C': '115200', '0D': '230400', '0E': '460800', '0F': '921600'
}
let currentUserType = 0
try {
    currentUserType = Number(localStorage.getItem('userType')) || 0
} catch (e) { }
const viewMode = ref('card')
const multipleTableRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [5, 10, 20, 50, 100]
const deviceList = ref([])
const pagedDeviceList = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return deviceList.value.slice(start, end)
})
function rowStyle() { return { height: '56px' } }
function handlePageChange(page) { currentPage.value = page }
function handleSizeChange(size) { pageSize.value = size; currentPage.value = 1 }
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
    } catch (e) {
        deviceList.value = []
    }
}
onMounted(fetchDeviceList)
const emit = defineEmits(["open-data-list"])
function handleGotoDataList(id) {
    emit("open-data-list", id)
}
</script>
<style scoped>
.device-card-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    padding: 12px;
    box-sizing: border-box;
    width: 100%;
    min-height: 140px;
}

.device-table-scroll {
    flex: 1 1 auto;
    overflow-y: auto;
    min-height: 0;
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

.pagination-bottom {
    width: 100%;
    display: flex;
    justify-content: center;
    background: transparent;
    margin-top: auto;
    padding: 12px 0 8px 0;
}

.device-list-wrapper {
    display: flex;
    flex-direction: column;
    height: 700px;
    box-sizing: border-box;
    overflow-x: hidden;
}

.device-list-wrapper>* {
    min-width: 0;
}

/* 防止侧边栏折叠时横向溢出 */
.device-list-wrapper {
    box-sizing: border-box;
    overflow-x: hidden;
    width: 100%;
}

.device-list-wrapper>* {
    min-width: 0;
}
</style>
