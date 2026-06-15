import { apiClient } from './client'

export interface BirthdayClassmate {
  account_id: string
  real_name: string
  nickname: string
  display_name: string
  avatar_url: string
  city: string
  birthday_month: number
}

export interface BirthdayWish {
  id: number
  recipient_account_id: string | null
  recipient_name: string
  display_name: string
  content: string
  display_mode: string
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function fetchCurrentMonthBirthdays(): Promise<PaginatedResponse<BirthdayClassmate>> {
  const resp = await apiClient.get<PaginatedResponse<BirthdayClassmate>>('/v1/birthdays/current-month/')
  return resp.data
}

export async function fetchBirthdayWishes(params?: { recipient?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<BirthdayWish>> {
  const resp = await apiClient.get<PaginatedResponse<BirthdayWish>>('/v1/birthdays/wishes/', { params })
  return resp.data
}

export async function createBirthdayWish(data: {
  recipient_account_ids?: string[]
  content: string
  display_mode: string
}): Promise<BirthdayWish[]> {
  const resp = await apiClient.post<BirthdayWish[]>('/v1/birthdays/wishes/', data)
  return resp.data
}

export async function deleteBirthdayWish(id: number): Promise<void> {
  await apiClient.delete(`/v1/birthdays/wishes/${id}/`)
}
