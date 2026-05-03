<template>
    <el-dialog :model-value="visible" @update:modelValue="emit('update:visible', $event)" title="用户授权" width="400px">
        <div style="margin-bottom: 18px;">
            <span>用户名：</span>
            <b>{{ user?.Username }}</b>
        </div>
        <el-form label-width="80px">
            <el-form-item label="权限类型">
                <el-select v-model="type" placeholder="请选择权限类型" style="width: 220px;">
                    <el-option label="普通用户" value="3" />
                    <el-option label="设备管理员" value="2" />
                    <el-option v-if="currentUserType === 0" label="系统管理员" value="1" />
                    <!-- <el-option v-if="currentUserType === 0" label="超级管理员" value="0" /> -->
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="close">取消</el-button>
            <el-button type="primary" @click="handleGrant">确定</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, } from 'vue'
// import api from '../api'
import api from '../../api'

const props = defineProps({
    visible: Boolean,
    user: Object,
    currentUserType: Number
})
const emit = defineEmits(['update:visible', 'success'])

const type = ref('')
watch(() => props.user, (val) => {
    type.value = val?.Type ? String(val.Type) : ''
})

function close() {
    emit('update:visible', false)
}

async function handleGrant() {
    if (!props.user || type.value === '') {
        window.$message ? window.$message.error('请选择权限类型') : alert('请选择权限类型')
        return
    }
    try {
        const res = await api.Permuser({
            id: props.user.id,
            Type: Number(type.value),
            CurrentUserType: props.currentUserType
        })
        if (res.data && res.data.code === 0) {
            window.$message ? window.$message.success('权限修改成功！') : alert('权限修改成功！')
            emit('success')
            close()
        } else {
            window.$message ? window.$message.error(res.data?.message || '权限修改失败') : alert(res.data?.message || '权限修改失败')
        }
    } catch (e) {
        window.$message ? window.$message.error('请求失败') : alert('请求失败')
    }
}
</script>
