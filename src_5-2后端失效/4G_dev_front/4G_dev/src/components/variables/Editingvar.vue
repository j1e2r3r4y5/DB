<template>
    <el-dialog v-model="visible" title="编辑变量" width="500px" @close="resetForm">
        <el-form :model="form" label-width="100px">
            <!-- <el-form-item label="所属设备ID">
                <el-input v-model="form.devID" type="number" style="width:320px;" />
            </el-form-item> -->
            <el-form-item label="变量名">
                <el-input v-model="form.varName" style="width:320px;" />
            </el-form-item>
            <el-form-item label="数据类型">
                <el-select v-model="form.dataType" placeholder="请选择数据类型" style="width:320px;">
                    <el-option v-for="opt in DataTypeOptions" :key="opt.value" :label="opt.label"
                        :value="opt.value" />
                </el-select>
            </el-form-item>
            <el-form-item label="Modbus类型">
                <el-select v-model="form.modbusType" placeholder="请选择数据类型" style="width:320px;">
                    <el-option label="0区 线圈 (Coils)" value="0" />
                    <el-option label="1区 离散输入 (Discrete Inputs)" value="1" />
                    <el-option label="3区 输入寄存器 (Input Registers)" value="3" />
                    <el-option label="4区 保持寄存器 (Holding Registers)" value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="Modbus从站">
                <el-input v-model="form.modbusDevice" type="number" style="width:320px;" />
            </el-form-item>
            <el-form-item label="Modbus地址">
                <el-input v-model="form.modbusAddr" style="width:320px;" />
            </el-form-item>
            <el-form-item label="寄存器数量">
                <el-input v-model="form.data_len" type="number" style="width:300px" :disabled="true"
                    :placeholder="`自动计算: ${autoRegisterNum}`" />
            </el-form-item>
            <el-form-item label="字符串长度">
                <el-input v-model="form.stringLen" type="number" style="width:300px"
                    :disabled="!isStringType(form.dataType)" placeholder="仅字符串类型可填" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="loading">保存</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import api from '../../api'
import { DataTypeOptions, calculateRegisterNum, isStringType } from '../../utils/datatype'

const props = defineProps({
    modelValue: Boolean,
    variable: Object
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

const loading = ref(false)

const form = ref({
    id: '',
    devID: '',
    varName: '',
    dataType: '',
    modbusType: '', // 新增字段
    modbusDevice: '',
    modbusAddr: '',
    data_len: '',
    stringLen: ''
})

// 自动计算寄存器数量
const autoRegisterNum = computed(() => {
    if (!form.value.dataType) return '-'
    const stringLen = parseInt(form.value.stringLen) || 0
    return calculateRegisterNum(form.value.dataType, stringLen)
})

// 监听数据类型和字符串长度变化，自动设置data_len
watch([() => form.value.dataType, () => form.value.stringLen], () => {
    const registerNum = autoRegisterNum.value
    if (registerNum !== '-') {
        form.value.data_len = registerNum
    }
})


// 监听 props.variable 变化，填充表单数据
// 注意：modbusType(区域) 和 dataType(类型) 是两个独立字段，不再自动同步
watch(() => props.variable, v => {
    if (v) {
        form.value = { ...v }
        // 旧代码已删除：之前错误地将 dataType 自动同步到 modbusType
        // 原因：modbusType 表示 Modbus 区域(1=线圈,2=离散输入,3=输入寄存器,4=保持寄存器)
        //       dataType 表示数据类型(1=整数,2=浮点数,3=定点数,4=字符串)，两者概念不同不应同步
    }
}, { immediate: true })

// 以下监听器已删除
// 旧代码：监听 dataType 变化自动同步到 modbusType
// 问题：这会导致用户在编辑变量时，看到的 modbusType 被意外改变
// 修复：删除了这个错误的自动同步逻辑，让两个字段独立运作
function resetForm() {
    form.value = {
        id: '',
        devID: '',
        varName: '',
        dataType: '',
        modbusType: '',
        modbusNumber: '',
        modbusAddr: '',
        data_len: '',
        stringLen: ''
    }
}

async function handleSubmit() {
    loading.value = true
    try {
        await api.modifyvariable({
            variable: {
                id: form.value.id,
                devID: Number(form.value.devID),
                varName: form.value.varName,
                dataType: form.value.dataType,
                modbusType: form.value.modbusType, // 使用 modbusType 字段
                modbusDevice: Number(form.value.modbusDevice),
                modbusAddr: Number(form.value.modbusAddr),
                data_len: form.value.data_len,
                stringLen: form.value.stringLen
            }
        })
        emit('success')
        visible.value = false
        resetForm()
        if (window.ElMessage) window.ElMessage.success('修改成功')
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('修改失败')
    }
    loading.value = false
}
</script>
