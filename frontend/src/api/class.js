import api from './index'

// 获取工作区的所有班级
export function getClasses(workspaceId = 1) {
    return api.get('/auth/classes', { params: { workspace_id: workspaceId } })
}
