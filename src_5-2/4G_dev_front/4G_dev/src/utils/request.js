import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const service = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000
})

service.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

function redirectToLogin() {
  localStorage.removeItem('userId')
  localStorage.removeItem('userType')
  localStorage.removeItem('token')
  setTimeout(() => {
    router.push('/login')
  }, 500)
}

service.interceptors.response.use(
  response => {
    if (response.data && (
      response.data.message === '未登录' ||
      response.data.message === 'token已失效' ||
      response.data.message === '未登录或登录过期，请重新登陆'
    )) {
      ElMessage.error('登录已失效，请重新登录')
      redirectToLogin()
      return Promise.reject(new Error('登录已失效'))
    }
    return response
  },
  error => {
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        ElMessage.error('请求超时，请检查后端服务是否运行')
      } else {
        ElMessage.error('网络异常，请检查网络连接或后端服务')
      }
    } else if (error.response.status === 401 || error.response.data?.message === '未登录') {
      ElMessage.error('登录已失效，请重新登录')
      redirectToLogin()
    } else if (error.response.status >= 500) {
      ElMessage.error('服务器内部错误，请稍后重试')
    } else if (error.response.status === 403) {
      ElMessage.error('没有权限访问该资源')
    } else if (error.response.status === 404) {
      ElMessage.error('请求的资源不存在')
    } else {
      ElMessage.error(error.response.data?.message || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default service
