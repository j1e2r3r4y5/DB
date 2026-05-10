<template>
  <el-container style="height: 100vh;">
    <el-aside :width="collapsed ? '64px' : '200px'" class="sidebar">
      <div class="logo" @click="collapsed = !collapsed">
        <el-icon :size="28"><Monitor /></el-icon>
        <span v-if="!collapsed" class="logo-text">IoT平台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="#223147"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/home/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>主页</template>
        </el-menu-item>
        
        <el-sub-menu index="device" v-if="userStore.userType !== 3">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>设备管理</span>
          </template>
          <el-menu-item index="/home/devices">
            <el-icon><List /></el-icon>
            <template #title>设备列表</template>
          </el-menu-item>
          <el-menu-item index="/home/devices/add">
            <el-icon><Plus /></el-icon>
            <template #title>新建设备</template>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/home/devlist">
          <el-icon><DataLine /></el-icon>
          <template #title>设备列表</template>
        </el-menu-item>

        <el-menu-item index="/home/users" v-if="userStore.isAdmin">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <el-icon 
            class="collapse-btn" 
            :size="20"
            @click="collapsed = !collapsed"
          >
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <span class="header-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-icon><UserFilled /></el-icon>
              <span>个人</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">
                  <el-icon><Edit /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
    
    <Modifuser v-model:visible="changePwdVisible" @success="handlePwdSuccess" />
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore, useDeviceStore } from '../stores'
import Modifuser from '../components/Modifuser.vue'
import api from '../api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const deviceStore = useDeviceStore()

const collapsed = ref(false)
const changePwdVisible = ref(false)

const activeMenu = computed(() => {
  return route.path
})

const pageTitle = computed(() => {
  const titles = {
    '/home/dashboard': '监控大屏',
    '/home/devices': '设备管理',
    '/home/devices/add': '新建设备',
    '/home/devlist': '设备列表',
    '/home/variables': '变量管理',
    '/home/data': '数据管理',
    '/home/users': '用户管理'
  }
  return titles[route.path] || route.meta?.title || '工业物联网平台'
})

function handleCommand(command) {
  if (command === 'password') {
    changePwdVisible.value = true
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      try {
        await api.logout()
      } catch (e) {}
      userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}

function handlePwdSuccess() {
  ElMessage.success('密码修改成功')
}

let timer = null
onMounted(() => {
  deviceStore.fetchDevices()
  timer = setInterval(() => {
    deviceStore.fetchDevices()
  }, 15000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.sidebar {
  background: #223147;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
  white-space: nowrap;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.main-header {
  height: 60px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #223147;
  transition: transform 0.3s;
}

.collapse-btn:hover {
  color: #409EFF;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #223147;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #223147;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-dropdown:hover {
  background: #f5f7fa;
}

.content-area {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
