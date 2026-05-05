<template>
    <el-dialog v-model="visible" :title="dialogTitle" width="400px">
        <el-form :model="form" label-width="100px">
            <el-form-item label="发送模式">
                <el-select v-model="form.sendmodel" placeholder="请选择发送模式" disabled>
                    <el-option label="定时发送" value="00" />
                </el-select>
            </el-form-item>
            <el-form-item label="发送间隔(秒)">
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
        <div
            style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 8px; min-height: 24px;">
            <div>
                <span v-if="isBatch" style="color: #888; font-size: 13px;">批量配置</span>
                <span v-else></span>
            </div>
            <span v-if="isBatch" style="color: #888; font-size: 13px;">正在修改{{ batchCount }}个设备</span>
            <span v-else style="color: #888; font-size: 13px;">正在配置：{{ form.name }}</span>
        </div>
        <div style="position: absolute; left: 16px; right: 16px; bottom: 16px; font-size: 13px;">
            <span v-if="resultMsg" :style="{ color: resultType === 'success' ? '#67C23A' : '#F56C6C' }">{{ resultMsg
            }}</span>
        </div>
        <template #footer>
            <el-button @click="close">取消</el-button>
            <!-- <el-button @click="queryDevStatus">调试查询</el-button> -->
            <el-button type="primary" :loading="loading" :disabled="!isFormChanged"
                @click="handleConfirm">下发配置</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { toRefs, watchEffect } from 'vue'
import { ref, watch, computed } from 'vue'
// import { ElMessage } from 'element-plus'
import api from '../api'

const props = defineProps({
    modelValue: Boolean,
    row: Object,
    rows: Array // 批量配置时传 rows
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const isBatch = computed(() => Array.isArray(props.rows) && props.rows.length > 1)
const batchCount = computed(() => (props.rows && props.rows.length) || 0)
const dialogTitle = computed(() => isBatch.value ? '批量配置' : '配置')
const form = ref({})
const configType = ref('dec')
const configInput = ref('')
const loading = ref(false)
const resultMsg = ref("")
const resultType = ref("") // 'success' or 'error'

// 记录初始表单和输入框内容
const initialForm = ref({})
const initialConfigInput = ref("")

// 是否有改动
const isFormChanged = ref(false)

// 监听弹窗打开时记录初始值
watch([visible], ([v]) => {
    if (v) {
        initialForm.value = JSON.stringify(form.value)
        initialConfigInput.value = configInput.value
        isFormChanged.value = false
    }
})

// 监听表单和输入框变化
watch([form, configInput], () => {
    const formChanged = JSON.stringify(form.value) !== initialForm.value
    const inputChanged = configInput.value !== initialConfigInput.value
    isFormChanged.value = formChanged || inputChanged
}, { deep: true })

function getDefaultDevice() {
    if (isBatch.value && props.rows && props.rows.length) {
        let minDev = props.rows[0]
        for (const dev of props.rows) {
            if (Number(dev.id) < Number(minDev.id)) minDev = dev
        }
        return minDev
    } else if (props.row) {
        return props.row
    }
    return {}
}

watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))
// 监听设备数据变化，填充配置下发表单
// 问题修复：后端返回的字段名与前端不一致，需要做字段映射
// 后端返回：serial, configdata, Devname, DevLocation
// 前端使用：sn, config, name, location
watch([() => props.row, () => props.rows], () => {
    const dev = getDefaultDevice()
    if (dev) {
        // 统一字段名映射，解决后端字段名与前端不一致的问题
        form.value = {
            ...dev,
            sn: dev.serial || dev.sn,                  // 后端 serial -> 前端 sn
            config: dev.configdata || dev.config,    // 后端 configdata -> 前端 config
            name: dev.name || dev.Devname,            // 兼容不同命名
            location: dev.location || dev.DevLocation, // 兼容不同命名
        }
    } else {
        form.value = {}
    }
    configType.value = 'dec'
    configInput.value = dev && (dev.config || dev.configdata) ? String(dev.config || dev.configdata) : ''
    resultMsg.value = ""
    resultType.value = ""
}, { immediate: true })

// 联动：切换进制时自动转换输入框内容
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

function close() {
    visible.value = false
    emit('success') // 关闭时通知父组件刷新
}

// ===================== 工具函数：十六进制字符串转字节 =====================
function hexToByte(hexStr) {
    return parseInt(hexStr, 16)
}

