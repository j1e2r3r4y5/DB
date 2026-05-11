<template>
    <div>
        <el-breadcrumb style="margin-bottom: 16px;">
            <el-breadcrumb-item :to="{ path: '/home/variables' }">变量管理</el-breadcrumb-item>
            <el-breadcrumb-item>导入变量</el-breadcrumb-item>
        </el-breadcrumb>
        <el-card shadow="never">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <span style="font-weight: bold;">设备：</span>
                <Screening v-model="selectedDevID" @update:model-value="onDeviceChange" />
                <span v-if="!selectedDevID" style="color: #f56c6c; font-size: 13px;">请先选择设备</span>
            </div>
            <el-steps :active="1" align-center style="margin-bottom: 24px;">
                <el-step title="①选择方式" />
                <el-step title="②解析预览" />
                <el-step title="③执行导入" />
            </el-steps>
            <el-tabs v-model="activeTab" @tab-change="onTabChange" style="margin-bottom: 16px;">
                <el-tab-pane label="文件上传" name="file">
                    <el-upload drag accept=".txt" :auto-upload="false" :on-change="handleFileChange" :show-file-list="false">
                        <el-icon class="el-icon--upload" style="font-size: 48px;"><UploadFilled /></el-icon>
                        <div style="margin-top: 8px;">拖拽 .txt 文件到此处，或<em>点击上传</em></div>
                        <template #tip><div style="font-size: 12px; color: #909399;">格式：idx partition address length（每行一个）</div></template>
                    </el-upload>
                    <div v-if="filePreviewItems.length > 0" style="margin-top: 16px;">
                        <div style="font-weight: bold; margin-bottom: 8px;">解析预览（共 {{ filePreviewItems.length }} 条）</div>
                        <el-table :data="filePreviewItems" border size="small" max-height="300">
                            <el-table-column prop="idx" label="序号" width="80" />
                            <el-table-column prop="partition" label="分区" width="80" />
                            <el-table-column prop="address" label="地址" width="100" />
                            <el-table-column prop="length" label="长度" width="80" />
                        </el-table>
                        <el-button type="primary" style="margin-top: 12px;" @click="handleFileImport" :loading="importing" :disabled="!selectedDevID">执行导入</el-button>
                    </div>
                </el-tab-pane>
                <el-tab-pane label="粘贴文本" name="paste">
                    <div style="margin-bottom: 8px; font-size: 13px; color: #909399;">
                        格式：idx partition address length（每行一个，空格分隔）
                    </div>
                    <el-input v-model="pasteText" type="textarea" :rows="8" placeholder="示例：&#10;1 3 100 10&#10;2 4 200 5" @input="onPasteInput" />
                    <div v-if="pastePreviewItems.length > 0" style="margin-top: 16px;">
                        <div style="font-weight: bold; margin-bottom: 8px;">解析预览（共 {{ pastePreviewItems.length }} 条）</div>
                        <el-table :data="pastePreviewItems" border size="small" max-height="300">
                            <el-table-column prop="idx" label="序号" width="80" />
                            <el-table-column prop="partition" label="分区" width="80" />
                            <el-table-column prop="address" label="地址" width="100" />
                            <el-table-column prop="length" label="长度" width="80" />
                        </el-table>
                        <el-button type="primary" style="margin-top: 12px;" @click="handlePasteImport" :loading="importing" :disabled="!selectedDevID">执行导入</el-button>
                    </div>
                </el-tab-pane>
                <el-tab-pane label="Seed生成" name="seed">
                    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                        <el-input v-model="seedValue" placeholder="输入种子字符串（如：test123）" style="width: 300px;" />
                        <el-button type="primary" @click="handleGenerate">生成预览</el-button>
                    </div>
                    <div v-if="generatedVars.length > 0" style="margin-top: 16px;">
                        <div style="font-weight: bold; margin-bottom: 8px;">生成预览（共 {{ generatedVars.length }} 个变量）</div>
                        <el-table :data="generatedVars" border size="small" max-height="300">
                            <el-table-column prop="varName" label="变量名" min-width="140" />
                            <el-table-column prop="dataType" label="数据类型" width="100" />
                            <el-table-column prop="modbusAddr" label="地址" width="80" />
                            <el-table-column prop="data_len" label="长度" width="80" />
                        </el-table>
                        <div style="margin-top: 12px; display: flex; gap: 12px;">
                            <el-button @click="handleExportSeed">导出种子数据</el-button>
                            <el-button type="primary" @click="handleSeedImport" :loading="importing" :disabled="!selectedDevID">执行导入</el-button>
                        </div>
                    </div>
                </el-tab-pane>
            </el-tabs>
            <el-progress v-if="importing" :percentage="importProgress" style="margin-top: 12px;" />
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import Screening from './Screening.vue'
import api from '../../api'
import { parseLine } from '../../utils/importParser'
import { generateFromSeed } from '../../utils/seedGenerator'
import { exportToTxt } from '../../utils/exportUtils'

