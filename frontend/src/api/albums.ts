import { apiClient } from './client'

export interface AlbumListItem {
  id: number
  title: string
  description: string
  category: string
  category_display: string
  creator_name: string
  activity: number | null
  cover_url: string | null
  photo_count: number
  created_at: string
}

export interface PhotoListItem {
  id: number
  album: number
  display_name: string
  caption: string
  display_mode: string
  image_url: string
  comment_count: number
  created_at: string
}

export interface PhotoComment {
  id: number
  author_id: string
  author_real_name: string
  display_name: string
  content: string
  display_mode: string
  parent: number | null
  replies: PhotoCommentReply[]
  created_at: string
}

export interface PhotoCommentReply {
  id: number
  author_id: string
  author_real_name: string
  display_name: string
  content: string
  display_mode: string
  parent: number | null
  reply_to: number | null
  reply_to_display_name: string
  created_at: string
}

export interface AlbumDetail extends AlbumListItem {
  photos: PhotoListItem[]
  updated_at: string
}

export interface PhotoDetail extends PhotoListItem {
  comments: PhotoComment[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AlbumPayload {
  title: string
  description: string
  category: string
  activity?: number | null
}

export const ALBUM_CATEGORIES = [
  { value: 'campus', label: '高中校园' },
  { value: 'graduation', label: '毕业照' },
  { value: 'teacher', label: '老师合影' },
  { value: 'gathering', label: '聚会照片' },
  { value: 'classmate_life', label: '同学近况' },
  { value: 'memory', label: '班级纪念' },
]

export async function fetchAlbums(params?: {
  category?: string
  activity?: number
  page?: number
  page_size?: number
}): Promise<PaginatedResponse<AlbumListItem>> {
  const resp = await apiClient.get<PaginatedResponse<AlbumListItem>>('/v1/albums/', { params })
  return resp.data
}

export async function createAlbum(data: AlbumPayload): Promise<AlbumDetail> {
  const resp = await apiClient.post<AlbumDetail>('/v1/albums/', data)
  return resp.data
}

export async function fetchAlbumDetail(id: number): Promise<AlbumDetail> {
  const resp = await apiClient.get<AlbumDetail>(`/v1/albums/${id}/`)
  return resp.data
}

export async function uploadPhoto(albumId: number, data: { image: File; caption: string; display_mode: string }): Promise<PhotoDetail> {
  const formData = new FormData()
  formData.append('image', data.image)
  formData.append('caption', data.caption)
  formData.append('display_mode', data.display_mode)
  const resp = await apiClient.post<PhotoDetail>(`/v1/albums/${albumId}/photos/`, formData)
  return resp.data
}

export async function fetchPhotoDetail(id: number): Promise<PhotoDetail> {
  const resp = await apiClient.get<PhotoDetail>(`/v1/photos/${id}/`)
  return resp.data
}

export async function createPhotoComment(photoId: number, data: { content: string; display_mode: string }): Promise<PhotoComment> {
  const resp = await apiClient.post<PhotoComment>(`/v1/photos/${photoId}/comments/`, data)
  return resp.data
}

export async function replyToPhotoComment(commentId: number, data: { content: string; display_mode: string }): Promise<PhotoComment> {
  const resp = await apiClient.post<PhotoComment>(`/v1/photo-comments/${commentId}/replies/`, data)
  return resp.data
}

export async function deleteAlbum(id: number): Promise<void> {
  await apiClient.delete(`/v1/albums/${id}/`)
}

export async function deletePhoto(id: number): Promise<void> {
  await apiClient.delete(`/v1/photos/${id}/delete/`)
}

export async function deletePhotoComment(id: number): Promise<void> {
  await apiClient.delete(`/v1/photo-comments/${id}/`)
}
