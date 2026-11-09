import client from './client';
import type {
  TokenResponse, User, VideoIdea, Video, VideoJob, Character,
  DashboardStats, YouTubeChannel, PaginatedResponse
} from '@/types';

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    client.post<TokenResponse>('/auth/login', { email, password }).then(r => r.data),
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    client.post<User>('/auth/register', data).then(r => r.data),
  me: () => client.get<User>('/auth/me').then(r => r.data),
  changePassword: (current: string, next: string) =>
    client.put('/auth/change-password', { current_password: current, new_password: next }).then(r => r.data),
};

// ── Research / Ideas ──────────────────────────────────────────────────────────
export const researchApi = {
  generateIdeas: (params: { count?: number; categories?: string[]; keywords?: string[] }) =>
    client.post<VideoIdea[]>('/research/generate-ideas', params).then(r => r.data),
  listIdeas: (page = 1, pageSize = 20, status?: string) =>
    client.get<PaginatedResponse<VideoIdea>>('/research/ideas', { params: { page, page_size: pageSize, status } }).then(r => r.data),
  getIdea: (id: number) => client.get<VideoIdea>(`/research/ideas/${id}`).then(r => r.data),
  approveIdea: (id: number) => client.post<VideoIdea>(`/research/ideas/${id}/approve`).then(r => r.data),
  rejectIdea: (id: number, reason: string) =>
    client.post<VideoIdea>(`/research/ideas/${id}/reject`, null, { params: { reason } }).then(r => r.data),
  deleteIdea: (id: number) => client.delete(`/research/ideas/${id}`),
};

// ── Videos ────────────────────────────────────────────────────────────────────
export const videosApi = {
  listVideos: (page = 1, pageSize = 20, status?: string) =>
    client.get<PaginatedResponse<Video>>('/videos', { params: { page, page_size: pageSize, status } }).then(r => r.data),
  getVideo: (id: number) => client.get<Video>(`/videos/${id}`).then(r => r.data),
  startProduction: (ideaId: number, format = 'landscape', madeForKids = true) =>
    client.post<VideoJob>('/videos/start-production', { idea_id: ideaId, format, made_for_kids: madeForKids }).then(r => r.data),
  approveVideo: (id: number) => client.post<Video>(`/videos/${id}/approve`).then(r => r.data),
  rejectVideo: (id: number, reason: string) =>
    client.post<Video>(`/videos/${id}/reject`, null, { params: { reason } }).then(r => r.data),
  getJobs: (videoId: number) => client.get<VideoJob[]>(`/videos/${videoId}/jobs`).then(r => r.data),
};

// ── Characters ────────────────────────────────────────────────────────────────
export const charactersApi = {
  listCharacters: () => client.get<Character[]>('/characters').then(r => r.data),
  getCharacter: (id: number) => client.get<Character>(`/characters/${id}`).then(r => r.data),
  createCharacter: (data: Partial<Character>) => client.post<Character>('/characters', data).then(r => r.data),
  generateImage: (id: number) => client.post<Character>(`/characters/${id}/generate-image`).then(r => r.data),
  deleteCharacter: (id: number) => client.delete(`/characters/${id}`),
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  getDashboardStats: () => client.get<DashboardStats>('/analytics/dashboard').then(r => r.data),
  getStatusBreakdown: () =>
    client.get<{ status: string; count: number }[]>('/analytics/video-status-breakdown').then(r => r.data),
  getCostByCategory: () =>
    client.get<{ category: string; total_usd: number }[]>('/analytics/cost-by-category').then(r => r.data),
  getRecentVideos: () => client.get<Video[]>('/analytics/recent-videos').then(r => r.data),
};

// ── YouTube ───────────────────────────────────────────────────────────────────
export const youtubeApi = {
  getAuthUrl: () => client.get<{ auth_url: string }>('/youtube/auth-url').then(r => r.data),
  listChannels: () => client.get<YouTubeChannel[]>('/youtube/channels').then(r => r.data),
  listUploads: () => client.get('/youtube/uploads').then(r => r.data),
  scheduleUpload: (data: object) => client.post('/youtube/uploads', data).then(r => r.data),
};

// ── Settings ──────────────────────────────────────────────────────────────────
export const settingsApi = {
  getConfig: () => client.get('/settings/config').then(r => r.data),
  getCostLimits: () => client.get('/settings/cost-limits').then(r => r.data),
  createCostLimit: (data: object) => client.post('/settings/cost-limits', data).then(r => r.data),
};
