const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const REQUEST_TIMEOUT_MS = 10_000

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest(path, options = {}) {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  const requestSignal = options.signal
  const abortRequest = () => controller.abort(requestSignal?.reason)
  requestSignal?.addEventListener('abort', abortRequest, { once: true })
  const requestUrl = new URL(path, API_BASE_URL)

  try {
    const response = await fetch(requestUrl, {
      ...options,
      signal: controller.signal,
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })

    if (!response.ok) {
      let payload
      try {
        payload = await response.json()
      } catch (error) {
        if (!(error instanceof SyntaxError)) throw error
        payload = null
      }
      const detail = typeof payload?.detail === 'string'
        ? payload.detail
        : Array.isArray(payload?.detail)
          ? payload.detail.map((item) => item.msg).join('; ')
          : ''
      const routeNotFound = response.status === 404 && (!detail || /^(?:detail\s+)?not found\.?$/i.test(detail.trim()))
      const fallback = routeNotFound
        ? `API route not found: ${options.method || 'GET'} ${requestUrl.pathname} at ${requestUrl.origin}. Check VITE_API_BASE_URL and restart the backend.`
        : `API request failed (${response.status} ${response.statusText})`
      throw new ApiError(routeNotFound ? fallback : detail || fallback, response.status)
    }

    return response.status === 204 ? null : response.json()
  } catch (error) {
    if (controller.signal.aborted && !requestSignal?.aborted) {
      throw new ApiError('The API request timed out. Check that the backend is running, then retry.', 0)
    }
    if (error instanceof ApiError) throw error
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('The API request was cancelled.', 0)
    }
    if (error instanceof TypeError) {
      throw new ApiError('Could not reach the ASCEND API. Check the backend and VITE_API_BASE_URL, then retry.', 0)
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
    requestSignal?.removeEventListener('abort', abortRequest)
  }
}

export function signup(payload) {
  return apiRequest('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function login(payload) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getCurrentUser() {
  return apiRequest('/auth/me')
}

export function logout() {
  return apiRequest('/auth/logout', { method: 'POST' })
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

export function updateGoal(goalId, changes, options = {}) {
  return apiRequest(`/goals/${encodeURIComponent(goalId)}`, {
    ...options,
    method: 'PATCH',
    body: JSON.stringify(changes),
  })
}

export function deleteGoal(goalId, options = {}) {
  return apiRequest(`/goals/${encodeURIComponent(goalId)}`, {
    ...options,
    method: 'DELETE',
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

export function deleteTask(taskId, options = {}) {
  return apiRequest(`/tasks/${encodeURIComponent(taskId)}`, {
    ...options,
    method: 'DELETE',
  })
}

export function getContributions(options) {
  return apiRequest('/contributions', options)
}

export function createContribution(contribution, options = {}) {
  return apiRequest('/contributions', {
    ...options,
    method: 'POST',
    body: JSON.stringify(contribution),
  })
}
