import axios from 'axios'

const service = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    // baseURL: 'http://172.12.0.230:8000',
    timeout: 5000
})

// 请求拦截器：每次请求自动加 token
service.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
}, error => {
    return Promise.reject(error)
})

// 响应拦截器：token失效时提示并跳转登录
service.interceptors.response.use(
    response => {
        // 这里假设后端返回的未登录/掉线状态码为401或自定义code
        if (response.data && (
            // response.data.code === 401 ||
            response.data.code === 66 || // gcode.CodeInvalidRequest.Code() 可能为 1001
            response.data.message === '未登录' ||
            response.data.message === 'token已失效' ||
            response.data.message === '未登录或登录过期，请重新登陆'
        )) {
            // 弹窗提示
            if (window.ElMessage) {
                window.ElMessage.error('登录已失效，请重新登录')
            } else {
                alert('登录已失效，请重新登录')
            }
            localStorage.removeItem('userId');
            localStorage.removeItem('userType');
            localStorage.removeItem('token');
            setTimeout(() => {
                window.location.href = '/login';
            }, 500)
            return Promise.reject(new Error('登录已失效'))
        }
        return response
    },
    error => {
        // 处理401等错误码
        if (error.response && (error.response.status === 401 || error.response.data?.message === '未登录')) {
            if (window.ElMessage) {
                window.ElMessage.error('登录已失效，请重新登录')
            } else {
                alert('登录已失效，请重新登录')
            }
            localStorage.removeItem('userId');
            localStorage.removeItem('userType');
            localStorage.removeItem('token');
            setTimeout(() => {
                window.location.href = '/login';
            }, 500)
        }
        return Promise.reject(error)
    }
)

export default service