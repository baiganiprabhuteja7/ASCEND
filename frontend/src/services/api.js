const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function apiRequest(path, options = {}) {
  const response = await fetch(new URL(path, API_BASE_URL), {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const payload = await response.json()
    const detail = typeof payload.detail === 'string'
      ? payload.detail
      : Array.isArray(payload.detail)
        ? payload.detail.map((item) => item.msg).join('; ')
        : ''
    throw new Error(detail || `API request failed (${response.status} ${response.statusText})`)
  }

  return response.status === 204 ? null : response.json()
}

export function getGoals(options) {
  return apiRequest('/goals', options)
}

export function getGoalPlan(goalId, options) {
  return apiRequest(`/goals/${encodeURIComponent(goalId)}/plan`, options)
}

export function generateGoalPlan(goalId, force = false, options = {}) {
  return apiRequest(`/goals/${encodeURIComponent(goalId)}/plan`, {
    ...options,
    method: 'POST',
    body: JSON.stringify({ force }),
  })
}

export function getProgress(options) {
  return apiRequest('/progress', options)
}

export function createGoal(goal, options = {}) {
  return apiRequest('/goals', {
    ...options,
    method: 'POST',
    body: JSON.stringify(goal),
  })
}

export function getTasks(goalId, options) {
  const query = goalId ? `?goal_id=${encodeURIComponent(goalId)}` : ''
  return apiRequest(`/tasks${query}`, options)
}

export function createTask(task, options = {}) {
  return apiRequest('/tasks', {
    ...options,
    method: 'POST',
    body: JSON.stringify(task),
  })
}

export function updateTask(taskId, changes, options = {}) {
  return apiRequest(`/tasks/${encodeURIComponent(taskId)}`, {
    ...options,
    method: 'PATCH',
    body: JSON.stringify(changes),
  })
}
