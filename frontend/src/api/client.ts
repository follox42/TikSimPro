import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Video {
  id: number
  created_at: string
  generator_name: string
  generator_params: Record<string, unknown>
  audio_mode: string | null
  video_path: string | null
  validation_score: number | null
  platform: string | null
  platform_video_id: string | null
  duration: number | null
  fps: number | null
}

export interface Metric {
  id: number
  video_id: number
  platform: string
  scraped_at: string
  views: number
  likes: number
  comments: number
  shares: number
  engagement_rate: number | null
}

export interface Conversation {
  id: number
  created_at: string
  user_message: string
  assistant_message: string
  actions_taken: unknown[]
}

export interface PipelineStatus {
  running: boolean
  last_video_id: number | null
  last_error: string | null
  videos_today: number
  total_videos: number
}

export interface MetricsSummary {
  total_views: number
  total_likes: number
  total_comments: number
  total_shares: number
  average_engagement_rate: number
  best_video_id: number | null
  best_video_views: number
}

// API Functions
export const videosApi = {
  list: (params?: { limit?: number; offset?: number; generator?: string }) =>
    api.get<Video[]>('/api/videos', { params }),

  get: (id: number) => api.get<Video>(`/api/videos/${id}`),

  getMetrics: (id: number) => api.get<Metric[]>(`/api/videos/${id}/metrics`),

  getStats: () => api.get('/api/videos/stats'),

  delete: (id: number) => api.delete(`/api/videos/${id}`),
}

export const metricsApi = {
  summary: () => api.get<MetricsSummary>('/api/metrics/summary'),

  tiktok: (days?: number) =>
    api.get('/api/metrics/tiktok', { params: { days } }),

  youtube: (days?: number) =>
    api.get('/api/metrics/youtube', { params: { days } }),

  performance: () => api.get('/api/metrics/performance'),

  timeline: (days?: number) =>
    api.get('/api/metrics/timeline', { params: { days } }),

  bestPerformers: (limit?: number) =>
    api.get('/api/metrics/best-performers', { params: { limit } }),
}

export const pipelineApi = {
  status: () => api.get<PipelineStatus>('/api/pipeline/status'),

  start: () => api.post('/api/pipeline/start'),

  stop: () => api.post('/api/pipeline/stop'),

  generate: () => api.post('/api/pipeline/generate'),

  getConfig: () => api.get('/api/pipeline/config'),

  updateConfig: (config: Record<string, unknown>) =>
    api.put('/api/pipeline/config', config),
}

export const claudeApi = {
  chat: (message: string) =>
    api.post<Conversation>('/api/claude/chat', { message }),

  history: (limit?: number) =>
    api.get<Conversation[]>('/api/claude/history', { params: { limit } }),

  analysis: () => api.get('/api/claude/analysis'),

  suggestions: () => api.get('/api/claude/suggestions'),

  context: () => api.get('/api/claude/context'),

  clearHistory: () => api.delete('/api/claude/history'),

  executeAction: (action: Record<string, unknown>) =>
    api.post('/api/claude/action', action),
}
