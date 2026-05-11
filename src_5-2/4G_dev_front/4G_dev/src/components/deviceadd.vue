<template>
  <div v-if="isPage" class="device-add-page">
    <div class="page-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <h3>新建设备</h3>
    </div>
    <el-card class="page-card">
      <el-form :model="form" label-width="120px">
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
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
      <div v-if="errorMsg" style="color: red; margin-top: 8px;">{{ errorMsg }}</div>
    </el-card>
  </div>
  <el-dialog v-else v-model="visible" title="新建设备" width="400px" @close="resetForm">
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
      <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
    </template>
    <div v-if="errorMsg" style="color: red; margin-top: 8px;">{{ errorMsg }}</div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const route = useRoute()
const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'success'])

const isPage = computed(() => route.path === '/home/devices/add')
const submitting = ref(false)

const visible = ref(props.visible)
watch(() => props.visible, val => visible.value = val)
watch(visible, val => emit('update:visible', val))

const form = ref({
    devName: '',
    devSerial: '',
    devLocation: '',
    sendmodel: '00',
    baud: '05',
})
const configType = ref('dec')
const configInput = ref('30')
const errorMsg = ref('')

function goBack() {
  router.push('/home/devices')
}

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
        const n = Number(configInput.value)
        if (!isNaN(n)) configInput.value = n.toString(16).toUpperCase()
    } else {
        const n = parseInt(configInput.value, 16)
        if (!isNaN(n)) configInput.value = String(n)
    }
}
async function handleSubmit() {
    submitting.value = true
    errorMsg.value = ''
    if (!form.value.devName || !form.value.devSerial || !form.value.devLocation) {
        errorMsg.value = '请填写完整信息'
        submitting.value = false
        return
    }
    try {
        let configStr = configInput.value
        if (configType.value === 'hex') {
            const n = parseInt(configInput.value, 16)
            configStr = isNaN(n) ? '30' : String(n)
        }
        const res = await api.Adddevice({
            Device: [
                {
                    name: form.value.devName,
                    serial: form.value.devSerial,
                    location: form.value.devLocation,
                    sendmodel: form.value.sendmodel,
                    configdata: configStr,
                    baud: form.value.baud
                }
            ]
        })
        if (res.data && res.data.code === 0) {
            const failureList = res.data.data?.failureList
            if (failureList && failureList.length > 0) {
                errorMsg.value = failureList[0].reason || '添加失败'
            } else {
                ElMessage.success('设备创建成功')
                emit('success')
                if (isPage.value) {
                  router.push('/home/devices')
                } else {
                  visible.value = false
                }
                resetForm()
            }
        } else if (res.data && res.data.reason) {
            errorMsg.value = res.data.reason
        } else {
            errorMsg.value = '添加失败'
        }
    } catch (e) {
        errorMsg.value = '请求失败'
    } finally {
        submitting.value = false
    }
}
</script>

<style scoped>
.el-dialog__body {
    padding-bottom: 0;
}
.device-add-page {
  padding: 0;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
  color: #223147;
}
.page-card {
  max-width: 600px;
}
</style>
