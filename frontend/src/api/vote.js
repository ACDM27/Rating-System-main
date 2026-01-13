import request from './index'

// 提交投票
export function submitVote(voteData) {
  return request.post('/vote/submit', voteData)
}

// 获取我的投票记录
export function getMyVotes(contestId) {
  return request.get(`/vote/my-votes/${contestId}`)
}

// 获取投票统计（管理员用）
export function getVoteStatistics(contestId) {
  return request.get(`/vote/stats/${contestId}`)
}
