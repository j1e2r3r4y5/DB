<template>
  <div class="device-table-wrapper">
    <el-breadcrumb style="margin-bottom: 16px;">
      <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
      <el-breadcrumb-item>编辑变量</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never">
      <template #header>
        <span style="font-weight: 600; font-size: 16px;">编辑变量</span>
      </template>
      <div v-if="!form.id" style="text-align: center; padding: 40px; color: #909399;">
        加载变量信息中...
      </div>
      <el-form v-else :model="form" label-width="110px" style="max-width: 520px;">
        <el-form-item label="变量名">
          <el-input v-model="form.varName" placeholder="请输入变量名" />
        </el-form-item>
        <el-form-item label="数据类型">
          <el-select v-model="form.dataType" placeholder="请选择数据类型" style="width: 100%;">
            <el-option v-for="opt in DataTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="Modbus类型">
          <el-select v-model="form.modbusType" placeholder="请选择Modbus类型" style="width: 100%;">
            <el-option label="0区 线圈 (Coils)" value="0" />
            <el-option label="1区 离散输入 (Discrete Inputs)" value="1" />
            <el-option label="3区 输入寄存器 (Input Registers)" value="3" />
            <el-option label="4区 保持寄存器 (Holding Registers)" value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="Modbus从站">
          <el-input v-model="form.modbusDevice" type="number" placeholder="请输入Modbus从站号" />
        </el-form-item>
        <el-form-item label="Modbus地址">
          <el-input v-model="form.modbusAddr" placeholder="请输入Modbus地址" />
        </el-form-item>
        <el-form-item label="寄存器数量">
          <el-input v-model="form.data_len" type="number" disabled :placeholder="`自动计算: ${autoRegisterNum}`" />
        </el-form-item>
        <el-form-item label="字符串长度">
          <el-input v-model="form.stringLen" type="number" :disabled="!isStringType(form.dataType)" placeholder="仅字符串类型可填" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">保存</el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { DataTypeOptions, calculateRegisterNum, isStringType } from '../../utils/datatype'

const router = useRouter()
const route = useRoute()
const loading = ref(false)

const form = ref({
  id: '',
  devID: '',
  varName: '',
  dataType: '',
  modbusType: '',
  modbusDevice: '',
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

async function loadVariable(id) {
  try {
    const res = await api.getvariables({})
    let list = []
    if (res.data && res.data.data && Array.isArray(res.data.data.variables)) {
      list = res.data.data.variables
    } else if (res.data && Array.isArray(res.data.variables)) {
      list = res.data.variables
    }
    const variable = list.find(v => String(v.id) === String(id) || String(v.iD) === String(id))
    if (variable) {
      form.value = {
        id: variable.id ?? variable.iD ?? '',
        devID: variable.devID ?? '',
        varName: variable.varName ?? '',
        dataType: variable.dataType ?? '',
        modbusType: variable.modbusType ?? '',
        modbusDevice: variable.modbusDevice ?? '',
        modbusAddr: variable.modbusAddr ?? '',
        data_len: variable.data_len ?? '',
        stringLen: variable.stringLen ?? ''
      }
    } else {
      ElMessage.error('未找到该变量')
      router.push('/home/variables')
    }
  } catch (e) {
    ElMessage.error('加载变量信息失败')
    router.push('/home/variables')
  }
}

async function handleSubmit() {
  if (!form.value.id) {
    ElMessage.warning('变量信息不完整')
    return
  }
  loading.value = true
  try {
    await api.modifyvariable({
      variable: {
        id: form.value.id,
        devID: Number(form.value.devID),
        varName: form.value.varName,
        dataType: form.value.dataType,
        modbusType: form.value.modbusType,
        modbusDevice: Number(form.value.modbusDevice),
        modbusAddr: Number(form.value.modbusAddr),
        data_len: form.value.data_len,
        stringLen: form.value.stringLen
      }
    })
    ElMessage.success('修改成功')
    router.push('/home/variables')
  } catch (e) {
    ElMessage.error('修改失败：' + (e.message || '接口异常'))
  }
  loading.value = false
}

onMounted(() => {
  const id = route.params.id
  if (id) {
    loadVariable(id)
  } else {
    ElMessage.error('缺少变量ID')
    router.push('/home/variables')
  }
})
</script>
