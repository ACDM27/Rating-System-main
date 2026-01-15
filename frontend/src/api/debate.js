import request from './index'

// 辩论赛阶段管理
export function setDebateStage(stage, classId, contestId = null) {
  return request.post('/admin/debate/stage', null, {
    params: {
      stage,
      class_id: classId,
      contest_id: contestId
    }
  })
}

// 获取辩论进度（管理员专用）
export function getDebateProgress(classId) {
  return request.get('/admin/debate/progress', {
    params: { class_id: classId }
  })
}

// 揭晓辩论结果
export function revealDebateResults(classId) {
  return request.post('/admin/debate/reveal-results', null, {
    params: { class_id: classId }
  })
}

// 获取辩论结果（不揭晓）
export function getDebateResults(contestId) {
  return request.get(`/admin/debate/results/${contestId}`)
}

// 创建比赛
export function createContest(topic, proTeamName, conTeamName, classId, proTopic, conTopic) {
  return request.post('/admin/debate/contest', null, {
    params: {
      topic,
      pro_team_name: proTeamName,
      con_team_name: conTeamName,
      class_id: classId,
      pro_topic: proTopic,
      con_topic: conTopic
    }
  })
}

// 获取当前比赛（通过 class_id）
export function getCurrentContest(classId) {
  return request.get('/admin/debate/contest', {
    params: { class_id: classId }
  })
}

// 根据比赛ID获取比赛信息
export function getContestById(contestId) {
  return request.get(`/admin/debate/contest/${contestId}`)
}

// 更新用户辩论角色
export function updateUserDebateRole(userId, teamSide = null, debaterPosition = null) {
  const params = {}
  if (teamSide !== null) params.team_side = teamSide
  if (debaterPosition !== null) params.debater_position = debaterPosition

  return request.put(`/admin/users/${userId}/debate-role`, null, { params })
}

// 重置辩论系统
export function resetDebateSystem(classId) {
  return request.post('/admin/debate/reset', null, {
    params: { class_id: classId }
  })
}