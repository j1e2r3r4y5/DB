<template>
    <el-container style="height: 100vh;">
        <el-aside :width="collapsed ? '64px' : '180px'" class="sidebar">
            <div class="logo" @click="collapsed = !collapsed" style="cursor:pointer;">
                <span class="logo-icon">🛡️</span>
            </div>
            <nav class="nav">
                <div class="nav-item" :class="{ active: currentMenu === 'home' }" @click="currentMenu = 'home'">
                    <span class="nav-icon">🏠</span>
                    <span v-if="!collapsed">主页</span>
                </div>
                <div v-if="userType !== 3" class="nav-item" :class="{ active: currentMenu === 'device' }"
                    @click="currentMenu = 'device'">
                    <span class="nav-icon">🧑‍🔧</span>
                    <span v-if="!collapsed">设备管理</span>
                </div>
                <div class="nav-item" :class="{ active: currentMenu === 'devlist' }" @click="currentMenu = 'devlist'">
                    <span class="nav-icon">📊</span>
                    <span v-if="!collapsed">设备列表</span>
                </div>
                <!-- <div class="nav-item" :class="{ active: currentMenu === 'data' }" @click="currentMenu = 'data'">
                    <span class="nav-icon">📋</span>
                    <span v-if="!collapsed">数据列表</span>
                </div> -->
                <div v-if="userType === 0 || userType === 1" class="nav-item"
                    :class="{ active: currentMenu === 'user' }" @click="currentMenu = 'user'">
                    <span class="nav-icon">👤</span>
                    <span v-if="!collapsed">用户管理</span>
                </div>
            </nav>
        </el-aside>
        <el-container>
            <el-header class="main-header">
                <div class="header-title" style="display: flex; align-items: center; gap: 10px;">
                    <span class="header-arrow"
                        :style="{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s', cursor: 'pointer', fontSize: '0.8rem', color: '#223147', marginLeft: '-2px', marginRight: '12px' }"
                        @click="collapsed = !collapsed">
                        < </span>
                            <template v-if="currentMenu === 'home'">综合管理平台</template>
                            <template v-else-if="currentMenu === 'device'">设备管理</template>
                            <template v-else-if="currentMenu === 'variable'">变量管理</template>
                            <template v-else-if="currentMenu === 'devlist'">设备列表</template>
                            <template v-else-if="currentMenu === 'data'">数据管理</template>
                            <template v-else-if="currentMenu === 'user'">用户管理</template>

                </div>
                <div class="dropdown" @mouseenter="showDropdown = true" @mouseleave="showDropdown = false">
                    <span class="dropdown-trigger">个人</span>
                    <div class="dropdown-menu" v-if="showDropdown">
                        <button class="dropdown-button" @click="showChangePwd">修改密码</button>
                        <Modifuser v-model:visible="changePwdVisible" @success="handlePwdSuccess" />
                        <button class="dropdown-button" @click="handleLogout">登出</button>
                    </div>
                </div>
                <!-- </div> -->
            </el-header>
            <el-main class="content-area">
                <template v-if="currentMenu === 'home'">
                    <h2>主页暂无内容敬请期待</h2>
                </template>
                <template v-else-if="currentMenu === 'device'">
                    <div class="device-table-wrapper">
                        <div
                            style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <div>
                                <el-button v-if="userType !== 3" class="my-create-btn" type="primary"
                                    @click="handleCreateDevice">新建设备</el-button>
                                <el-button type="primary" style="margin-left: 12px;"
                                    @click="handleRefreshDevice">刷新页面</el-button>
                                <el-button type="danger" style="margin-left: 12px;"
                                    :disabled="!multipleSelection.length" @click="handleBatchDelete">删除设备</el-button>
                                <el-button type="warning" style="margin-left: 12px;"
                                    :disabled="!multipleSelection.length" @click="handleConfigAll">配置下发</el-button>
                            </div>
                            <DeviceAdd v-model:visible="dialogVisible" @success="handleDeviceAddSuccess" />
                        </div>
                        <DeviceContent ref="deviceContentRef" @selection-change="handleSelectionChange"
                            @open-variables="openVariables" />
                        <DeviceDownDialog v-model="downDialogVisible" :rows="selectedRows"
                            @success="handleDownSuccess" />
                    </div>
                </template>
                <template v-else-if="currentMenu === 'variable'">
                    <Variables :dev-id="variablesDevId" @back-to-device="currentMenu = 'device'" />
                </template>
                <template v-else-if="currentMenu === 'devlist'">
                    <div class="device-table-wrapper">
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                            <el-button type="primary" style="width: 120px;"
                                @click="handleRefreshDevice">刷新页面</el-button>
                        </div>
                        <Devlist @open-data-list="handleOpenDataList" />
                    </div>
                </template>
                <template v-else-if="currentMenu === 'user'">
                    <div class="device-table-wrapper">
                        <Administrator ref="administratorRef" />
                    </div>
                </template>
                <template v-else-if="currentMenu === 'data'">
                    <!-- <h2>数据列表</h2> -->
                    <Data :dev-id="dataDevId" @back-to-devlist="currentMenu = 'devlist'" />
                </template>
            </el-main>
        </el-container>
    </el-container>
