import request from './index'

// 提交评委评分
export function submitJudgeScore(scoreData) {
  return request.post('/judge-scores/submit', scoreData)
}

// 获取评委的评分记录
export function getJudgeScores(contestId, judgeId) {
  return request.get('/judge-scores/my-scores', {
    params: {
      contest_id: contestId,
      judge_id: judgeId
    }
  })
}

// 获取辞手的所有评分
export function getDebaterScores(contestId, debaterId) {
  return request.get('/judge-scores/debater-scores', {
    params: {
      contest_id: contestId,
      debater_id: debaterId
    }
  })
}