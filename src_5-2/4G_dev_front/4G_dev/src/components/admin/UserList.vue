<template>
    <div class="admin-wrapper">
        <div class="admin-header">
            <div class="admin-title">用户列表</div>
        </div>
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
            <el-table-column class-name="operation-col" label="操作" min-width="200">
                <template #default="scope">
                    <el-button v-if="canEdit(scope.row)" link class="el-oll" size="small"
                        @click="handleEdit(scope.row)">修改</el-button>
                    <el-button v-if="scope.row.Type !== 0 && scope.row.Type !== '0'" link class="el-oll" size="small"
                        @click="openRemoveDialog(scope.row)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <RemoveUser v-if="removeUserId !== null" v-model="removeDialogVisible" :user-id="removeUserId"
            @success="fetchUserList" />
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'
import RemoveUser from './RemoveUser.vue'

const router = useRouter()
const userList = ref([])
const typeMap = {
    '0': '超级管理员',
    '1': '系统管理员',
    '2': '设备管理员',
    '3': '普通用户'
}

const currentUserType = Number(localStorage.getItem('userType') || 0)
let userId = ''
try { userId = localStorage.getItem('userId') || '' } catch (e) {}

function canEdit(row) {
    const rowType = Number(row.Type)
    if (currentUserType === 0) return true
    if (String(row.id) === userId) return true
    if (currentUserType === 1 && rowType >= 2) return true
    return false
}

function handleEdit(row) {
    router.push(`/home/users/edit/${row.id}`)
}

const removeDialogVisible = ref(false)
const removeUserId = ref(null)
function openRemoveDialog(row) {
    removeUserId.value = row.id
    removeDialogVisible.value = true
}

async function fetchUserList() {
    try {
        const res = await api.getUserList({})
        if (res.data && res.data.data && Array.isArray(res.data.data.users)) {
            userList.value = res.data.data.users
        } else {
            userList.value = []
        }
    } catch (e) {
        userList.value = []
    }
}

onMounted(() => {
    fetchUserList()
    setInterval(fetchUserList, 20000)
})
</script>

<style scoped>
.admin-wrapper {
    padding: 24px;
}

.admin-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}

.admin-title {
    font-size: 1.3rem;
    font-weight: bold;
    color: #223147;
}

:deep(.el-oll) {
    color: #409EFF !important;
    font-weight: bold;
}
</style>
