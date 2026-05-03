<template>
    <el-dialog v-model="visible" title="编辑用户信息" width="400px">
        <el-form :model="form" label-width="80px">
            <el-form-item label="用户名">
                <el-input v-model="form.Username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="昵称">
                <el-input v-model="form.Nickname" placeholder="请输入昵称" />
            </el-form-item>
            <!-- <el-form-item label="类型">
                <el-select v-model="form.Type" placeholder="请选择用户类型">
                    <el-option label="超级管理员" :value="0" />
                    <el-option label="系统管理员" :value="1" />
                    <el-option label="设备管理员" :value="2" />
                    <el-option label="普通用户" :value="3" />
                </el-select>
            </el-form-item> -->
            <el-form-item label="密码">
                <el-input v-model="form.Password" type="password" placeholder="请输入密码" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="close">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="loading">保存</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../../api'
const props = defineProps({
    user: {
        type: Object,
        required: true
    },
    modelValue: {
        type: Boolean,
        default: false
    }
})
const emits = defineEmits(['update:modelValue', 'success'])
const visible = ref(props.modelValue)
const loading = ref(false)
const form = ref({ Username: '', Nickname: '', Type: 3, Password: '', id: null })
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emits('update:modelValue', v))
watch(() => props.user, (u) => {
    if (u) form.value = { ...u, Password: '' }
}, { immediate: true })

function close() {
    visible.value = false
}

async function handleSave() {
    loading.value = true
    try {
        // 只传有值的字段
        const data = { ID: form.value.id }
        if (form.value.Username) data.Username = form.value.Username
        if (form.value.Nickname) data.Nickname = form.value.Nickname
        if (form.value.Password) data.Password = form.value.Password
        // if (form.value.Type !== undefined) data.Type = form.value.Type
        const res = await api.Changeuser(data)
        if (res.data && res.data.code === 0) {
            window.$message ? window.$message.success('修改成功') : alert('修改成功')
            emits('success')
            close()
        } else {
            window.$message ? window.$message.error(res.data?.message || '修改失败') : alert(res.data?.message || '修改失败')
        }
    } catch (e) {
        window.$message ? window.$message.error('请求失败') : alert('请求失败')
    } finally {
        loading.value = false
    }
}
</script>
