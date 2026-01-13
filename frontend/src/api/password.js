import api from './index'

// 修改密码
export function changePassword(userId, oldPassword, newPassword) {
    return api.post('/auth/change-password', null, {
        params: {
            user_id: userId,
            old_password: oldPassword,
            new_password: newPassword
        }
    })
}
