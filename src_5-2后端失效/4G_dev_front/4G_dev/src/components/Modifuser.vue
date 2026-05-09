<template>
    <el-dialog v-model="visible" title="修改密码" width="350px" @close="resetForm">
        <el-form :model="form" label-width="80px">
            <el-form-item label="旧密码">
                <el-input v-model="form.OldPassword" type="password" />
            </el-form-item>
            <el-form-item label="新密码">
                <el-input v-model="form.NewPassword" type="password" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit">确定</el-button>
        </template>
        <div v-if="errorMsg" style="color: red; margin-top: 8px;">{{ errorMsg }}</div>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../api'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'success'])

const visible = ref(props.visible)
watch(() => props.visible, val => visible.value = val)
watch(visible, val => emit('update:visible', val))

const form = ref({ OldPassword: '', NewPassword: '' })
const errorMsg = ref('')

function resetForm() {
    form.value = { OldPassword: '', NewPassword: '' }
    errorMsg.value = ''
}

async function handleSubmit() {
    errorMsg.value = ''
    const userId = Number(localStorage.getItem('userId')) // 或你的用户ID获取方式
    // console.log('当前用户ID:', userId)
    if (!form.value.OldPassword || !form.value.NewPassword) {
        errorMsg.value = '请填写完整信息'
        return
    }
    // console.log('提交的表单数据:', form.value)
    try {
        const res = await api.Modifyuser({
            ID: userId,
            OldPassword: form.value.OldPassword,
            NewPassword: form.value.NewPassword
        })
        // console.log('修改密码请求结果:', res)
        if (res.data && res.data.code === 0) {
            alert('修改成功！')
            emit('success')
            visible.value = false
            resetForm()
        } else if (res.data && res.data.reason) {
            errorMsg.value = res.data.reason
        } else {
            errorMsg.value = '修改失败'
        }
    } catch (e) {
        errorMsg.value = '请求失败'
    }
}
</script>