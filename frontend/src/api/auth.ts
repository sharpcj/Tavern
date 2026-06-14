import { apiClient } from './client'

export interface RegisterPayload {
  email: string
  password: string
  password_confirm: string
  real_name: string
  high_school: string
  high_school_class: string
  nickname?: string
  extra_info?: string
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface CurrentUser {
  id: number
  account_id: string
  email: string
  real_name: string
  high_school: string
  high_school_class: string
  nickname: string
  extra_info: string
  role: string
  role_display: string
  review_status: string
  review_status_display: string
  account_status: string
  account_status_display: string
  review_message: string
  date_joined: string
}

export async function register(payload: RegisterPayload) {
  const response = await apiClient.post('/v1/auth/register/', payload)
  return response.data
}

export async function login(email: string, password: string): Promise<TokenPair> {
  const response = await apiClient.post<TokenPair>('/v1/auth/token/', { email, password })
  return response.data
}

export async function refreshAccessToken(refresh: string): Promise<TokenPair> {
  const response = await apiClient.post<TokenPair>('/v1/auth/token/refresh/', { refresh })
  return response.data
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>('/v1/auth/me/')
  return response.data
}
