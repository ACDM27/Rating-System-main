import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '../api/auth'
import { selectClass as selectClassApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(null)
    const user = ref(null)
    const currentClassId = ref(null)
    const currentClassName = ref(null)
    const availableClasses = ref([])
    const needSelectClass = ref(false)
    const needChangePassword = ref(false)
    const needSetTopic = ref(false)

    const isLoggedIn = computed(() => !!token.value)
    const hasSelectedClass = computed(() => currentClassId.value !== null)

    async function login(username, password, loginType = 'teacher') {
        const response = await loginApi(username, password, loginType)
        token.value = response.access_token
        user.value = response.user
        availableClasses.value = response.available_classes || []
        needSelectClass.value = response.need_select_class
        needChangePassword.value = response.need_change_password || false
        needSetTopic.value = response.need_set_topic || false

        // 保存到 localStorage
        localStorage.setItem('token', response.access_token)
        localStorage.setItem('user', JSON.stringify(response.user))
        localStorage.setItem('availableClasses', JSON.stringify(response.available_classes || []))
        localStorage.setItem('needSelectClass', String(response.need_select_class))
        localStorage.setItem('needChangePassword', String(response.need_change_password || false))
        localStorage.setItem('needSetTopic', String(response.need_set_topic || false))

        // 学生自动设置班级
        if (user.value.role === 'student' && response.available_classes.length > 0) {
            currentClassId.value = response.available_classes[0].id
            currentClassName.value = response.available_classes[0].name
            localStorage.setItem('currentClassId', String(currentClassId.value))
            localStorage.setItem('currentClassName', currentClassName.value)
        }

        return response.user
    }

    async function selectClass(classId) {
        const response = await selectClassApi(classId, user.value.id)
        token.value = response.access_token
        currentClassId.value = response.class_id
        currentClassName.value = response.class_name

        // 更新 localStorage
        localStorage.setItem('token', response.access_token)
        localStorage.setItem('currentClassId', String(response.class_id))
        localStorage.setItem('currentClassName', response.class_name)

        return response
    }

    function switchClass(classId, className) {
        // 切换班级（不重新获取 token，仅更新状态）
        currentClassId.value = classId
        currentClassName.value = className
        localStorage.setItem('currentClassId', String(classId))
        localStorage.setItem('currentClassName', className)
    }

    function logout() {
        token.value = null
        user.value = null
        currentClassId.value = null
        currentClassName.value = null
        availableClasses.value = []
        needSelectClass.value = false
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('currentClassId')
        localStorage.removeItem('currentClassName')
        localStorage.removeItem('availableClasses')
        localStorage.removeItem('needSelectClass')
        localStorage.removeItem('needChangePassword')
    }

    function restoreSession() {
        const savedToken = localStorage.getItem('token')
        const savedUser = localStorage.getItem('user')
        const savedClassId = localStorage.getItem('currentClassId')
        const savedClassName = localStorage.getItem('currentClassName')
        const savedAvailableClasses = localStorage.getItem('availableClasses')
        const savedNeedSelectClass = localStorage.getItem('needSelectClass')

        if (savedToken && savedUser) {
            token.value = savedToken
            user.value = JSON.parse(savedUser)
        }
        if (savedClassId) {
            currentClassId.value = parseInt(savedClassId)
        }
        if (savedClassName) {
            currentClassName.value = savedClassName
        }
        if (savedAvailableClasses) {
            availableClasses.value = JSON.parse(savedAvailableClasses)
        }
        if (savedNeedSelectClass) {
            needSelectClass.value = savedNeedSelectClass === 'true'
        }
        const savedNeedChangePassword = localStorage.getItem('needChangePassword')
        if (savedNeedChangePassword) {
            needChangePassword.value = savedNeedChangePassword === 'true'
        }
        const savedNeedSetTopic = localStorage.getItem('needSetTopic')
        if (savedNeedSetTopic) {
            needSetTopic.value = savedNeedSetTopic === 'true'
        }
    }

    return {
        token,
        user,
        currentClassId,
        currentClassName,
        availableClasses,
        needSelectClass,
        isLoggedIn,
        hasSelectedClass,
        login,
        selectClass,
        switchClass,
        logout,
        restoreSession,
        needChangePassword,
        needSetTopic
    }
})
