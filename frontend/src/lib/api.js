import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authApi = {
  login: (data) => api.post('/auth/login', data).then(res => res.data),
  register: (data) => api.post('/auth/register', data).then(res => res.data),
}

export const userApi = {
  list: () => api.get('/users/').then(res => res.data),
  get: (id) => api.get(`/users/${id}`).then(res => res.data),
  create: (data) => api.post('/users/', data).then(res => res.data),
}

/**
 * 解析 SSE chunk 为 { event, data } 对象
 */
function parseSSEChunk(chunk) {
  const lines = chunk.split('\n')
  let event = 'message'
  let data = ''

  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      data = line.slice(5).trim()
    }
  }

  if (!data) return null

  try {
    return { event, data: JSON.parse(data) }
  } catch (e) {
    return { event, data }
  }
}

/**
 * SSE 流式聊天
 * 返回 { stream, controller, [Symbol.asyncIterator] }
 */
function createSSEStream(url, body) {
  const controller = new AbortController()

  const streamPromise = fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  }).then(response => {
    if (!response.ok) throw new Error('SSE 连接失败')
    return response.body
  })

  return {
    controller,
    async *[Symbol.asyncIterator]() {
      const body = await streamPromise
      const reader = body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // SSE 以 \n\n 分隔事件
          const chunks = buffer.split('\n\n')
          buffer = chunks.pop() || ''

          for (const chunk of chunks) {
            const event = parseSSEChunk(chunk)
            if (event) yield event
          }
        }
      } finally {
        reader.releaseLock()
      }
    }
  }
}

export const aiApi = {
  chat: (message, userId, sessionId) => api.post('/ai/chat', { message, user_id: userId, session_id: sessionId }).then(res => res.data),
  chatStream: (message, userId, sessionId) => {
    return createSSEStream('/api/ai/chat/stream', { message, user_id: userId, session_id: sessionId })
  },
  listSessions: (userId) => api.get('/ai/sessions', { params: { user_id: userId } }).then(res => res.data),
  createSession: (userId) => api.post('/ai/sessions', null, { params: { user_id: userId } }).then(res => res.data),
  deleteSession: (sessionId) => api.delete(`/ai/sessions/${sessionId}`).then(res => res.data),
  getMessages: (sessionId) => api.get(`/ai/sessions/${sessionId}/messages`).then(res => res.data),
}

export const taskApi = {
  list: (userId) => api.get('/tasks/', { params: { user_id: userId } }).then(res => res.data),
  get: (id) => api.get(`/tasks/${id}`).then(res => res.data),
  create: (data) => api.post('/tasks/', data).then(res => res.data),
  update: (id, data) => api.patch(`/tasks/${id}`, data).then(res => res.data),
  delete: (id) => api.delete(`/tasks/${id}`).then(res => res.data),
  complete: (id) => api.post(`/tasks/${id}/complete`).then(res => res.data),
}

export const planApi = {
  list: (userId) => api.get('/plans/', { params: { user_id: userId } }).then(res => res.data),
  get: (id) => api.get(`/plans/${id}`).then(res => res.data),
  create: (data) => api.post('/plans/', data).then(res => res.data),
  update: (id, data) => api.patch(`/plans/${id}`, data).then(res => res.data),
  delete: (id) => api.delete(`/plans/${id}`).then(res => res.data),
  progress: (id) => api.get(`/plans/${id}/progress`).then(res => res.data),
}

export default api
