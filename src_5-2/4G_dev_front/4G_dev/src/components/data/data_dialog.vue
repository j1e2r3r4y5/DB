<template>
    <el-dialog :model-value="modelValue" @update:modelValue="emit('update:modelValue', $event)" title="历史数据"
        width="600px">
        <div style="max-height: 400px; overflow: auto;">
            <el-table :data="historyData" style="width: 100%;">
                <el-table-column prop="value" label="数据值" min-width="100"></el-table-column>
                <el-table-column prop="time" label="时间" min-width="160"></el-table-column>

            </el-table>
        </div>
        <template #footer>
            <el-button @click="close">关闭</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
// import { defineProps, defineEmits } from 'vue'
const props = defineProps({
    modelValue: Boolean,
    historyData: Array
})
const emit = defineEmits(['update:modelValue'])
function close() {
    emit('update:modelValue', false)
}
</script>