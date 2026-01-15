import api from './index'

// ===== 用户管理 (通用) =====
export function deleteUser(userId) {
    return api.delete(`/admin/users/${userId}`)
}

// ===== 观众管理 =====
export function getStudents(classId) {
    return api.get('/admin/students', { params: { class_id: classId } })
}

export function createStudent(data) {
    return api.post('/admin/students', data)
}

export function importStudents(data) {
    return api.post('/admin/students/import', data)
}

// ===== 评委管理 =====
export function getTeachers(classId) {
    return api.get('/admin/teachers', { params: { class_id: classId } })
}

export function createTeacher(data) {
    return api.post('/admin/teachers', data)
}

export function importTeachers(data) {
    return api.post('/admin/teachers/import', data)
}

export function addTeacherToClass(classId, teacherId) {
    return api.post(`/admin/teachers/add`, null, { params: { class_id: classId, teacher_id: teacherId } })
}

export function removeTeacherFromClass(classId, teacherId) {
    return api.delete(`/admin/teachers/${teacherId}`, { params: { class_id: classId } })
}

// ===== 团队和选项 =====
export function getTeams(classId) {
    return api.get('/admin/teams', { params: { class_id: classId } })
}

// ===== 系统状态 =====
export function getSystemState(classId) {
    return api.get('/admin/state', { params: { class_id: classId } })
}

export function setStage(stage, teamId, classId) {
    const data = { stage }
    if (teamId) {
        data.target_team_id = teamId
    }
    return api.post('/admin/stage/set', data, { params: { class_id: classId } })
}

export function getProgress(classId) {
    return api.get('/admin/progress', { params: { class_id: classId } })
}

export function resetSystem(classId) {
    return api.post('/admin/reset-system', {}, { params: { class_id: classId } })
}

export function updateUserDebateRole(userId, teamSide, debaterPosition) {
    return api.put(`/admin/users/${userId}/debate-role`, null, {
        params: {
            team_side: teamSide,
            debater_position: debaterPosition
        }
    })
}
