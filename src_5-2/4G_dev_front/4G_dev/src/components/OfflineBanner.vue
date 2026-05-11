<template>
  <div class="offline-banner" v-if="!isOnline">
    <el-icon><WarningFilled /></el-icon>
    <span>网络已断开，请检查网络连接</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const isOnline = ref(navigator.onLine)

function handleOnline() {
  isOnline.value = true
}

function handleOffline() {
  isOnline.value = false
}

onMounted(() => {
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped>
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(90deg, #f56c6c 0%, #e6a23c 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  z-index: 9999;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
  }
  to {
    transform: translateY(0);
  }
}
</style>
