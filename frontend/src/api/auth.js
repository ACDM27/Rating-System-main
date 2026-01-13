import api from './index'

// ===== 登录 =====
export function login(username, password, loginType = 'teacher') {
    return api.post('/auth/login', { username, password, login_type: loginType })
}

// ===== 选择班级 =====
export function selectClass(classId, userId) {
    return api.post('/auth/select-class', { class_id: classId }, { params: { user_id: userId } })
}
