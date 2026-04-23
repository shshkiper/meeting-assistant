import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60_000,
})

// Inject JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),
  register: (data: { email: string; full_name: string; password: string }) =>
    api.post('/auth/register', data).then((r) => r.data),
  me: () => api.get('/users/me').then((r) => r.data),
}

// ── Meetings ──────────────────────────────────────────────────────────────────
export const meetingsApi = {
  list: () => api.get('/meetings/').then((r) => r.data),
  get: (id: string) => api.get(`/meetings/${id}`).then((r) => r.data),
  upload: (formData: FormData) =>
    api.post('/meetings/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600_000,
    }).then((r) => r.data),
  delete: (id: string) => api.delete(`/meetings/${id}`),
}

// ── Transcripts ───────────────────────────────────────────────────────────────
export const transcriptApi = {
  get: (meetingId: string) =>
    api.get(`/transcriptions/${meetingId}`).then((r) => r.data),
  getParticipants: (meetingId: string) =>
    api.get(`/transcriptions/${meetingId}/participants`).then((r) => r.data),
  updateParticipant: (meetingId: string, participantId: string, data: object) =>
    api.patch(`/transcriptions/${meetingId}/participants/${participantId}`, data).then((r) => r.data),
}

// ── Protocol ──────────────────────────────────────────────────────────────────
export const protocolApi = {
  get: (meetingId: string) =>
    api.get(`/protocols/${meetingId}`).then((r) => r.data),
  update: (meetingId: string, data: object) =>
    api.patch(`/protocols/${meetingId}`, data).then((r) => r.data),
  exportDocx: (meetingId: string) =>
    api.get(`/protocols/${meetingId}/export/docx`, { responseType: 'blob' }).then((r) => r.data),
}

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const tasksApi = {
  list: (meetingId: string) =>
    api.get(`/tasks/${meetingId}`).then((r) => r.data),
  update: (taskId: string, data: object) =>
    api.patch(`/tasks/${taskId}`, data).then((r) => r.data),
  syncJira: (taskId: string) =>
    api.post(`/tasks/${taskId}/sync-jira`).then((r) => r.data),
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: () => api.get('/analytics/dashboard').then((r) => r.data),
  sentiment: (meetingId: string) =>
    api.get(`/analytics/${meetingId}/sentiment`).then((r) => r.data),
  keywords: (meetingId: string) =>
    api.get(`/analytics/${meetingId}/keywords`).then((r) => r.data),
  contacts: (meetingId: string) =>
    api.get(`/analytics/${meetingId}/contacts`).then((r) => r.data),
}
