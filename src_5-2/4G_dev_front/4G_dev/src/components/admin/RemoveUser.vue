<template>
    <el-dialog v-model="visible" title="删除用户" width="340px">
        <div style="font-size:16px;">确定要删除该用户吗？</div>
        <template #footer>
            <el-button @click="close">取消</el-button>
            <el-button type="danger" @click="handleDelete" :loading="loading">删除</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../../api'
const props = defineProps({
    userId: {
        type: [Number, String],
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
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emits('update:modelValue', v))

function close() {
    visible.value = false
}

async function handleDelete() {
    loading.value = true
    try {
        const res = await api.Deleteuser({ ID: [props.userId] })
        if (res.data && res.data.code === 0) {
            window.$message ? window.$message.success('删除成功') : alert('删除成功')
            emits('success')
            close()
        } else {
            window.$message ? window.$message.error(res.data?.message || '删除失败') : alert(res.data?.message || '删除失败')
        }
    } catch (e) {
        window.$message ? window.$message.error('请求失败') : alert('请求失败')
    } finally {
        loading.value = false
    }
}
</script>
