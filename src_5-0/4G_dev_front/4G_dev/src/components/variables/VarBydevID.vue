<!-- <template>
    <el-dialog v-model="visible" title="变量列表" width="1000px" @close="reset">
        <el-table :data="varList" style="width: 100%">
            <el-table-column prop="id" label="变量ID" min-width="60" />
            <el-table-column prop="varName" label="变量名" min-width="120" />
            <el-table-column prop="dataType" label="数据类型" min-width="100" :formatter="dataTypeFormatter" />
            <el-table-column prop="modbusDevice" label="Modbus从站" min-width="100" />
            <el-table-column prop="modbusAddr" label="Modbus地址" min-width="100" />
            <el-table-column prop="data_len" label="数据长度" min-width="120" />
            <el-table-column prop="stringLen" label="字符串长度" min-width="100" />
            <el-table-column prop="decimalDigits" label="小数位数" min-width="100" />
        </el-table>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../../api'
const props = defineProps({
    modelValue: Boolean,
    deviceId: [String, Number]
})
const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

const varList = ref([])

const dataTypeMap = {
    '1': '整数',
    '2': '浮点数',
    '3': '定点数',
    '4': '字符串'
}
function dataTypeFormatter(row) {
    return dataTypeMap[row.dataType] || row.dataType
}

function reset() {
    varList.value = []
}

watch(
    () => [visible.value, props.deviceId],
    async ([show, id]) => {
        if (show && id) {
            const res = await api.getvarbydeviceid({ deviceId: id })
            let list = []
            if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
                list = res.data.data.variables
            }
            varList.value = (list || []).map(item => ({
                id: item.iD ?? item.id ?? '',
                varName: item.varName ?? '',
                dataType: item.dataType ?? '',
                modbusDevice: item.modbusDevice ?? '',
                modbusAddr: item.modbusAddr ?? '',
                data_len: item.data_len ?? item.dataLen ?? '', // 新增数据长度字段
                stringLen: item.stringLen ?? '',
                decimalDigits: item.decimalDigits ?? ''
            }))

        }
    },
    { immediate: true }
)
</script> -->