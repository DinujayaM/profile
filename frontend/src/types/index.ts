// Auth
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  role: 'viewer' | 'editor' | 'admin' | 'superadmin';
  is_active: boolean;
  mfa_enabled: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Video Ideas
export type IdeaStatus = 'pending' | 'approved' | 'rejected' | 'in_production' | 'completed';
export type AgeCategory = '0-2' | '3-5' | '6-8' | '9-12';
export type ContentCategory =
  | 'nursery_rhyme' | 'educational' | 'animal_story' | 'bedtime_story'
  | 'alphabet' | 'numbers' | 'colors' | 'shapes' | 'seasons'
  | 'holiday' | 'adventure' | 'friendship' | 'science' | 'music';

export interface VideoIdea {
  id: number;
  title: string;
  concept: string;
  educational_value?: string;
  age_category: AgeCategory;
  content_category: ContentCategory;
  estimated_duration_minutes: number;
  estimated_cost_usd?: number;
  status: IdeaStatus;
  keywords?: string[];
  created_by_id?: number;
}

// Videos
export type VideoStatus =
  | 'draft' | 'generating' | 'quality_check' | 'pending_approval'
  | 'approved' | 'rejected' | 'uploading' | 'published' | 'failed' | 'archived';
export type VideoFormat = 'landscape' | 'portrait';

export interface Video {
  id: number;
  title: string;
  description?: string;
  tags?: string[];
  thumbnail_url?: string;
  video_url?: string;
  format: VideoFormat;
  duration_seconds?: number;
  width: number;
  height: number;
  status: VideoStatus;
  made_for_kids: boolean;
  total_cost_usd?: number;
  quality_score?: number;
  youtube_video_id?: string;
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'retrying' | 'cancelled';

export interface VideoJob {
  id: number;
  video_id?: number;
  job_type: string;
  step?: string;
  status: JobStatus;
  progress_pct: number;
  error_message?: string;
  retry_count: number;
}

// Characters
export type CharacterType = 'main' | 'supporting' | 'background' | 'narrator';

export interface Character {
  id: number;
  name: string;
  character_type: CharacterType;
  description: string;
  personality?: string;
  appearance: string;
  reference_image_url?: string;
  is_active: boolean;
  tags?: string[];
}

// Analytics
export interface DashboardStats {
  total_videos: number;
  pending_approval: number;
  published_videos: number;
  failed_jobs: number;
  scheduled_uploads: number;
  total_youtube_views?: number;
  subscriber_count?: number;
  total_cost_usd: number;
  daily_cost_usd: number;
  monthly_cost_usd: number;
}

// YouTube
export interface YouTubeChannel {
  id: number;
  channel_id: string;
  channel_name?: string;
  channel_url?: string;
  subscriber_count?: number;
  total_views?: number;
  video_count?: number;
  quota_used_today: number;
  daily_quota_limit: number;
  is_active: boolean;
}

export type UploadStatus = 'pending' | 'uploading' | 'processing' | 'published' | 'failed' | 'removed';

export interface YouTubeUpload {
  id: number;
  video_id: number;
  youtube_video_id?: string;
  upload_status: UploadStatus;
  upload_progress_pct: number;
  error_message?: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