</template>
<script setup>
import api from '../api'
import DeviceContent from '../components/device.vue'
import Administrator from '../components/Administrator.vue'
import DeviceAdd from '../components/deviceadd.vue'
import Modifuser from '../components/Modifuser.vue'
import Variables from '../components/variables/variables.vue'
import Devlist from '../components/devlist.vue'
import Data from '../components/data/data.vue'
import { ref, watch, onMounted, onUnmounted, provide } from 'vue'
import DeviceDownDialog from '../components/DeviceDownDialog.vue'
const downDialogVisible = ref(false)
const selectedRows = ref([])
const deviceList = ref([]) // 设备列表
const dataDevId = ref('')
function handleOpenDataList(deviceId) {
    dataDevId.value = deviceId
    currentMenu.value = 'data'
}
// 提供设备列表给子组件
provide('deviceList', deviceList)

function handleConfigAll() {
    if (!multipleSelection.value.length) return
    selectedRows.value = multipleSelection.value.slice()
    downDialogVisible.value = true
}
function handleDownSuccess() {
    if (deviceContentRef.value && deviceContentRef.value.fetchDeviceList) {
        deviceContentRef.value.fetchDeviceList()
    }
    downDialogVisible.value = false
}
const currentMenu = ref(localStorage.getItem('currentMenu') || 'home');
const userType = Number(localStorage.getItem('userType') || 0);
const userId = Number(localStorage.getItem('userId')) // 或你的用户ID获取方式
// console.log('当前用户ID:', userId)
// console.log('currentMenu:', currentMenu.value);
const changePwdVisible = ref(false)
function showChangePwd() { changePwdVisible.value = true }
function handlePwdSuccess() { /* 可加成功提示 */ }
const collapsed = ref(false);
const deviceContentRef = ref(null)
const administratorRef = ref(null)
const dialogVisible = ref(false)
const showDropdown = ref(false)
const variablesDevId = ref('') // 用于传递给变量页面的设备ID
function handleCreateDevice() {
    dialogVisible.value = true
}

function openVariables(devId) {
    // 接收到设备组件传来的设备ID，切换到变量页并传入ID
    variablesDevId.value = devId
    currentMenu.value = 'variable'
}

function handleRefreshDevice() {
    if (deviceContentRef.value && deviceContentRef.value.fetchDeviceList) {
        deviceContentRef.value.fetchDeviceList()
    }
    // 同时更新 provide 的设备列表
    fetchDeviceListForProvider()
}

