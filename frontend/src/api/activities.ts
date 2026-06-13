import { apiClient } from './client'

export interface ActivityListItem {
  id: number
  title: string
  activity_type: string
  activity_type_display: string
  initiator_name: string
  status: string
  status_display: string
  location: string
  start_time: string | null
  deadline: string | null
  signup_count: number
  created_at: string
}

export interface ActivityDetail {
  id: number
  title: string
  activity_type: string
  activity_type_display: string
  initiator_id: string
  initiator_name: string
  description: string
  location: string
  start_time: string | null
  deadline: string | null
  max_participants: number | null
  allow_guests: boolean
  contact_info: string
  status: string
  status_display: string
  is_multi_choice: boolean
  show_voter_names: boolean
  allow_vote_change: boolean
  vote_options: VoteOption[]
  signups: SignupItem[]
  vote_results: VoteResult[]
  chain_records: ChainRecordItem[]
  created_at: string
  updated_at: string
}

export interface VoteOption {
  id: number
  text: string
  order: number
}

export interface SignupItem {
  real_name: string
  participant_count: number
  bring_guests: boolean
  note: string
  created_at: string
}

export interface VoteResult {
  option_id: number
  text: string
  count: number
  voters?: string[]
}

export interface ChainRecordItem {
  real_name: string
  will_attend: boolean
  participant_count: number
  note: string
  created_at: string
}

export interface ActivityCreatePayload {
  title: string
  activity_type: 'gathering' | 'voting' | 'chain'
  description: string
  location?: string
  start_time?: string
  deadline?: string
  max_participants?: number
  allow_guests?: boolean
  contact_info?: string
  is_multi_choice?: boolean
  show_voter_names?: boolean
  allow_vote_change?: boolean
  vote_options?: string[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export const ACTIVITY_TYPES = [
  { value: 'gathering', label: '聚会报名' },
  { value: 'voting', label: '投票' },
  { value: 'chain', label: '接龙' },
]

export async function fetchActivities(params?: {
  status?: string
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<ActivityListItem>> {
  const resp = await apiClient.get<PaginatedResponse<ActivityListItem>>('/v1/activities/', { params })
  return resp.data
}

export async function fetchActivityDetail(id: number): Promise<ActivityDetail> {
  const resp = await apiClient.get<ActivityDetail>(`/v1/activities/${id}/`)
  return resp.data
}

export async function createActivity(data: ActivityCreatePayload): Promise<ActivityDetail> {
  const resp = await apiClient.post<ActivityDetail>('/v1/activities/', data)
  return resp.data
}

export async function signupActivity(id: number, data: { participant_count: number; bring_guests: boolean; note: string }) {
  await apiClient.post(`/v1/activities/${id}/signup/`, data)
}

export async function cancelSignup(id: number) {
  await apiClient.delete(`/v1/activities/${id}/signup/`)
}

export async function voteActivity(id: number, optionIds: number[]) {
  await apiClient.post(`/v1/activities/${id}/vote/`, { option_ids: optionIds })
}

export async function fillChain(id: number, data: { will_attend: boolean; participant_count: number; note: string }) {
  await apiClient.post(`/v1/activities/${id}/chain/`, data)
}

export async function updateActivityStatus(id: number, status: string) {
  await apiClient.post(`/v1/activities/${id}/update-status/`, { status })
}
