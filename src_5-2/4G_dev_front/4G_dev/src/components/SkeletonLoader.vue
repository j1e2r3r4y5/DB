<template>
  <div class="skeleton-grid">
    <div v-for="i in count" :key="i" class="skeleton-card">
      <div class="skeleton-icon pulse"></div>
      <div class="skeleton-text pulse"></div>
      <div class="skeleton-value pulse"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  count: {
    type: Number,
    default: 6
  }
})
</script>

<style scoped>
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.skeleton-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  border-radius: 12px;
  background: #f5f7fa;
}

.skeleton-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-bottom: 12px;
}

.skeleton-text {
  width: 80px;
  height: 16px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.skeleton-value {
  width: 60px;
  height: 24px;
  border-radius: 8px;
}

.pulse {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