// 获取设备列表用于 provide
async function fetchDeviceListForProvider() {
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

watch(currentMenu, (val) => {
    localStorage.setItem('currentMenu', val);
});
let timer = null
let isPageVisible = true

onMounted(() => {
    fetchDeviceListForProvider()
    document.addEventListener('visibilitychange', () => {
        isPageVisible = document.visibilityState === 'visible'
    })
    timer = setInterval(() => {
        if (!isPageVisible) return
        if (currentMenu.value === 'device' && deviceContentRef.value?.fetchDeviceList) {
            deviceContentRef.value.fetchDeviceList()
        }
        if (currentMenu.value === 'user' && administratorRef.value?.fetchUserList) {
            administratorRef.value.fetchUserList()
        }
        fetchDeviceListForProvider()
    }, 15000)
})
function handleDeviceAddSuccess() {
    if (deviceContentRef.value && deviceContentRef.value.fetchDeviceList) {
        deviceContentRef.value.fetchDeviceList()
    }
    // 同时更新 provide 的设备列表
    fetchDeviceListForProvider()
}
const multipleSelection = ref([])
function handleSelectionChange(val) {
    multipleSelection.value = val
}
async function handleBatchDelete() {
    if (!multipleSelection.value.length) return
    if (!window.confirm('确定要批量删除选中的设备吗？')) return
    const idList = multipleSelection.value.map(item => item.id)
    try {
        const res = await api.DeleteDevice({ Idlist: idList })
        if (res.data && res.data.code === 0) {
            window.$message ? window.$message.success('删除成功') : alert('删除成功')
            if (deviceContentRef.value && deviceContentRef.value.fetchDeviceList) {
                deviceContentRef.value.fetchDeviceList()
            }
            // 同时更新 provide 的设备列表
            fetchDeviceListForProvider()
            multipleSelection.value = []
        } else {
            window.$message ? window.$message.error(res.data?.message || '删除失败') : alert(res.data?.message || '删除失败')
        }
    } catch (e) {
        window.$message ? window.$message.error('请求失败') : alert('请求失败')
    }
}
async function handleLogout() {
    if (window.confirm('确定要退出登录吗？')) {
        try {
            await api.logout()
        } catch (e) {
            // 可选：处理接口异常
        }
        localStorage.removeItem('userId');
        localStorage.removeItem('userType');
        localStorage.removeItem('token');
        window.location.href = '/login'; // 跳转到登录页
    }
}
onUnmounted(() => {
    if (timer) clearInterval(timer)
})
</script>
<style scoped>
.main-layout {
    display: flex;
    height: 100vh;
    width: 100vw;
    background: #f8f9fa;
}

.sidebar {
    background: #223147;
    color: #fff;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 24px;
    transition: width 0.2s;
    overflow: hidden;
}

.logo {
    margin-bottom: 32px;
}

.logo-icon {
    font-size: 2.5rem;
}

.nav {
    width: 100%;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 24px;
    font-size: 1.15rem;
    cursor: pointer;
    transition: background 0.2s;
}

.nav-item:hover {
    background: #2c3e5a;
}

.nav-icon {
    font-size: 1.3rem;
}

.nav-arrow {
    margin-left: auto;
    font-size: 1rem;
}

.main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.device-table {
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    margin-top: 8px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.device-table th,
.device-table td {
    padding: 12px 8px;
    border-bottom: 1px solid #eee;
    text-align: left;
    font-size: 15px;
}

.device-table th {
    background: #f5f7fa;
    font-weight: 600;
}

.main-header {
    height: 56px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 32px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.header-title {
    font-size: 1.5rem;

    .nav-item.active {
        background: #31415a;
    }

    font-weight: bold;
    color: #223147;
}

.header-user {
    font-size: 1.1rem;
    color: #223147;
}

.content-area {
    flex: 1;
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;
    padding-top: 32px;
    box-sizing: border-box;
    width: 100%;
}

.content-area h2 {
    color: #223147;
    font-size: 1.3rem;
    font-weight: bold;
}

/* 表格外层容器样式，可自定义边框、阴影等 */
.device-table-wrapper {
    background: #ffffff;
    border-radius: 15px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
    padding: 18px 18px 8px 18px;
    margin-bottom: 32px;
    width: 100%;
    min-height: 600px;
    max-height: 700px;
    /* 固定最大高度，可根据需要调整 */
    height: 700px;
    /* 固定高度，内容溢出自动滚动 */
    overflow-y: auto;
    overflow-x: hidden;
    /* 禁止横向滚动 */
    /* 内容超出时滚动 */
    display: flex;
    flex-direction: column;
    /* 容器宽度始终填满内容区 */
}

.device-table-wrapper>* {
    min-width: 0;
    /* 允许子元素在 flex 容器里收缩，避免撑开父容器 */
}

.my-create-btn {
    background: #32c273;
    color: #fff;
    /* border-radius: 8px; */
    font-size: 16px;
}

.dropdown {
    position: relative;
    display: inline-block;
}

.dropdown-menu {
    position: absolute;
    right: 0;
    top: 100%;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    border-radius: 6px;
    min-width: 120px;
    z-index: 10;
    display: block;
    gap: 8px;
    padding: 8px 12px;
}

.dropdown-menu button:hover {
    background: #fff8f8;
}

.dropdown-button {
    background: #ffffff;
    color: #223147;
    cursor: pointer;
    border-radius: 6px;
    padding: 10px 24px;
    width: 120px;
    /* 固定宽度，按钮长度不会跟着字体变 */
    text-align: center;
}
</style>
