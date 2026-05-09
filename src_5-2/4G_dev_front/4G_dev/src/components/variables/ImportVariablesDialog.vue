<template>
    <el-dialog v-model="visible" title="导入变量" width="600px" @close="resetForm">
        <el-tabs v-model="activeTab" type="border-card">
            <el-tab-pane label="文件上传" name="file">
                <el-upload ref="uploadRef" class="upload-demo" drag :auto-upload="false"
                    :limit="1" accept=".txt" :on-change="handleFileChange">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
                    <template #tip>
                        <div class="el-upload__tip">支持 .txt 格式文件（UTF-8编码）</div>
                    </template>
                </el-upload>
            </el-tab-pane>
            <el-tab-pane label="粘贴文本" name="paste">
                <el-input v-model="pasteContent" type="textarea" :rows="10"
                    placeholder="请粘贴变量数据，格式：idx partition address length" />
            </el-tab-pane>
            <el-tab-pane label="Seed生成" name="seed">
                <el-form label-width="100px">
                    <el-form-item label="Seed">
                        <el-input v-model="seedInput" placeholder="输入随机种子，如 seed123" />
                    </el-form-item>
                </el-form>
                <div style="display: flex; gap: 12px;">
                    <el-button type="primary" @click="handleSeedGenerate" :loading="seedLoading">
                        生成数据
                    </el-button>
                    <el-button type="success" @click="handleExportSeedData" 
                        :disabled="!isSeedGenerated || !previewList.length"
                        v-if="activeTab === 'seed'">
                        导出数据
                    </el-button>
                </div>
            </el-tab-pane>
        </el-tabs>

        <div v-if="previewList.length > 0" style="margin-top: 16px;">
            <el-divider>预览（共 {{ previewList.length }} 个变量）</el-divider>
            <el-table :data="previewList.slice(0, 20)" size="small" border max-height="300">
                <el-table-column prop="varName" label="变量名" width="80" />
                <el-table-column prop="partition" label="分区" width="120">
                    <template #default="{ row }">
                        {{ row.partition === 1 ? '1区(离散输入)' : '4区(保持寄存器)' }}
                    </template>
                </el-table-column>
                <el-table-column prop="address" label="地址" width="100" />
                <el-table-column prop="length" label="长度" width="80" />
                <el-table-column prop="dataType" label="数据类型" width="100">
                    <template #default="{ row }">
                        {{ row.dataType === '0' ? 'bool' : 'string' }}
                    </template>
                </el-table-column>
            </el-table>
            <div v-if="previewList.length > 20" style="color: #909399; text-align: center; margin-top: 8px;">
                仅显示前20条，共 {{ previewList.length }} 条...
            </div>
        </div>

        <div v-if="errorMsg" style="margin-top: 12px;">
            <el-alert type="error" :closable="false">{{ errorMsg }}</el-alert>
        </div>

        <div v-if="importProgress > 0 && importProgress < 100" style="margin-top: 16px;">
            <el-progress :percentage="importProgress" :status="importStatus" />
            <div style="text-align: center; margin-top: 4px; color: #909399; font-size: 13px;">
                {{ importProgressText }}
            </div>
        </div>

        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleImport" :loading="loading" :disabled="previewList.length === 0">
                确认导入
            </el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../../api'
import { DataType } from '../../utils/datatype'

const MAX_BITS = 1536
const MAX_REGS = 12288
const ADDRESS_SPACE_END = 65535

function seededRandom(seed) {
    let state = 0
    for (let i = 0; i < seed.length; i++) {
        state = ((state << 5) - state + seed.charCodeAt(i)) | 0
    }
    return function() {
        state = (Math.imul(1664525, state) + 1013904223) | 0
        return (state >>> 0) / 0xFFFFFFFF
    }
}

function randInt(rng, min, max) {
    return Math.floor(rng() * (max - min + 1)) + min
}

function randChoice(rng, arr) {
    return arr[Math.floor(rng() * arr.length)]
}

function computeFreeIntervals(existing) {
    if (!existing || existing.length === 0) {
        return [[0, ADDRESS_SPACE_END]]
    }
    const sorted = [...existing].sort((a, b) => a[0] - b[0])
    const free = []
    if (sorted[0][0] > 0) {
        free.push([0, sorted[0][0] - 1])
    }
    for (let i = 0; i < sorted.length - 1; i++) {
        if (sorted[i][1] + 1 <= sorted[i + 1][0] - 1) {
            free.push([sorted[i][1] + 1, sorted[i + 1][0] - 1])
        }
    }
    if (sorted[sorted.length - 1][1] < ADDRESS_SPACE_END) {
        free.push([sorted[sorted.length - 1][1] + 1, ADDRESS_SPACE_END])
    }
    return free
}

