import { apiClient } from './client'

export interface ProfileData {
  real_name: string
  nickname: string
  email: string
  avatar_url: string
  avatar_visible: boolean
  city: string
  occupation: string
  bio: string
  birthday_month: number | null
  show_birthday: boolean
  phone: string
  phone_visibility: 'everyone' | 'selected' | 'only_me'
  wechat: string
  wechat_visibility: 'everyone' | 'selected' | 'only_me'
  email_visibility: 'everyone' | 'selected' | 'only_me'
  contact_visible_to: string[]
  created_at: string
  updated_at: string
}

export interface ClassmateListItem {
  account_id: string
  real_name: string
  nickname: string
  avatar_url: string
  city: string
  occupation: string
  bio: string
  birthday_month: number | null
}

export interface ClassmateDetail extends ClassmateListItem {
  email: string | null
  phone: string | null
  wechat: string | null
}

export type ProfileUpdatePayload = Partial<ProfileData> & {
  avatar?: File | null
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function fetchMyProfile(): Promise<ProfileData> {
  const resp = await apiClient.get<ProfileData>('/v1/me/profile/')
  return resp.data
}

export async function updateMyProfile(data: ProfileUpdatePayload): Promise<ProfileData> {
  if (data.avatar) {
    const formData = new FormData()
    Object.entries(data).forEach(([key, value]) => {
      if (value === undefined || value === null) return
      if (key === 'avatar') {
        formData.append('avatar', value as File)
        return
      }
      if (Array.isArray(value)) {
        value.forEach(item => formData.append(key, String(item)))
        return
      }
      formData.append(key, String(value))
    })
    const resp = await apiClient.patch<ProfileData>('/v1/me/profile/', formData)
    return resp.data
  }
  const resp = await apiClient.patch<ProfileData>('/v1/me/profile/', data)
  return resp.data
}

export async function fetchClassmates(params?: {
  search?: string
  city?: string
  occupation?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<ClassmateListItem>> {
  const resp = await apiClient.get<PaginatedResponse<ClassmateListItem>>('/v1/classmates/', { params })
  return resp.data
}

export async function fetchClassmateDetail(accountId: string): Promise<ClassmateDetail> {
  const resp = await apiClient.get<ClassmateDetail>(`/v1/classmates/${accountId}/`)
  return resp.data
}
