import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('userId') || '')
  const userType = ref(Number(localStorage.getItem('userType') || 0))
  const token = ref(localStorage.getItem('token') || '')
  const username = ref('')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userType.value === 0 || userType.value === 1)

  function setUser(data) {
    userId.value = data.id || ''
    userType.value = data.type || 0
    token.value = data.token || ''
    username.value = data.username || ''
    
    localStorage.setItem('userId', data.id || '')
    localStorage.setItem('userType', String(data.type || 0))
    localStorage.setItem('token', data.token || '')
  }

  function logout() {
    userId.value = ''
    userType.value = 0
    token.value = ''
    username.value = ''
    
    localStorage.removeItem('userId')
    localStorage.removeItem('userType')
    localStorage.removeItem('token')
  }

  function hasPermission(requiredType) {
    if (requiredType === 'admin') {
      return isAdmin.value
    }
    return true
  }

  return {
    userId,
    userType,
    token,
    username,
    isLoggedIn,
    isAdmin,
    setUser,
    logout,
    hasPermission
  }
})
