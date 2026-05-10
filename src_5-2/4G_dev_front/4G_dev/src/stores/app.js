import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const loadingText = ref('加载中...')
  const error = ref(null)
  const pageTitle = ref('')

  function setLoading(val, text = '加载中...') {
    loading.value = val
    loadingText.value = text
  }

  function setError(err) {
    error.value = err
  }

  function clearError() {
    error.value = null
  }

  function setPageTitle(title) {
    pageTitle.value = title
    document.title = title ? `${title} - 工业物联网平台` : '工业物联网平台'
  }

  return {
    loading,
    loadingText,
    error,
    pageTitle,
    setLoading,
    setError,
    clearError,
    setPageTitle
  }
})
