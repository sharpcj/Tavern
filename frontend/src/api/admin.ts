import { apiClient } from './client'

export interface AdminUser {
  id: number
  account_id: string
  email: string
  real_name: string
  high_school: string
  high_school_class: string
  nickname: string
  role: string
  role_display: string
  review_status: string
  review_status_display: string
  account_status: string
  account_status_display: string
  review_note: string
  review_message: string
  reviewed_by: number | null
  reviewed_at: string | null
  date_joined: string
}

export interface AdminContentItem {
  id: number
  author_name?: string
  uploader_name?: string
  creator_name?: string
  content?: string
  caption?: string
  title?: string
  album_title?: string
  status: string
  created_at: string
}

export interface AdminActivityItem {
  id: number
  title: string
  activity_type: string
  initiator_name: string
  status: string
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function fetchAdminUsers(params?: { status?: string; role?: string; page?: number }): Promise<PaginatedResponse<AdminUser>> {
  const resp = await apiClient.get<PaginatedResponse<AdminUser>>('/v1/admin/users/', { params })
  return resp.data
}

export async function updateAdminUser(accountId: string, data: { role?: string; account_status?: string }): Promise<AdminUser> {
  const resp = await apiClient.patch<AdminUser>(`/v1/admin/users/${accountId}/`, data)
  return resp.data
}

export async function fetchPendingReviews(): Promise<PaginatedResponse<AdminUser>> {
  const resp = await apiClient.get<PaginatedResponse<AdminUser>>('/v1/admin/users/review/')
  return resp.data
}

export async function reviewUser(accountId: string, data: { action: string; reason?: string }): Promise<AdminUser> {
  const resp = await apiClient.post<AdminUser>(`/v1/admin/users/${accountId}/review-action/`, data)
  return resp.data
}

export async function fetchAdminPosts(params?: { status?: string; page?: number }): Promise<PaginatedResponse<AdminContentItem>> {
  const resp = await apiClient.get<PaginatedResponse<AdminContentItem>>('/v1/admin/contents/posts/', { params })
  return resp.data
}

export async function hidePost(id: number): Promise<void> {
  await apiClient.post(`/v1/admin/contents/posts/${id}/hide/`)
}

export async function deletePost(id: number): Promise<void> {
  await apiClient.post(`/v1/admin/contents/posts/${id}/delete/`)
}

export async function fetchAdminComments(params?: { page?: number }): Promise<PaginatedResponse<AdminContentItem>> {
  const resp = await apiClient.get<PaginatedResponse<AdminContentItem>>('/v1/admin/contents/comments/', { params })
  return resp.data
}

export async function hideComment(id: number): Promise<void> {
  await apiClient.post(`/v1/admin/contents/comments/${id}/hide/`)
}

export async function deleteComment(id: number): Promise<void> {
  await apiClient.post(`/v1/admin/contents/comments/${id}/delete/`)
}

export async function fetchAdminPhotos(params?: { page?: number }): Promise<PaginatedResponse<AdminContentItem>> {
  const resp = await apiClient.get<PaginatedResponse<AdminContentItem>>('/v1/admin/contents/photos/', { params })
  return resp.data
}

export async function hidePhoto(id: number): Promise<void> {
  await apiClient.post(`/v1/admin/contents/photos/${id}/hide/`)
}

export async function fetchAdminAlbums(params?: { page?: number }): Promise<PaginatedResponse<AdminContentItem>> {
  const resp = await apiClient.get<PaginatedResponse<AdminContentItem>>('/v1/admin/contents/albums/', { params })
  return resp.data
}

export async function hideAlbum(id: number): Promise<void> {
  await apiClient.post(`/v1/admin/contents/albums/${id}/hide/`)
}

export async function fetchAdminActivities(params?: { status?: string; page?: number }): Promise<PaginatedResponse<AdminActivityItem>> {
  const resp = await apiClient.get<PaginatedResponse<AdminActivityItem>>('/v1/admin/activities/', { params })
  return resp.data
}

export async function updateActivityStatus(id: number, status: string): Promise<void> {
  await apiClient.post(`/v1/admin/activities/${id}/update-status/`, { status })
}

export async function deleteActivity(id: number, reason: string): Promise<void> {
  await apiClient.post(`/v1/admin/activities/${id}/delete/`, { reason })
}