function generateFromSeed(seedStr) {
    const rng = seededRandom(seedStr)
    const S = randInt(rng, 1, 30)
    const intervals_1 = []
    const intervals_4 = []
    let used_bits_1 = 0
    let used_regs_4 = 0

    for (let i = 0; i < S; i++) {
        const can_1 = used_bits_1 < MAX_BITS
        const can_4 = used_regs_4 < MAX_REGS
        if (!can_1 && !can_4) break

        let zone
        if (can_1 && can_4) {
            zone = randChoice(rng, [1, 4])
        } else if (can_1) {
            zone = 1
        } else {
            zone = 4
        }

        if (zone === 1) {
            const freeIntervals = computeFreeIntervals(intervals_1)
            if (freeIntervals.length === 0) continue
            const [f_start, f_end] = randChoice(rng, freeIntervals)
            const max_len = Math.min(f_end - f_start + 1, MAX_BITS - used_bits_1)
            if (max_len < 1) continue
            const length = randInt(rng, 1, max_len)
            const start = randInt(rng, f_start, f_end - length + 1)
            intervals_1.push([start, start + length - 1])
            used_bits_1 += length
        } else {
            const freeIntervals = computeFreeIntervals(intervals_4)
            if (freeIntervals.length === 0) continue
            const [f_start, f_end] = randChoice(rng, freeIntervals)
            const max_len = Math.min(f_end - f_start + 1, MAX_REGS - used_regs_4)
            if (max_len < 1) continue
            const length = randInt(rng, 1, max_len)
            const start = randInt(rng, f_start, f_end - length + 1)
            intervals_4.push([start, start + length - 1])
            used_regs_4 += length
        }
    }

    const original = []
    for (const [s, e] of intervals_1) {
        for (let bit = s; bit <= e; bit++) {
            original.push({ partition: 1, address: bit, length: 1 })
        }
    }
    for (const [s, e] of intervals_4) {
        original.push({ partition: 4, address: s, length: e - s + 1 })
    }
    original.sort((a, b) => a.partition - b.partition || a.address - b.address)
    return original.map((item, idx) => ({ idx: idx + 1, ...item }))
}

const props = defineProps({
    modelValue: Boolean,
    deviceId: [String, Number],
    deviceSn: String
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => visible.value = v)
watch(visible, v => emit('update:modelValue', v))

const activeTab = ref('file')
const uploadRef = ref(null)
const pasteContent = ref('')
const seedInput = ref('')
const seedLoading = ref(false)
const loading = ref(false)
const previewList = ref([])
const errorMsg = ref('')
const importProgress = ref(0)
const importStatus = ref('')
const importProgressText = ref('')
const currentSeed = ref('') // 记录当前用于生成数据的 seed
const isSeedGenerated = ref(false) // 标记当前预览数据是否由 Seed 生成

function resetForm() {
    activeTab.value = 'file'
    pasteContent.value = ''
    seedInput.value = ''
    previewList.value = []
    errorMsg.value = ''
    currentSeed.value = ''
    isSeedGenerated.value = false
    if (uploadRef.value) {
        uploadRef.value.clearFiles()
    }
}

function parseLine(line) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return null
    const parts = trimmed.split(/\s+/)
    if (parts.length < 4) return null
    const idx = parseInt(parts[0])
    const partition = parseInt(parts[1])
    const address = parseInt(parts[2])
    const length = parseInt(parts[3])
    if (isNaN(idx) || isNaN(partition) || isNaN(address) || isNaN(length)) return null
    if (partition !== 1 && partition !== 4) return null
    if (address < 0 || address > 65535) return null
    if (length <= 0) return null
    return { idx, partition, address, length }
}

function buildPreview(parsedList) {
    return parsedList.map(item => {
        const varName = String(item.idx)
        const dataType = item.partition === 1 ? DataType.BOOL : DataType.STRING
        const data_len = item.partition === 1 ? 1 : item.length
        const modbusType = item.partition === 1 ? '1' : '4'
        return {
            varName,
            dataType,
            modbusType,
            modbusDevice: 1,
            modbusAddr: item.address,
            data_len,
            stringLen: item.partition === 4 ? item.length : undefined,
            scope: 'sandbox'
        }
    })
}

function processParsedList(parsedList) {
    if (!parsedList || parsedList.length === 0) {
        errorMsg.value = '未解析到有效数据'
        previewList.value = []
        return
    }
    errorMsg.value = ''
    previewList.value = buildPreview(parsedList)
}

async function handleFileChange(file) {
    try {
        const text = await file.raw.text()
        const lines = text.split('\n')
        const parsedList = []
        for (const line of lines) {
            const item = parseLine(line)
            if (item) parsedList.push(item)
        }
        processParsedList(parsedList)
        isSeedGenerated.value = false
        currentSeed.value = ''
    } catch (e) {
        errorMsg.value = '文件读取失败：' + e.message
        previewList.value = []
        isSeedGenerated.value = false
        currentSeed.value = ''
    }
}

function handlePasteInput() {
    if (!pasteContent.value.trim()) {
        previewList.value = []
        errorMsg.value = ''
        isSeedGenerated.value = false
        currentSeed.value = ''
        return
    }
    const lines = pasteContent.value.split('\n')
    const parsedList = []
    for (const line of lines) {
        const item = parseLine(line)
        if (item) parsedList.push(item)
    }
    processParsedList(parsedList)
    isSeedGenerated.value = false
    currentSeed.value = ''
}

