<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48" color="#409EFF"><Monitor /></el-icon>
        </div>
        <h1 class="title">工业物联网管理平台</h1>
        <p class="subtitle">Industrial IoT Management Platform</p>
      </div>
      
      <el-form class="login-form" @submit.prevent="handleLogin" :model="form" :rules="rules" ref="formRef">
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入用户名" 
            clearable 
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码" 
            clearable
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <div class="captcha-row">
            <el-input 
              v-model="form.captcha" 
              placeholder="请输入验证码" 
              size="large"
              :prefix-icon="Key"
              style="flex: 1"
            />
            <div class="captcha-img" @click="refreshCaptcha">
              <span class="captcha-text">{{ captchaText }}</span>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="form.remember">记住密码</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            style="width: 100%" 
            @click="handleLogin"
            :loading="loading"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p class="version">v2.0.0</p>
        <p class="copyright">© 2026 工业物联网平台</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Key, Monitor } from '@element-plus/icons-vue'
import api from '../api'
import { useUserStore } from '../stores'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const captchaText = ref('ABCD')

const form = reactive({
  username: '',
  password: '',
  captcha: '',
  remember: false
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function generateCaptcha() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let result = ''
  for (let i = 0; i < 4; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

function refreshCaptcha() {
  captchaText.value = generateCaptcha()
}

async function handleLogin() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const res = await api.login({
        username: form.username,
        password: form.password
      })
      
      if (res.data.code === 0) {
        ElMessage.success('登录成功！')
        userStore.setUser(res.data.data)
        
        if (form.remember) {
          localStorage.setItem('rememberedUser', form.username)
        } else {
          localStorage.removeItem('rememberedUser')
        }
        
        router.push('/home/dashboard')
      } else {
        if (res.data.code === 53) {
          ElMessage.error(res.data.msg || '账号或密码错误')
        } else if (res.data.code === 54) {
          ElMessage.error('账号已被禁用')
        } else {
          ElMessage.error(res.data.msg || res.data.message || '登录失败')
        }
        refreshCaptcha()
      }
    } catch (error) {
      console.error('登录失败:', error)
      if (!error.response) {
        ElMessage.error('网络异常，请检查后端服务是否运行')
      } else {
        ElMessage.error('请求失败，请检查网络或重试')
      }
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  refreshCaptcha()
  const remembered = localStorage.getItem('rememberedUser')
  if (remembered) {
    form.username = remembered
    form.remember = true
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.shape-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  top: -200px;
  right: -100px;
  animation: float 20s infinite ease-in-out;
}

.shape-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  bottom: -100px;
  left: -50px;
  animation: float 15s infinite ease-in-out reverse;
}

.shape-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 10s infinite ease-in-out;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(50px, 50px) rotate(90deg); }
  50% { transform: translate(0, 100px) rotate(180deg); }
  75% { transform: translate(-50px, 50px) rotate(270deg); }
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.1; }
  50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.15; }
}

.login-box {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  margin-bottom: 16px;
}

.title {
  color: #223147;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #909399;
  font-size: 0.85rem;
  margin: 0;
}

.login-form {
  margin-top: 20px;
}

.captcha-row {
  display: flex;
  gap: 12px;
  width: 100%;
}

.captcha-img {
  width: 120px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  transition: transform 0.2s;
}

.captcha-img:hover {
  transform: scale(1.05);
}

.captcha-text {
  font-size: 1.5rem;
  font-weight: bold;
  color: #fff;
  letter-spacing: 8px;
  font-family: 'Courier New', monospace;
}

.login-footer {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.version {
  color: #909399;
  font-size: 0.8rem;
  margin: 0 0 4px 0;
}

.copyright {
  color: #c0c4cc;
  font-size: 0.75rem;
  margin: 0;
}

@media (max-width: 480px) {
  .login-box {
    width: 90%;
    padding: 30px 20px;
  }
}
</style>