async function handleConfirm() {
    loading.value = true
    resultMsg.value = "";
    resultType.value = "";
    try {
        // configInput 存库时始终转为十进制字符串
        let configStr = ''
        let configData = 0
        if (configType.value === 'hex') {
            configData = parseInt(configInput.value, 16)
            configStr = String(isNaN(configData) ? 0 : configData)
        } else {
            configData = Number(configInput.value)
            configStr = String(configData)
        }
        // 发送模式和波特率转为字节
        const sendMode = hexToByte(form.value.sendmodel || '00')
        const baudRate = hexToByte(form.value.baud || '00')
        
        if (isBatch.value && props.rows && props.rows.length) {
            // 批量配置
            // 先全部下发命令
            for (const dev of props.rows) {
                await api.sendModuleConfig({
                    devSerial: dev.sn,
                    sendMode: sendMode,
                    configData: configData,
                    baudRate: baudRate
                })
            }

            // 批量查询统计
            setTimeout(async () => {
                try {
                    let successCount = 0;
                    let failCount = 0;
                    for (const dev of props.rows) {
                        const params = {
                            org: 'myorg',
                            bucket: 'mybucket',
                            dev_serial: dev.sn || '',
                            featurescode: 0x02
                        }
                        const queryRes = await api.query(params)
                        let arr = null;
                        if (queryRes && queryRes.data) {
                            if (Array.isArray(queryRes.data.data)) {
                                arr = queryRes.data.data;
                            } else if (queryRes.data.data && Array.isArray(queryRes.data.data.data)) {
                                arr = queryRes.data.data.data;
                            }
                        }
                        let found = false;
                        let isSuccess = false;
                        if (arr) {
                            for (const item of arr) {
                                if (
                                    item.field === 'success' &&
                                    item.dev_serial === dev.sn &&
                                    String(item.features_code) === String(0x02)
                                ) {
                                    found = true;
                                    if (item.value === '00') {
                                        successCount++;
                                        isSuccess = true;
                                    } else {
                                        failCount++;
                                    }
                                    break;
                                }
                            }
                        }
                        if (!found) failCount++;
                        // 只有成功才更新数据库
                        if (isSuccess) {
                            const data = {
                            ID: dev.id,
                            Devname: dev.name,
                            DevSerial: dev.sn,
                            DevLocation: dev.location,
                            Sendmodel: form.value.sendmodel,
                            Configdata: configStr,
                            Baud: form.value.baud,
                        }
                        await api.ModifyDevice(data)
                        // emit('success')
                    }
                }
                resultMsg.value = `下发成功${successCount}个，失败${failCount}个`;
                    resultType.value = successCount > 0 && failCount === 0 ? 'success' : 'error';
                } catch (e) {
                    resultMsg.value = "批量查询失败";
                    resultType.value = "error";
                    // console.error('批量查询接口异常:', e);
                } finally {
                    loading.value = false;
                    // 不自动关闭弹窗
                }
            }, 2000)
        } else {
            // 单个配置
            await api.sendModuleConfig({
                devSerial: form.value.sn,
                sendMode: sendMode,
                configData: configData,
                baudRate: baudRate
            })

            // 查询前保持 loading，收到查询结果后再关闭 loading
            setTimeout(async () => {
                try {
                    const params = {
                        org: 'myorg',
                        bucket: 'mybucket',
                        dev_serial: form.value.sn || '',
                        featurescode: 0x02 // 功能码，举例
                    }
                    const queryRes = await api.query(params)
                    let found = false;
                    let arr = null;
                    let isSuccess = false;
                    // console.log('查询结果:', queryRes);
                    if (queryRes && queryRes.data) {
                        if (Array.isArray(queryRes.data.data)) {
                            arr = queryRes.data.data;
                        } else if (queryRes.data.data && Array.isArray(queryRes.data.data.data)) {
                            arr = queryRes.data.data.data;
                        }
                    }
                    if (arr) {
                        const devSerial = form.value.sn || '';
                        const featuresCode = String(0x02);
                        for (const item of arr) {
                            if (
                                item.field === 'success' &&
                                item.dev_serial === devSerial &&
                                String(item.features_code) === featuresCode
                            ) {
                                if (item.value === '00') {
                                    resultMsg.value = "下发成功";
                                    resultType.value = "success";
                                    isSuccess = true;
                                } else {
                                    resultMsg.value = "下发失败";
                                    resultType.value = "error";
                                }
                                found = true;
                                break;
                            }
                        }
                    }
                    if (!found) {
                        resultMsg.value = "未找到下发结果";
                        resultType.value = "error";
                    }
                    // 只有成功才更新数据库
                    if (isSuccess) {
                        const data = {
                            ID: form.value.id,
                            Devname: form.value.name,
                            DevSerial: form.value.sn,
                            DevLocation: form.value.location,
                            Sendmodel: form.value.sendmodel,
                            Configdata: configStr,
                            Baud: form.value.baud,
                        }
                        await api.ModifyDevice(data)
                        emit('refresh')
                    }
                } catch (e) {
                    resultMsg.value = "查询失败"
                    resultType.value = "error"
                    console.error('查询接口异常:', e)
                } finally {
                    loading.value = false;
                }
            }, 2000)
        }
        // 不自动关闭弹窗，需用户手动操作
    } catch (e) {
        loading.value = false;
        throw e;
    }
}

// // 查询时序数据库接口调用示例
// async function queryDevStatus() {
//     const params = {
//         org: 'myorg', // 组织
//         bucket: 'mybucket', // 存储桶
//         dev_serial: form.value.sn || '', // 设备序列号
//         featurescode: 0x02 // 功能码，举例
//     }
//     try {
//         const res = await api.query(params)
//         console.log('时序数据库查询结果:', res)
//         // 这里可以根据实际返回做后续处理
//     } catch (e) {
//         console.error('时序数据库查询失败:', e)
//     }
// }
</script>