watch(pasteContent, () => {
    handlePasteInput()
})

function handleSeedGenerate() {
    if (!seedInput.value.trim()) {
        ElMessage.warning('请输入Seed')
        return
    }
    seedLoading.value = true
    try {
        const result = generateFromSeed(seedInput.value.trim())
        const parsedList = result.map(item => ({
            idx: item.idx,
            partition: item.partition,
            address: item.address,
            length: item.length
        }))
        processParsedList(parsedList)
        currentSeed.value = seedInput.value.trim()
        isSeedGenerated.value = true
        ElMessage.success('生成成功')
    } catch (e) {
        errorMsg.value = '生成失败：' + e.message
        previewList.value = []
        currentSeed.value = ''
        isSeedGenerated.value = false
    } finally {
        seedLoading.value = false
    }
}

// 导出 Seed 生成的数据
function handleExportSeedData() {
    if (!isSeedGenerated.value || !previewList.value.length) {
        ElMessage.warning('请先生成数据')
        return
    }
    if (!currentSeed.value) {
        ElMessage.warning('无法获取 Seed 信息')
        return
    }
    
    try {
        // 构建导出内容，使用和导入相同的格式：idx partition address length
        // 需要从原始生成数据中获取，而不是从 previewList
        // 重新生成一次来获取原始格式数据
        const result = generateFromSeed(currentSeed.value)
        const content = result.map(item => 
            `${item.idx} ${item.partition} ${item.address} ${item.length}`
        ).join('\n')
        
        // 创建下载
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        
        // 文件名包含 seed 值（替换掉文件名中不允许的字符）
        const safeSeed = currentSeed.value.replace(/[<>:"/\\|?*]/g, '_')
        link.download = `seed_${safeSeed}_variables.txt`
        link.href = url
        link.click()
        
        URL.revokeObjectURL(url)
        ElMessage.success('导出成功')
    } catch (e) {
        ElMessage.error('导出失败：' + e.message)
    }
}

async function handleImport() {
    if (previewList.value.length === 0) {
        ElMessage.warning('没有可导入的变量')
        return
    }
    if (!props.deviceId) {
        ElMessage.warning('请先选择设备')
        return
    }
    loading.value = true
    importProgress.value = 0
    importStatus.value = ''
    importProgressText.value = '准备导入...'
    let successCount = 0
    let failCount = 0
    const total = previewList.value.length
    try {
        // 构建批量数据
        const variables = previewList.value.map(v => ({
            devID: Number(props.deviceId),
            varName: v.varName,
            dataType: v.dataType,
            modbusType: v.modbusType,
            modbusDevice: v.modbusDevice,
            modbusAddr: v.modbusAddr,
            data_len: v.data_len,
            stringLen: v.stringLen || 0,
            scope: 'sandbox'
        }))
        importProgressText.value = `正在批量导入 ${total} 个变量...`
        importProgress.value = 10
        try {
            const res = await api.batchAddvariable({ variables })
            importProgress.value = 90
            if (res.data && res.data.data) {
                successCount = res.data.data.successCount || 0
                failCount = total - successCount
            } else {
                successCount = total
                failCount = 0
            }
            importProgressText.value = `批量导入完成：成功 ${successCount} / ${total}`
            importProgress.value = 100
            importStatus.value = 'success'
        } catch (batchErr) {
            console.warn('批量导入失败，回退到逐条导入:', batchErr)
            importProgressText.value = '批量接口不可用，逐条导入中...'
            importProgress.value = 5
            const CONCURRENCY = 5
            const chunks = []
            for (let i = 0; i < variables.length; i += CONCURRENCY) {
                chunks.push(variables.slice(i, i + CONCURRENCY))
            }
            for (let ci = 0; ci < chunks.length; ci++) {
                const chunk = chunks[ci]
                const results = await Promise.allSettled(
                    chunk.map(v => api.addvariable({ variable: v }))
                )
                results.forEach(r => {
                    if (r.status === 'fulfilled') {
                        successCount++
                    } else {
                        failCount++
                    }
                })
                const pct = Math.min(Math.round(((ci + 1) / chunks.length) * 90) + 5, 95)
                importProgress.value = pct
                importProgressText.value = `正在导入... ${successCount + failCount}/${total}`
            }
            importProgress.value = 100
            importStatus.value = failCount === 0 ? 'success' : 'warning'
            importProgressText.value = `导入完成：成功 ${successCount}，失败 ${failCount}`
        }
        await new Promise(r => setTimeout(r, 500))
        if (failCount === 0) {
            ElMessage.success(`导入成功：共 ${successCount} 个变量`)
        } else {
            ElMessage.warning(`部分导入成功：成功 ${successCount} 个，失败 ${failCount} 个`)
        }
        emit('success')
        visible.value = false
        resetForm()
    } finally {
        loading.value = false
        importProgress.value = 0
    }
}
</script>
