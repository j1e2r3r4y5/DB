<template>
  <div class="device-table-wrapper">
    <el-breadcrumb style="margin-bottom: 16px;">
      <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
      <el-breadcrumb-item>新建变量</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never">
      <template #header>
        <span style="font-weight: 600; font-size: 16px;">新建变量</span>
      </template>
      <el-form :model="form" label-width="110px" style="max-width: 520px;">
        <el-form-item label="变量名">
          <el-input v-model="form.varName" placeholder="请输入变量名" />
        </el-form-item>
        <el-form-item label="数据类型">
          <el-select v-model="form.dataType" placeholder="请选择数据类型" style="width: 100%;">
            <el-option v-for="opt in DataTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据分区">
          <el-select v-model="form.modbusType" placeholder="请选择数据分区" style="width: 100%;">
            <el-option label="0区 线圈 (Coils)" value="0" />
            <el-option label="1区 离散输入 (Discrete Inputs)" value="1" />
            <el-option label="3区 输入寄存器 (Input Registers)" value="3" />
            <el-option label="4区 保持寄存器 (Holding Registers)" value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="Modbus站号">
          <el-input v-model="form.modbusNumber" type="number" placeholder="请输入Modbus站号" />
        </el-form-item>
        <el-form-item label="数据地址">
          <el-input v-model="form.modbusAddr" placeholder="请输入数据地址" />
        </el-form-item>
        <el-form-item label="寄存器数量">
          <el-input v-model="form.data_len" type="number" disabled :placeholder="`自动计算: ${autoRegisterNum}`" />
        </el-form-item>
        <el-form-item label="字符串长度">
          <el-input v-model="form.stringLen" type="number" :disabled="!isStringType(form.dataType)" placeholder="仅字符串类型可填" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { DataTypeOptions, calculateRegisterNum, isStringType } from '../../utils/datatype'

const router = useRouter()
const route = useRoute()
const loading = ref(false)

const form = ref({
  devID: route.query.devId || '',
  varName: '',
  dataType: '',
  modbusType: '',
  modbusNumber: '',
  modbusAddr: '',
  data_len: '',
  stringLen: ''
})

const autoRegisterNum = computed(() => {
  if (!form.value.dataType) return '-'
  const stringLen = parseInt(form.value.stringLen) || 0
  return calculateRegisterNum(form.value.dataType, stringLen)
})

watch([() => form.value.dataType, () => form.value.stringLen], () => {
  const registerNum = autoRegisterNum.value
  if (registerNum !== '-') {
    form.value.data_len = registerNum
  }
})

function handleCancel() {
  router.push('/home/variables')
}

async function handleSubmit() {
  if (!form.value.devID) {
    ElMessage.warning('请通过变量列表页选择设备后再新建变量')
    return
  }
  loading.value = true
  try {
    await api.addvariable({
      variable: {
        devID: Number(form.value.devID),
        varName: form.value.varName,
        dataType: form.value.dataType,
        modbusType: form.value.modbusType,
        modbusDevice: Number(form.value.modbusNumber),
        modbusAddr: Number(form.value.modbusAddr),
        data_len: form.value.data_len,
        stringLen: form.value.stringLen
      }
    })
    ElMessage.success('新建成功')
    router.push('/home/variables')
  } catch (e) {
    ElMessage.error('新建失败：' + (e.message || '接口异常'))
  }
  loading.value = false
}
</script>
