<template>
    <el-select v-model="selectedDevID" placeholder="请选择设备" style="width: 200px;">
        <el-option v-for="item in deviceOptions" :key="item.value" :label="item.label" :value="item.value" />
    </el-select>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../../api'

const props = defineProps({
    modelValue: [String, Number]
})
const emit = defineEmits(['update:modelValue'])

const selectedDevID = ref(props.modelValue !== undefined ? String(props.modelValue) : '')
watch(() => props.modelValue, v => selectedDevID.value = v !== undefined ? String(v) : '')
watch(selectedDevID, v => emit('update:modelValue', v))

const deviceOptions = ref([])
async function fetchDeviceList() {
    const res = await api.getDeviceList()
    let list = []
    if (res.data && res.data.data && res.data.data.devicelist) {
        list = res.data.data.devicelist
    } else if (res.data && res.data.devicelist) {
        list = res.data.devicelist
    }
    deviceOptions.value = (list || []).map(item => ({
        label: item.Devname || item.name || String(item.id),
        value: String(item.id)
    }))
    // 如果当前选中的ID不在新options里，自动切换到第一个设备
    const idList = deviceOptions.value.map(opt => opt.value)
    if (!idList.includes(selectedDevID.value) && deviceOptions.value.length > 0) {
        selectedDevID.value = deviceOptions.value[0].value
    }
}
onMounted(fetchDeviceList)
</script>