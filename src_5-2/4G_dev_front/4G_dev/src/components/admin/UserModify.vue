<template>
    <div class="admin-wrapper">
        <div class="admin-header">
            <el-button type="default" @click="goBack" style="margin-right: 12px;">返回</el-button>
            <div class="admin-title">修改用户</div>
        </div>

        <el-card v-if="!userIdParam" style="max-width: 500px;">
            <el-form label-width="80px">
                <el-form-item label="选择用户">
                    <el-select v-model="selectedUserId" placeholder="请选择要修改的用户" style="width: 100%;" @change="loadUser">
                        <el-option v-for="u in allUsers" :key="u.id" :label="`${u.Username} (${typeMap[u.Type] || u.Type})`" :value="String(u.id)" />
                    </el-select>
                </el-form-item>
            </el-form>
        </el-card>

        <el-card v-if="loading" style="max-width: 500px;">
            <el-skeleton :rows="4" active />
        </el-card>

        <el-card v-else-if="!userData && userIdParam" style="max-width: 500px;">
            <el-empty description="未找到用户信息">
                <el-button type="primary" @click="goBack">返回用户列表</el-button>
            </el-empty>
        </el-card>

        <el-card v-else-if="userData" style="max-width: 500px;">
            <el-form label-width="80px">
                <el-form-item label="用户名">
                    <el-input v-model="form.Username" placeholder="请输入用户名" />
                </el-form-item>
                <el-form-item label="昵称">
                    <el-input v-model="form.Nickname" placeholder="请输入昵称" />
                </el-form-item>
                <el-form-item label="密码">
                    <el-input v-model="form.Password" type="password" placeholder="留空不修改密码" />
                </el-form-item>
                <el-divider>权限设置</el-divider>
                <el-form-item label="用户类型">
                    <el-select v-model="form.Type" placeholder="请选择用户类型" :disabled="!canChangeType">
                        <el-option v-if="currentUserType === 0" label="超级管理员" :value="0" />
                        <el-option v-if="currentUserType === 0" label="系统管理员" :value="1" />
                        <el-option label="设备管理员" :value="2" />
                        <el-option label="普通用户" :value="3" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
                    <el-button @click="goBack">取消</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const currentUserType = Number(localStorage.getItem('userType') || 0)
let myUserId = ''
try { myUserId = localStorage.getItem('userId') || '' } catch (e) {}

const loading = ref(false)
const saving = ref(false)
const userData = ref(null)
const allUsers = ref([])
const selectedUserId = ref('')
const form = ref({ Username: '', Nickname: '', Type: 3, Password: '', id: null })

const userIdParam = ref('')

const typeMap = {
    '0': '超级管理员',
    '1': '系统管理员',
    '2': '设备管理员',
    '3': '普通用户'
}

const canChangeType = computed(() => {
    if (!userData.value) return false
    if (currentUserType === 0) return true
    const targetType = Number(userData.value.Type)
    const self = String(userData.value.id) === myUserId
    if (self) return false
    if (currentUserType === 1 && targetType >= 2) return true
    return false
})

function goBack() {
    router.push('/home/users')
}

async function fetchAllUsers() {
    try {
        const res = await api.getUserList({})
        if (res.data && res.data.data && Array.isArray(res.data.data.users)) {
            allUsers.value = res.data.data.users
        }
    } catch (e) {}
}

function loadUser(id) {
    if (!id) return
    router.replace(`/home/users/edit/${id}`)
    doFetchUser(id)
}

async function doFetchUser(id) {
    if (!id) return
    loading.value = true
    userIdParam.value = id
    try {
        if (allUsers.value.length === 0) await fetchAllUsers()
        const found = allUsers.value.find(u => String(u.id) === String(id))
        if (found) {
            const type = currentUserType === 0 ? found.Type : (found.Type === 0 ? 0 : found.Type)
            userData.value = found
            form.value = { ...found, Type: Number(type), Password: '' }
        } else {
            userData.value = null
            ElMessage.warning('未找到该用户信息')
        }
    } catch (e) {
        userData.value = null
        ElMessage.error('获取用户信息失败：' + (e.message || ''))
    } finally {
        loading.value = false
    }
}

onMounted(async () => {
    await fetchAllUsers()
    const param = route.params.userId
    if (param && param !== '0') {
        userIdParam.value = param
        doFetchUser(param)
    }
})

async function handleSave() {
    if (!form.value.Username) {
        ElMessage.error('用户名不能为空')
        return
    }
    if (!canChangeType.value && userData.value) {
        const origType = Number(userData.value.Type)
        const newType = Number(form.value.Type)
        if (origType !== newType) {
            ElMessage.error('您没有权限修改该用户的类型')
            form.value.Type = origType
            return
        }
    }
    saving.value = true
    try {
        const data = { ID: form.value.id }
        if (form.value.Username) data.Username = form.value.Username
        if (form.value.Nickname) data.Nickname = form.value.Nickname
        if (form.value.Password) data.Password = form.value.Password

        let needsTypeChange = false
        if (form.value.Type !== undefined && form.value.Type !== null && userData.value) {
            const origType = Number(userData.value.Type)
            const newType = Number(form.value.Type)
            if (origType !== newType) {
                needsTypeChange = true
            }
        }

        const res = await api.Changeuser(data)
        if (res.data && res.data.code === 0) {
            if (needsTypeChange) {
                try {
                    await api.Permuser({
                        id: form.value.id,
                        Type: Number(form.value.Type),
                        CurrentUserType: currentUserType
                    })
                } catch (e) {
                    ElMessage.warning('用户信息已保存，但权限修改失败')
                    router.push('/home/users')
                    return
                }
            }
            ElMessage.success('修改成功')
            router.push('/home/users')
        } else {
            ElMessage.error(res.data?.message || '修改失败')
        }
    } catch (e) {
        ElMessage.error('请求失败：' + (e.message || ''))
    } finally {
        saving.value = false
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
