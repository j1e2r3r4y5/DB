<template>
    <div class="admin-wrapper">
        <!-- <el-card> -->
        <div class="admin-title">用户管理</div>
        <el-button type="primary" @click="showRegisterDialog = true">新建用户</el-button>
        <el-table :data="userList" stripe style="width: 100%; background: #fff;"
            :header-cell-style="{ color: '#222', fontWeight: 'bold' }">
            <el-table-column prop="id" label="用户ID" min-width="80" />
            <el-table-column prop="Username" label="用户名" min-width="120" />
            <el-table-column prop="Nickname" label="昵称" min-width="120" />
            <el-table-column prop="Type" label="类型" min-width="80">
                <template #default="scope">
                    <span>{{ typeMap[scope.row.Type] || scope.row.Type }}</span>
                </template>
            </el-table-column>
            <el-table-column class-name="operation-col" prop="Operation" label="操作" min-width="120">
                <template #default="scope">
                    <!-- 超级管理员可编辑所有人 -->
                    <el-button v-if="currentUserType === 0" link class="el-oll" size="small"
                        @click="openEditDialog(scope.row)">编辑</el-button>
                    <!-- 系统管理员可编辑设备管理员、普通用户和自己 -->
                    <el-button
                        v-else-if="currentUserType === 1 && (scope.row.Type === 2 || scope.row.Type === 3 || scope.row.id == userId)"
                        link class="el-oll" size="small" @click="openEditDialog(scope.row)">编辑</el-button>
                    <!-- 其它操作按钮保持原逻辑 -->
                    <el-button v-if="scope.row.Type !== 0 && scope.row.Type !== '0'" link class="el-oll" size="small"
                        @click="openGrantDialog(scope.row)">授权</el-button>
                    <el-button v-if="scope.row.Type !== 0 && scope.row.Type !== '0'" link class="el-oll" size="small"
                        @click="openRemoveDialog(scope.row)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <permuser v-model:visible="grantDialogVisible" :user="grantUser" :currentUserType="currentUserType"
            @success="fetchUserList" />
        <el-dialog v-model="showRegisterDialog" title="新建用户" width="400px">
            <el-form label-width="80px">
                <el-form-item label="用户名">
                    <el-input v-model="registerForm.username" placeholder="请输入用户名" />
                </el-form-item>
                <el-form-item label="密码">
                    <el-input v-model="registerForm.password" show-password placeholder="请输入密码" />
                </el-form-item>
                <el-form-item label="昵称">
                    <el-input v-model="registerForm.nickname" placeholder="请输入昵称（可选）" />
                </el-form-item>
                <el-form-item label="类型">
                    <el-select v-model="registerForm.type" placeholder="请选择用户类型">
                        <el-option v-if="currentUserType === 0" label="系统管理员" :value="1" />
                        <el-option label="设备管理员" :value="2" />
                        <el-option label="普通用户" :value="3" />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="showRegisterDialog = false">取消</el-button>
                <el-button type="primary" @click="handleRegister">确定</el-button>
            </template>
        </el-dialog>
        <RemoveUser v-if="removeUserId !== null" v-model="removeDialogVisible" :user-id="removeUserId"
            @success="fetchUserList" />
        <!-- </el-card> -->
        <Changeusre v-if="editUser" v-model="editDialogVisible" :user="editUser" @success="fetchUserList" />
    </div>

</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import permuser from './admin/permuser.vue'
import RemoveUser from './admin/RemoveUser.vue'
import Changeusre from './admin/Changeusre.vue'
const userList = ref([])
const typeMap = {
    '0': '超级管理员',
    '1': '系统管理员',
    '2': '设备管理员',
    '3': '普通用户'
}
// 编辑用户
const editDialogVisible = ref(false)
const editUser = ref(null)
function openEditDialog(row) {
    editUser.value = row
    editDialogVisible.value = true
}
//删除用户
const removeDialogVisible = ref(false)
const removeUserId = ref(null)

function openRemoveDialog(row) {
    removeUserId.value = row.id
    removeDialogVisible.value = true
}
// 授权用户
const grantDialogVisible = ref(false)
const grantUser = ref(null)
const currentUserType = Number(localStorage.getItem('userType') || 0)
let userId = ''
try {
    userId = localStorage.getItem('userId') || ''
} catch (e) { }
function openGrantDialog(row) {
    // 如果要授权的用户是超级管理员或系统管理员，且当前用户不是超级管理员，提示权限不足
    if ((row.Type === 0 || row.Type === 1 || row.Type === '0' || row.Type === '1') && currentUserType !== 0) {
        window.$message ? window.$message.error('权限不足，无法操作该用户！') : alert('权限不足，无法操作该用户！')
        return
    }
    grantUser.value = row
    grantDialogVisible.value = true
}

async function fetchUserList() {
    try {
        // 这里User参数可根据实际需求传递
        const res = await api.getUserList({})
        // console.log('getUserList返回:', res)
        if (res.data && res.data.data && Array.isArray(res.data.data.users)) {
            userList.value = res.data.data.users
        } else {
            userList.value = []
        }
    } catch (e) {
        // console.error('获取用户列表失败:', e)
        userList.value = []
    }
}
const showRegisterDialog = ref(false)
const registerForm = ref({ username: '', password: '', type: 2, nickname: '' }) // 默认新用户类型为设备管理员，昵称可选
async function handleRegister() {
    if (!registerForm.value.username || !registerForm.value.password) {
        window.$message ? window.$message.error('用户名和密码不能为空') : alert('用户名和密码不能为空')
        return
    }
    try {
        // console.log('registerForm.value.type:', registerForm.value.type)
        const res = await api.Registeruser({
            Username: registerForm.value.username,
            Password: registerForm.value.password,
            Type: registerForm.value.type,
            Nickname: registerForm.value.nickname // 可选字段
        })
        if (res.data && res.data.code === 0) {
            window.$message ? window.$message.success('新建用户成功！') : alert('新建用户成功！')
            showRegisterDialog.value = false
            registerForm.value = { username: '', password: '', type: 2, nickname: '' }
            fetchUserList()
        } else {
            window.$message ? window.$message.error(res.data?.message || '新建用户失败') : alert(res.data?.message || '新建用户失败')
        }
    } catch (e) {
        window.$message ? window.$message.error('请求失败') : alert('请求失败')
    }
}
onMounted(() => {
    fetchUserList();
    // 定时刷新，每30秒刷新一次
    setInterval(fetchUserList, 20000);
})
</script>

<style scoped>
.admin-wrapper {
    padding: 24px;
}

.admin-title {
    font-size: 1.3rem;
    font-weight: bold;
    margin-bottom: 18px;
    color: #223147;
}

:deep(.operation-col .cell) {
    padding-left: 200px !important;
    /* padding-right: 24px !important; */
}

:deep(.el-oll) {
    color: #409EFF !important;
    font-weight: bold;
}
</style>