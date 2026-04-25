<template>
    <el-dialog v-model="visible" title="新建设备" width="400px" @close="resetForm">
        <el-form :model="form" label-width="100px">
            <el-form-item label="设备名称" required>
                <el-input v-model="form.devName" placeholder="请输入设备名称" />
            </el-form-item>
            <el-form-item label="设备序列号" required>
                <el-input v-model="form.devSerial" placeholder="请输入设备序列号" />
            </el-form-item>
            <el-form-item label="设备位置" required>
                <el-input v-model="form.devLocation" placeholder="请输入设备位置" />
            </el-form-item>
            <el-form-item label="发送模式">
                <el-select v-model="form.sendmodel" placeholder="请选择发送模式">
                    <el-option label="定时发送" value="00" />
                    <el-option label="线圈置位" value="01" />
                    <el-option label="寄存器变化" value="02" />
                </el-select>
            </el-form-item>
            <el-form-item :label="form.sendmodel === '00' ? '发送间隔(秒)' : '触发地址'">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <el-select v-model="configType" style="width: 100px;" @change="handleConfigTypeChange">
                        <el-option label="十进制" value="dec" />
                        <el-option label="十六进制" value="hex" />
                    </el-select>
                    <el-input v-model="configInput" style="flex:1;" :input-style="{ textAlign: 'right' }">
                        <template #prepend v-if="configType === 'hex'">
                            <span style="color:#888;">0x</span>
                        </template>
                    </el-input>
                </div>
            </el-form-item>
            <el-form-item label="波特率">
                <el-select v-model="form.baud" placeholder="请选择波特率">
                    <el-option label="300" value="00" />
                    <el-option label="600" value="01" />
                    <el-option label="1200" value="02" />
                    <el-option label="2400" value="03" />
                    <el-option label="4800" value="04" />
                    <el-option label="9600" value="05" />
                    <el-option label="14400" value="06" />
                    <el-option label="19200" value="07" />
                    <el-option label="28800" value="08" />
                    <el-option label="38400" value="09" />
                    <el-option label="57600" value="0A" />
                    <el-option label="76800" value="0B" />
                    <el-option label="115200" value="0C" />
                    <el-option label="230400" value="0D" />
                    <el-option label="460800" value="0E" />
                    <el-option label="921600" value="0F" />
                </el-select>
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
import { ref, watch, } from 'vue'
import api from '../api'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'success'])

const visible = ref(props.visible)
watch(() => props.visible, val => visible.value = val)
watch(visible, val => emit('update:visible', val))

const form = ref({
    devName: '',
    devSerial: '',
    devLocation: '',
    sendmodel: '00', // 默认定时发送
    baud: '05',      // 默认9600
})
const configType = ref('dec')
const configInput = ref('30') // 默认30秒
const errorMsg = ref('')

function resetForm() {
    form.value = {
        devName: '',
        devSerial: '',
        devLocation: '',
        sendmodel: '00',
        baud: '05',
    }
    configType.value = 'dec'
    configInput.value = '30'
    errorMsg.value = ''
}
function handleConfigTypeChange(val) {
    if (!configInput.value) return
    if (val === 'hex') {
        // dec -> hex
        const n = Number(configInput.value)
        if (!isNaN(n)) configInput.value = n.toString(16).toUpperCase()
    } else {
        // hex -> dec
        const n = parseInt(configInput.value, 16)
        if (!isNaN(n)) configInput.value = String(n)
    }
}
async function handleSubmit() {
    errorMsg.value = ''
    if (!form.value.devName || !form.value.devSerial || !form.value.devLocation) {
        errorMsg.value = '请填写完整信息'
        return
    }
    try {
        const res = await api.Adddevice({
            Device: [
                {
                    Devname: form.value.devName,
                    DevSerial: form.value.devSerial,
                    DevLocation: form.value.devLocation
                }
            ]
        })
        if (res.data && res.data.code === 0) {
            // 检查 failureList
            const failureList = res.data.data?.failureList
            if (failureList && failureList.length > 0) {
                errorMsg.value = failureList[0].reason || '添加失败'
            } else {
                emit('success')
                visible.value = false
                resetForm()
            }
        } else if (res.data && res.data.reason) {
            errorMsg.value = res.data.reason
        } else {
            errorMsg.value = '添加失败'
        }
    } catch (e) {
        errorMsg.value = '请求失败'
    }
}
</script>

<style scoped>
.el-dialog__body {
    padding-bottom: 0;
}
</style>
