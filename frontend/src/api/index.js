import axios from 'axios'

// 从环境变量读取后端 API 地址，默认为空（使用相对路径）
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
    baseURL: API_BASE,
    timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }

        // 自动添加 class_id 参数（如果已选择班级）
        const classId = localStorage.getItem('currentClassId')
        if (classId) {
            config.params = config.params || {}
            if (!config.params.class_id) {
                config.params.class_id = classId
            }
        }

        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
api.interceptors.response.use(
    (response) => response.data,
    (error) => {
        // 登录请求失败不刷新页面
        const isLoginRequest = error.config?.url?.includes('/auth/login')

        if (error.response?.status === 401 && !isLoginRequest) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            localStorage.removeItem('currentClassId')
            localStorage.removeItem('currentClassName')
            window.location.href = '/login'
        }
        return Promise.reject(error.response?.data || error)
    }
)

export default api
