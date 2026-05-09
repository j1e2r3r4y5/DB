<template>
    <div style="display: flex; align-items: center;">
        <el-input v-model="inputCode" placeholder="请输入验证码" style="width: 120px;" />
        <canvas ref="canvasRef" width="120" height="40" style="margin-left: 12px; cursor: pointer;"
            @click="drawCode"></canvas>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const inputCode = ref('')
const code = ref('')
const canvasRef = ref(null)

// 生成随机验证码
function randomCode(len = 5) {
    const chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    let result = ''
    for (let i = 0; i < len; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
}

// 绘制验证码
function drawCode() {
    code.value = randomCode()
    const canvas = canvasRef.value
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = '#f3f3f3'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    // 绘制干扰线
    for (let i = 0; i < 5; i++) {
        ctx.strokeStyle = '#' + Math.floor(Math.random() * 16777215).toString(16)
        ctx.beginPath()
        ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height)
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height)
        ctx.stroke()
    }
    // 绘制验证码字符
    for (let i = 0; i < code.value.length; i++) {
        ctx.font = `${24 + Math.random() * 8}px Arial`
        ctx.fillStyle = '#' + Math.floor(Math.random() * 16777215).toString(16)
        ctx.save()
        ctx.translate(20 * i + 10, 30)
        ctx.rotate((Math.random() - 0.5) * 0.5)
        ctx.fillText(code.value[i], 0, 0)
        ctx.restore()
    }
    // 绘制干扰点
    for (let i = 0; i < 30; i++) {
        ctx.fillStyle = '#' + Math.floor(Math.random() * 16777215).toString(16)
        ctx.beginPath()
        ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, 1, 0, 2 * Math.PI)
        ctx.fill()
    }
}

// 校验方法，供父组件调用
defineExpose({
    inputCode,
    code,
    validate() {
        return inputCode.value.trim().toUpperCase() === code.value
    },
    drawCode,
    refreshCode() {
        inputCode.value = ''
        drawCode()
    }
})

onMounted(drawCode)
</script>