import { apiClient } from './client'

export type ReportTargetType = 'post' | 'comment' | 'photo' | 'photo_comment' | 'activity' | 'birthday_wish'

export interface ReportPayload {
  target_type: ReportTargetType
  object_id: number
  reason: string
  description: string
}

export interface ReportItem {
  id: number
  reporter_name: string
  target_type: string
  object_id: number
  target_label: string
  reason: string
  reason_display: string
  description: string
  status: string
  status_display: string
  handled_by_name: string | null
  handled_at: string | null
  handle_note: string
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export const REPORT_REASONS = [
  { value: 'privacy', label: '涉及隐私' },
  { value: 'false_info', label: '内容不实' },
  { value: 'abuse', label: '攻击辱骂' },
  { value: 'ad', label: '广告推广' },
  { value: 'fraud', label: '诈骗或诱导转账' },
  { value: 'illegal', label: '违法违规' },
  { value: 'copyright', label: '侵犯肖像权或著作权' },
  { value: 'other', label: '其他原因' },
]

export const MODERATION_ACTIONS = [
  { value: 'ignore', label: '忽略举报' },
  { value: 'hide_content', label: '隐藏内容' },
  { value: 'delete_content', label: '删除内容' },
  { value: 'request_revision', label: '要求修改' },
  { value: 'warn_user', label: '警告用户' },
  { value: 'restrict_user', label: '限制用户' },
  { value: 'ban_user', label: '封禁用户' },
]

export async function createReport(payload: ReportPayload): Promise<ReportItem> {
  const resp = await apiClient.post<ReportItem>('/v1/reports/', payload)
  return resp.data
}

export async function fetchAdminReports(params?: { status?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<ReportItem>> {
  const resp = await apiClient.get<PaginatedResponse<ReportItem>>('/v1/admin/reports/', { params })
  return resp.data
}

export async function handleReport(id: number, data: { action_type: string; reason: string }): Promise<ReportItem> {
  const resp = await apiClient.post<ReportItem>(`/v1/admin/reports/${id}/handle/`, data)
  return resp.data
}
