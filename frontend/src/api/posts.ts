import { apiClient } from './client'

export interface PostListItem {
  id: number
  display_name: string
  content: string
  images: string[]
  category: string
  category_display: string
  is_pinned: boolean
  comment_count: number
  created_at: string
  updated_at: string
}

export interface PostDetail {
  id: number
  author_id: string
  author_real_name: string
  display_name: string
  content: string
  images: string[]
  category: string
  category_display: string
  display_mode: string
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface PostCreatePayload {
  content: string
  images?: string[]
  category: string
  display_mode: 'real_name' | 'nickname'
}

export interface CommentItem {
  id: number
  author_id: string
  author_real_name: string
  display_name: string
  content: string
  display_mode: string
  parent: number | null
  replies: CommentReply[]
  created_at: string
}

export interface CommentReply {
  id: number
  author_id: string
  author_real_name: string
  display_name: string
  content: string
  display_mode: string
  created_at: string
}

export interface CommentCreatePayload {
  content: string
  display_mode: 'real_name' | 'nickname'
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const CATEGORY_LABELS: Record<string, string> = {
  life: '生活近况',
  old_photos: '老照片',
  reunion: '同学聚会',
  teacher: '老师相关',
  work_city: '工作与城市',
  family: '家庭与成长',
  help: '求助与互助',
  chat: '闲聊',
}

export const POST_CATEGORIES = Object.entries(CATEGORY_LABELS).map(([value, label]) => ({ value, label }))

export async function fetchPosts(params?: {
  category?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<PostListItem>> {
  const resp = await apiClient.get<PaginatedResponse<PostListItem>>('/v1/posts/', { params })
  return resp.data
}

export async function fetchPostDetail(id: number): Promise<PostDetail> {
  const resp = await apiClient.get<PostDetail>(`/v1/posts/${id}/`)
  return resp.data
}

export async function createPost(data: PostCreatePayload): Promise<PostDetail> {
  const resp = await apiClient.post<PostDetail>('/v1/posts/', data)
  return resp.data
}

export async function updatePost(id: number, data: Partial<PostCreatePayload>): Promise<PostDetail> {
  const resp = await apiClient.patch<PostDetail>(`/v1/posts/${id}/`, data)
  return resp.data
}

export async function deletePost(id: number): Promise<void> {
  await apiClient.delete(`/v1/posts/${id}/`)
}

export async function fetchComments(postId: number): Promise<CommentItem[]> {
  const resp = await apiClient.get<PaginatedResponse<CommentItem>>(`/v1/posts/${postId}/comments/`)
  return resp.data.results
}

export async function createComment(postId: number, data: CommentCreatePayload): Promise<CommentItem> {
  const resp = await apiClient.post<CommentItem>(`/v1/posts/${postId}/comments/`, data)
  return resp.data
}

export async function replyToComment(commentId: number, data: CommentCreatePayload): Promise<CommentItem> {
  const resp = await apiClient.post<CommentItem>(`/v1/comments/${commentId}/replies/`, data)
  return resp.data
}

export async function deleteComment(commentId: number): Promise<void> {
  await apiClient.delete(`/v1/comments/${commentId}/`)
}
