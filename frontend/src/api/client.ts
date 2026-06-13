import axios from 'axios'

import { getAccessToken } from '@/stores/auth'

function getDefaultApiBaseURL() {
  if (typeof window === 'undefined') return 'http://localhost:8000/api'
  return `${window.location.protocol}//${window.location.hostname}:8000/api`
}

const apiBaseURL = import.meta.env.VITE_API_BASE_URL ?? getDefaultApiBaseURL()

export const apiClient = axios.create({
  baseURL: apiBaseURL,
  timeout: 10_000,
})

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
