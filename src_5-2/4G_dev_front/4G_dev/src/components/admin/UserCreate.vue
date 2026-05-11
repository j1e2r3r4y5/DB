<template>
    <div class="admin-wrapper">
        <div class="admin-header">
            <el-button type="default" @click="goBack" style="margin-right: 12px;">返回</el-button>
            <div class="admin-title">新建用户</div>
        </div>
        <el-card style="max-width: 500px;">
            <el-form label-width="80px">
                <el-form-item label="用户名">
                    <el-input v-model="form.username" placeholder="请输入用户名" />
                </el-form-item>
                <el-form-item label="密码">
                    <el-input v-model="form.password" show-password placeholder="请输入密码" />
                </el-form-item>
                <el-form-item label="昵称">
                    <el-input v-model="form.nickname" placeholder="请输入昵称（可选）" />
                </el-form-item>
                <el-form-item label="类型">
                    <el-select v-model="form.type" placeholder="请选择用户类型">
                        <el-option v-if="currentUserType === 0" label="系统管理员" :value="1" />
                        <el-option label="设备管理员" :value="2" />
                        <el-option label="普通用户" :value="3" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSubmit" :loading="submitting">确定创建</el-button>
                    <el-button @click="goBack">取消</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const currentUserType = Number(localStorage.getItem('userType') || 0)
const submitting = ref(false)
const form = ref({ username: '', password: '', type: 2, nickname: '' })

function goBack() {
    router.push('/home/users')
}

async function handleSubmit() {
    if (!form.value.username || !form.value.password) {
        ElMessage.error('用户名和密码不能为空')
        return
    }
    submitting.value = true
    try {
        const res = await api.Registeruser({
            Username: form.value.username,
            Password: form.value.password,
            Type: form.value.type,
            Nickname: form.value.nickname
        })
        if (res.data && res.data.code === 0) {
            ElMessage.success('新建用户成功！')
            router.push('/home/users')
        } else {
            ElMessage.error(res.data?.message || '新建用户失败')
        }
    } catch (e) {
        ElMessage.error('请求失败')
    } finally {
        submitting.value = false
    }
}
</script>

<style scoped>
.admin-wrapper {
    padding: 24px;
}
.admin-header {
    display: flex;
    align-items: center;
    margin-bottom: 18px;
}
.admin-title {
    font-size: 1.3rem;
    font-weight: bold;
    color: #223147;
}
</style>
