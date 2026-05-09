<template>
    <div class="login-container">
        <div class="login-box">
            <h1 class="title">设备管理平台登录</h1>
            <div class="arrow">▼</div>
            <el-form class="login-form" @submit.prevent="handleLogin" @keyup.enter.native="handleLogin">
                <el-form-item>
                    <el-input v-model="username" placeholder="请输入用户名" clearable prefix-icon="el-icon-user" />
                </el-form-item>
                <el-form-item>
                    <el-input v-model="password" type="password" placeholder="请输入密码" clearable
                        prefix-icon="el-icon-lock" show-password />
                </el-form-item>
                <el-form-item>
                    <Verification ref="verificationRef" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" style="width:100%" @click="handleLogin">登录</el-button>
                </el-form-item>
            </el-form>
        </div>
    </div>
</template>
<script setup>
import Verification from '../components/verification.vue'
import { ref } from 'vue';
import api from '../api';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
const router = useRouter();
const username = ref('');
const password = ref('');
const verificationRef = ref(null)
const handleLogin = async () => {
    // 验证码校验 - 暂时跳过
    // if (!verificationRef.value?.validate()) {
    //     ElMessage.error('验证码错误，请重新输入')
    //     verificationRef.value?.refreshCode()
    //     return
    // }
    try {
        const res = await api.login({
            username: username.value,
            password: password.value
        })
        if (res.data.code === 0) {
            ElMessage.success('登录成功！')
            localStorage.setItem('userId', res.data.data.id) // 保存用户ID
            localStorage.setItem('userType', res.data.data.type) // 保存type
            console.log('userid:', res.data.data.id);
            console.log('data', res.data);
            localStorage.setItem('token', res.data.data.token) // 保存token
            localStorage.removeItem('currentMenu')
            console.log('登录成功，跳转到首页', res);
            router.push('/home');
        } else {
            // 针对常见错误码做详细提示
            if (res.data.code === 53) {
                ElMessage.error(res.data.msg || '账号或密码错误')
            } else if (res.data.code === 54) {
                ElMessage.error('账号已被禁用')
            } else {
                ElMessage.error(res.data.msg || res.data.message || '登录失败')
            }
            // 可选：控制台输出详细错误信息
            console.error('登录失败详情:', res.data)
        }
    } catch (error) {
        console.error('请求失败详情:', error.response?.data || error)
        ElMessage.error('请求失败，请检查网络或重试')
    }
};
</script>
<style scoped>
.login-container {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: url('http://43.139.165.79:887/img/LoginBackground.e959bc7c.png') no-repeat center center;
    background-size: cover;
}

.login-box {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    width: 400px;
    text-align: center;
}

.title {
    color: #428bca;
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
}

.arrow {
    color: #428bca;
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
}

/* Element Plus 组件自带样式，保留整体布局美化 */
.login-form {
    margin-top: 1rem;
}
</style>