const router = useRouter()
const route = useRoute()

const selectedDevID = ref(route.query.devId || '')
const activeTab = ref('file')
const importing = ref(false)
const importProgress = ref(0)

const filePreviewItems = ref([])
const pastePreviewItems = ref([])
const pasteText = ref('')
const seedValue = ref('')
const generatedVars = ref([])

function onDeviceChange() {
    router.replace({ query: { ...route.query, devId: selectedDevID.value } })
}

function onTabChange(tab) {
    router.replace({ path: `/home/variables/import/${tab}`, query: { devId: selectedDevID.value } })
}

onMounted(() => {
    const tab = route.path.split('/').pop()
    if (['file', 'paste', 'seed'].includes(tab)) activeTab.value = tab
})

function handleFileChange(file) {
    const reader = new FileReader()
    reader.onload = (e) => {
        const text = e.target.result
        const lines = text.split('\n')
        const items = []
        lines.forEach((line, idx) => {
            if (!line.trim() || line.trim().startsWith('#')) return
            const parsed = parseLine(line)
            if (parsed) items.push({ ...parsed, lineNumber: idx + 1 })
        })
        filePreviewItems.value = items
        if (items.length > 0) ElMessage.success(`解析成功，共 ${items.length} 条`)
        else ElMessage.warning('未解析到有效数据')
    }
    reader.readAsText(file.raw)
}

function onPasteInput() {
    const lines = pasteText.value.split('\n')
    const items = []
    lines.forEach((line, idx) => {
        if (!line.trim() || line.trim().startsWith('#')) return
        const parsed = parseLine(line)
        if (parsed) items.push({ ...parsed, lineNumber: idx + 1 })
    })
    pastePreviewItems.value = items
}

function handleGenerate() {
    if (!seedValue.value) { ElMessage.warning('请输入种子字符串'); return }
    generatedVars.value = generateFromSeed(seedValue.value, 10)
    ElMessage.success(`已生成 ${generatedVars.value.length} 个变量`)
}

function handleExportSeed() {
    if (generatedVars.value.length === 0) return
    const content = generatedVars.value.map((v, i) =>
        `变量${i+1}: ${v.varName}, 数据类型: ${v.dataType}, 地址: ${v.modbusAddr}, 长度: ${v.data_len}`
    ).join('\n')
    exportToTxt(content, `seed_${seedValue.value}.txt`)
    ElMessage.success('导出成功')
}

async function executeImport(variables) {
    if (!selectedDevID.value) { ElMessage.warning('请先选择设备'); return }
    importing.value = true; importProgress.value = 0
    const total = variables.length; let success = 0; let fail = 0
    for (let i = 0; i < total; i++) {
        const v = variables[i]
        try {
            await api.addvariable({
                variable: {
                    devID: Number(selectedDevID.value), varName: v.varName || `var_import_${i}`,
                    dataType: v.dataType || '1', modbusType: v.partition ?? v.modbusType ?? '4',
                    modbusDevice: 1, modbusAddr: v.address ?? v.modbusAddr ?? 0,
                    data_len: v.length ?? v.data_len ?? 1, stringLen: 0
                }
            })
            success++
        } catch (e) { fail++ }
        importProgress.value = Math.round(((i + 1) / total) * 100)
    }
    ElMessage.success(`导入完成：成功 ${success} 个，失败 ${fail} 个`)
    importing.value = false
}

function handleFileImport() {
    if (filePreviewItems.value.length === 0) { ElMessage.warning('请先上传文件'); return }
    executeImport(filePreviewItems.value.map(item => ({
        varName: `file_${item.idx}`, dataType: '1',
        modbusType: String(item.partition), modbusAddr: item.address, data_len: item.length
    })))
}

function handlePasteImport() {
    if (pastePreviewItems.value.length === 0) { ElMessage.warning('请先粘贴有效数据'); return }
    executeImport(pastePreviewItems.value.map(item => ({
        varName: `paste_${item.idx}`, dataType: '1',
        modbusType: String(item.partition), modbusAddr: item.address, data_len: item.length
    })))
}

async function handleSeedImport() {
    if (generatedVars.value.length === 0) { ElMessage.warning('请先生成变量'); return }
    executeImport(generatedVars.value)
}
</script>
