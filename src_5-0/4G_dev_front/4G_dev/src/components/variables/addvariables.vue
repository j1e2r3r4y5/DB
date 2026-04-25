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
                    <el-option label="整数" value="1" />
                    <el-option label="浮点数" value="2" />
                    <el-option label="定点数" value="3" />
                    <el-option label="字符串" value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="数据分区">
                <el-select v-model="form.modbusType" placeholder="请选择数据分区" style="width:300px;">
                    <el-option label="线圈" value="1" />
                    <el-option label="离散输入" value="2" />
                    <el-option label="保持寄存器" value="3" />
                    <el-option label="输入寄存器" value="4" />
                </el-select>
            </el-form-item>
            <el-form-item label="Modbus站号">
                <el-input v-model="form.modbusNumber" type="number" style="width:300px" />
            </el-form-item>
            <el-form-item label="数据地址">
                <el-input v-model="form.modbusAddr" style="width:300px" />
            </el-form-item>
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
            <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '../../api'
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