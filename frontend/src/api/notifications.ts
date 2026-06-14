import { apiClient } from './client'

export interface NotificationItem {
  id: number
  notification_type: string
  notification_type_display: string
  title: string
  content: string
  target_type: string | null
  target_object_id: number | null
  target_url: string | null
  is_read: boolean
  read_at: string | null
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function fetchNotifications(params?: { unread?: boolean; page?: number }): Promise<PaginatedResponse<NotificationItem>> {
  const resp = await apiClient.get<PaginatedResponse<NotificationItem>>('/v1/notifications/', {
    params: { ...params, unread: params?.unread ? 'true' : undefined },
  })
  return resp.data
}

export async function fetchUnreadNotificationCount(): Promise<number> {
  const resp = await apiClient.get<{ unread_count: number }>('/v1/notifications/unread-count/')
  return resp.data.unread_count
}

export async function markNotificationRead(id: number): Promise<NotificationItem> {
  const resp = await apiClient.post<NotificationItem>(`/v1/notifications/${id}/read/`)
  return resp.data
}

export async function markAllNotificationsRead(): Promise<{ updated: number }> {
  const resp = await apiClient.post<{ updated: number }>('/v1/notifications/read-all/')
  return resp.data
}
