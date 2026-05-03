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
                    <el-option label="整数" value="1" />
                    <el-option label="浮点数" value="2" />
                    <el-option label="定点数" value="3" />
                    <el-option label="字符串" value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="Modbus类型">
                <el-select v-model="form.modbusType" placeholder="请选择数据类型" style="width:320px;">
                    <!-- 标准 Modbus 协议分区定义 -->
                    <!-- 0区: 线圈 (Coils) - 功能码 0x01/0x05, 读写, 位类型 -->
                    <el-option label="0区 线圈 (Coils)" value="1" />
                    <!-- 1区: 离散输入 (Discrete Inputs) - 功能码 0x02, 只读, 位类型 -->
                    <el-option label="1区 离散输入 (Discrete Inputs)" value="2" />
                    <!-- 3区: 输入寄存器 (Input Registers) - 功能码 0x04, 只读, 16位字 -->
                    <el-option label="3区 输入寄存器 (Input Registers)" value="3" />
                    <!-- 4区: 保持寄存器 (Holding Registers) - 功能码 0x03/0x06, 读写, 16位字 -->
                    <el-option label="4区 保持寄存器 (Holding Registers)" value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="Modbus从站">
                <el-input v-model="form.modbusDevice" type="number" style="width:320px;" />
            </el-form-item>
            <el-form-item label="Modbus地址">
                <el-input v-model="form.modbusAddr" style="width:320px;" />
            </el-form-item>
            <!-- <el-form-item label="数据长度">
                <el-input v-model="form.data_len" style="width:320px;" />
            </el-form-item> -->
            <el-form-item label="字符串长度">
                <el-input v-model="form.stringLen" style="width:300px" :disabled="form.dataType !== '4'"
                    placeholder="仅字符串类型可填" />
            </el-form-item>
            <el-form-item label="小数位数">
                <el-input v-model="form.decimalDigits" style="width:300px" :disabled="form.dataType !== '3'"
                    placeholder="仅定点数可填" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="loading">保存</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../../api'

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
    modbusNumber: '',
    modbusAddr: '',
    data_len: '',
    stringLen: '',
    decimalDigits: ''
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
        stringLen: '',
        decimalDigits: ''
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
                stringLen: form.value.stringLen,
                decimalDigits: Number(form.value.decimalDigits)
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