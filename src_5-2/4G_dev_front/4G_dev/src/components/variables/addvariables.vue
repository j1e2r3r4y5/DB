<template>
    <el-dialog v-model="visible" title="新建变量" width="500px" @close="resetForm">
        <el-form :model="form" label-width="100px">
            <!-- <el-form-item label="所属设备ID">
                <el-select v-model="form.devID" placeholder="请选择设备" style="width:300px">
                    <el-option v-for="item in deviceOptions" :key="item.value" :label="item.label"
                        :value="item.value" />
                </el-select>
            </el-form-item> -->
            <el-form-item label="变量名">
                <el-input v-model="form.varName" style="width:300px" />
            </el-form-item>
            <el-form-item label="数据类型">
                <el-select v-model="form.dataType" placeholder="请选择数据类型" style="width:300px">
                    <el-option v-for="opt in DataTypeOptions" :key="opt.value" :label="opt.label"
                        :value="opt.value" />
                </el-select>
            </el-form-item>
            <el-form-item label="数据分区">
                <el-select v-model="form.modbusType" placeholder="请选择数据分区" style="width:300px;">
                    <el-option label="0区 线圈 (Coils)" value="0" />
                    <el-option label="1区 离散输入 (Discrete Inputs)" value="1" />
                    <el-option label="3区 输入寄存器 (Input Registers)" value="3" />
                    <el-option label="4区 保持寄存器 (Holding Registers)" value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="Modbus站号">
                <el-input v-model="form.modbusNumber" type="number" style="width:300px" />
            </el-form-item>
            <el-form-item label="数据地址">
                <el-input v-model="form.modbusAddr" style="width:300px" />
            </el-form-item>
            <el-form-item label="寄存器数量">
                <el-input v-model="form.data_len" type="number" style="width:300px"
                    :disabled="true"
                    :placeholder="`自动计算: ${autoRegisterNum}`" />
            </el-form-item>
            <el-form-item label="字符串长度">
                <el-input v-model="form.stringLen" type="number" style="width:300px"
                    :disabled="!isStringType(form.dataType)"
                    placeholder="仅字符串类型可填" />
            </el-form-item>
            <el-form-item label="小数位数">
                <el-input v-model="form.decimalDigits" style="width:300px" :disabled="true"
                    placeholder="已移除，无需填写" />
            </el-form-item>

        </el-form>
        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import api from '../../api'
import { DataTypeOptions, calculateRegisterNum, isStringType } from '../../utils/datatype'
const deviceOptions = ref([])
const props = defineProps({
    modelValue: Boolean,
    defaultDevId: [String, Number]
})
const emit = defineEmits(['update:modelValue', 'success'])
const visible = ref(props.modelValue)
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

const loading = ref(false)
const form = ref({
    devID: props.defaultDevId ?? '',
    varName: '',
    dataType: '',
    modbusType: '', // 新增 modbusType 字段
    modbusNumber: '',
    modbusAddr: '',
    data_len: '',
    stringLen: '',
    decimalDigits: ''
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

function resetForm() {
    form.value = {
        devID: props.defaultDevId ?? '',
        varName: '',
        dataType: '',
        modbusType: '', // 新增 modbusType 字段
        modbusNumber: '',
        modbusAddr: '',
        data_len: '',
        stringLen: '',
        decimalDigits: ''
    }
}
// 监听 defaultDevId 变化，弹窗每次打开都同步
watch(visible, (v) => {
    if (v) {
        form.value.devID = props.defaultDevId ?? ''
    }
})
async function handleSubmit() {
    loading.value = true
    try {
        await api.addvariable({
            // ID: null,
            variable: {
                // ID: null,
                devID: Number(form.value.devID),
                varName: form.value.varName,
                dataType: form.value.dataType,
                modbusType: form.value.modbusType, // 使用 modbusType 字段
                modbusDevice: Number(form.value.modbusNumber),
                modbusAddr: Number(form.value.modbusAddr),
                data_len: form.value.data_len,
                stringLen: form.value.stringLen,
                decimalDigits: Number(form.value.decimalDigits)
            }
        })
        // console.log('新建变量数据', form.value.devID)
        emit('success')
        visible.value = false
        resetForm()
        if (window.ElMessage) window.ElMessage.success('新建成功')
    } catch (e) {
        if (window.ElMessage) window.ElMessage.error('新建失败')
    }
    loading.value = false
}
async function fetchDeviceList() {
    try {
        const res = await api.getDeviceList()
        let list = []
        if (res.data && res.data.code === 0) {
            if (res.data.data && res.data.data.devicelist) {
                list = res.data.data.devicelist
            } else if (res.data.devicelist) {
                list = res.data.devicelist
            }
        }
        deviceOptions.value = (list || []).map(item => ({
            label: item.name || item.id,
            value: item.id
        }))
    } catch (e) {
        deviceOptions.value = []
    }
}
onMounted(fetchDeviceList)
</script>