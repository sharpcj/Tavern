import { defineStore } from 'pinia'

import { fetchCurrentUser, login, type CurrentUser } from '@/api/auth'

const ACCESS_TOKEN_KEY = 'tavern_access_token'
const REFRESH_TOKEN_KEY = 'tavern_refresh_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) ?? '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) ?? '',
    currentUser: null as CurrentUser | null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    async login(email: string, password: string) {
      const tokens = await login(email, password)
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
      await this.loadCurrentUser()
    },
    async loadCurrentUser() {
      this.currentUser = await fetchCurrentUser()
    },
    logout() {
      this.accessToken = ''
      this.refreshToken = ''
      this.currentUser = null
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    },
  },
})

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? ''
}
