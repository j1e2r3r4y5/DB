<template>
    <el-dialog :model-value="modelValue" @update:modelValue="emit('update:modelValue', $event)" title="历史数据"
        width="600px">
        <div style="max-height: 400px; overflow: auto;">
            <el-table :data="historyData" style="width: 100%;">
                <el-table-column label="数据值" min-width="150">
                    <template #default="scope">
                        {{ formatHistoryValue(scope.row) }}
                    </template>
                </el-table-column>
                <el-table-column prop="time" label="时间" min-width="160"></el-table-column>

            </el-table>
        </div>
        <template #footer>
            <el-button @click="close">关闭</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { DataType } from '../../utils/datatype'

const props = defineProps({
    modelValue: Boolean,
    historyData: Array
})
const emit = defineEmits(['update:modelValue'])

// 格式化历史数据值
function formatHistoryValue(row) {
    // 优先使用解析后的值
    if (row.valueBool !== undefined && row.valueBool !== null) {
        return row.valueBool ? 'true' : 'false'
    }
    if (row.valueString) {
        return row.valueString
    }
    if (row.valueFloat !== undefined && row.valueFloat !== null) {
        // 修复浮点数显示问题
        const val = Number(row.valueFloat)
        if (!isNaN(val)) {
            // 检查是否接近整数
            if (Math.abs(val - Math.round(val)) < 0.0000001) {
                return Math.round(val)
            }
            // 固定显示6位小数
            return val.toFixed(6)
        }
        return row.valueFloat
    }
    if (row.valueInt !== undefined && row.valueInt !== null) {
        return row.valueInt
    }
    if (row.parsedValue !== undefined && row.parsedValue !== null) {
        return row.parsedValue
    }
    // 回退到原始值
    return row.value ?? '-'
}

function close() {
    emit('update:modelValue', false)
}
</script>