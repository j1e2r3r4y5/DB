<template>
  <OfflineBanner />
  <router-view />
</template>

<script setup>
import OfflineBanner from '../components/OfflineBanner.vue'
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
}
</style>
