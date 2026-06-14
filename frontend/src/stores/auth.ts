import { defineStore } from 'pinia'

import { fetchCurrentUser, login, refreshAccessToken, type CurrentUser, type TokenPair } from '@/api/auth'

const ACCESS_TOKEN_KEY = 'tavern_access_token'
const REFRESH_TOKEN_KEY = 'tavern_refresh_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) ?? '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) ?? '',
    currentUser: null as CurrentUser | null,
    userLoaded: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
    reviewStatus: (state) => state.currentUser?.review_status ?? null,
    accountStatus: (state) => state.currentUser?.account_status ?? null,
    role: (state) => state.currentUser?.role ?? null,
    isModeratorOrAbove: (state) => state.currentUser?.role === 'moderator' || state.currentUser?.role === 'super_admin',
    isReviewApproved: (state) => state.currentUser?.review_status === 'approved',
    isAccountNormal: (state) => state.currentUser?.account_status === 'normal',
    isAccountBanned: (state) => state.currentUser?.account_status === 'banned',
    isAccountRestricted: (state) => state.currentUser?.account_status === 'restricted',
  },
  actions: {
    async login(email: string, password: string) {
      const tokens = await login(email, password)
      this.saveTokens(tokens)
      await this.loadCurrentUser()
    },
    saveTokens(tokens: TokenPair) {
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
    },
    async refreshSession() {
      if (!this.refreshToken) return false
      try {
        const tokens = await refreshAccessToken(this.refreshToken)
        this.saveTokens(tokens)
        return true
      } catch {
        return false
      }
    },
    async loadCurrentUser() {
      try {
        this.currentUser = await fetchCurrentUser()
        this.userLoaded = true
      } catch {
        const refreshed = await this.refreshSession()
        if (!refreshed) {
          this.clearAuth()
          return
        }
        try {
          this.currentUser = await fetchCurrentUser()
          this.userLoaded = true
        } catch {
          this.clearAuth()
        }
      }
    },
    logout() {
      this.clearAuth()
    },
    clearAuth() {
      this.accessToken = ''
      this.refreshToken = ''
      this.currentUser = null
      this.userLoaded = false
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    },
  },
})

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? ''
}
