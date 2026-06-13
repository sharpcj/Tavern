import { apiClient } from './client'

export interface AnnouncementListItem {
  id: number
  title: string
  publisher_name: string
  is_pinned: boolean
  require_read_confirm: boolean
  expires_at: string | null
  created_at: string
  is_read: boolean
}

export interface AnnouncementDetail extends AnnouncementListItem {
  content: string
  pinned_at: string | null
  status: string
  updated_at: string
}

export interface AnnouncementPayload {
  title: string
  content: string
  is_pinned: boolean
  require_read_confirm: boolean
  expires_at?: string | null
  status: 'published' | 'hidden'
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function fetchAnnouncements(params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<AnnouncementListItem>> {
  const resp = await apiClient.get<PaginatedResponse<AnnouncementListItem>>('/v1/announcements/', { params })
  return resp.data
}

export async function fetchPinnedAnnouncements(): Promise<PaginatedResponse<AnnouncementListItem>> {
  const resp = await apiClient.get<PaginatedResponse<AnnouncementListItem>>('/v1/announcements/pinned/')
  return resp.data
}

export async function fetchAnnouncementDetail(id: number): Promise<AnnouncementDetail> {
  const resp = await apiClient.get<AnnouncementDetail>(`/v1/announcements/${id}/`)
  return resp.data
}

export async function createAnnouncement(data: AnnouncementPayload): Promise<AnnouncementDetail> {
  const resp = await apiClient.post<AnnouncementDetail>('/v1/announcements/', data)
  return resp.data
}

export async function updateAnnouncement(id: number, data: Partial<AnnouncementPayload>): Promise<AnnouncementDetail> {
  const resp = await apiClient.patch<AnnouncementDetail>(`/v1/announcements/${id}/`, data)
  return resp.data
}

export async function deleteAnnouncement(id: number): Promise<void> {
  await apiClient.delete(`/v1/announcements/${id}/`)
}

export async function confirmAnnouncementRead(id: number): Promise<AnnouncementDetail> {
  const resp = await apiClient.post<AnnouncementDetail>(`/v1/announcements/${id}/read-confirm/`)
  return resp.data
}
