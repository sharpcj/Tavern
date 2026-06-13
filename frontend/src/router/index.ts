import { createRouter, createWebHistory } from 'vue-router'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import NotFoundPage from '@/pages/NotFoundPage.vue'
import RegisterPage from '@/pages/RegisterPage.vue'
import ReviewStatusPage from '@/pages/ReviewStatusPage.vue'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresApproved?: boolean
    allowRestricted?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomePage,
          meta: { requiresAuth: false },
        },
        {
          path: 'register',
          name: 'register',
          component: RegisterPage,
          meta: { requiresAuth: false },
        },
        {
          path: 'login',
          name: 'login',
          component: LoginPage,
          meta: { requiresAuth: false },
        },
        {
          path: 'review-status',
          name: 'review-status',
          component: ReviewStatusPage,
          meta: { requiresAuth: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundPage,
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Load user info if we have a token but no user data yet.
  if (authStore.isAuthenticated && !authStore.userLoaded) {
    await authStore.loadCurrentUser()
  }

  const requiresAuth = to.meta.requiresAuth !== false

  if (!requiresAuth) {
    // Public pages: register, login, home — always accessible.
    next()
    return
  }

  // --- All routes below require authentication ---

  if (!authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Banned users can only see review-status.
  if (authStore.isAccountBanned) {
    if (to.name !== 'review-status') {
      next({ name: 'review-status' })
      return
    }
    next()
    return
  }

  // Non-approved users (pending, rejected, need_more_info) can only see review-status.
  if (!authStore.isReviewApproved) {
    if (to.name !== 'review-status') {
      next({ name: 'review-status' })
      return
    }
    next()
    return
  }

  // Restricted users: only pages that explicitly allow restricted access.
  if (authStore.isAccountRestricted && !to.meta.allowRestricted) {
    if (to.name !== 'review-status') {
      next({ name: 'review-status' })
      return
    }
  }

  next()
})

export default router
