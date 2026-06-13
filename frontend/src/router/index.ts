import { createRouter, createWebHistory } from 'vue-router'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import ClassmateDetailPage from '@/pages/ClassmateDetailPage.vue'
import ClassmateListPage from '@/pages/ClassmateListPage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import NotFoundPage from '@/pages/NotFoundPage.vue'
import PostCreatePage from '@/pages/PostCreatePage.vue'
import PostDetailPage from '@/pages/PostDetailPage.vue'
import PostListPage from '@/pages/PostListPage.vue'
import ProfileEditPage from '@/pages/ProfileEditPage.vue'
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
          component: PostListPage,
          meta: { requiresAuth: true, requiresApproved: true },
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
        {
          path: 'profile/edit',
          name: 'profile-edit',
          component: ProfileEditPage,
          meta: { requiresAuth: true, requiresApproved: true },
        },
        {
          path: 'classmates',
          name: 'classmate-list',
          component: ClassmateListPage,
          meta: { requiresAuth: true, requiresApproved: true },
        },
        {
          path: 'classmates/:accountId',
          name: 'classmate-detail',
          component: ClassmateDetailPage,
          meta: { requiresAuth: true, requiresApproved: true },
        },
        {
          path: 'posts/create',
          name: 'post-create',
          component: PostCreatePage,
          meta: { requiresAuth: true, requiresApproved: true },
        },
        {
          path: 'posts/:id',
          name: 'post-detail',
          component: PostDetailPage,
          meta: { requiresAuth: true, requiresApproved: true },
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

  if (authStore.isAuthenticated && !authStore.userLoaded) {
    await authStore.loadCurrentUser()
  }

  const requiresAuth = to.meta.requiresAuth !== false

  if (!requiresAuth) {
    next()
    return
  }

  if (!authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (authStore.isAccountBanned) {
    if (to.name !== 'review-status') {
      next({ name: 'review-status' })
      return
    }
    next()
    return
  }

  if (!authStore.isReviewApproved) {
    if (to.name !== 'review-status') {
      next({ name: 'review-status' })
      return
    }
    next()
    return
  }

  if (authStore.isAccountRestricted && !to.meta.allowRestricted) {
    if (to.name !== 'review-status') {
      next({ name: 'review-status' })
      return
    }
  }

  next()
})

export default router
