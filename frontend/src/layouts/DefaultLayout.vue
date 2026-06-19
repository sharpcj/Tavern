<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-title" @click="$router.push('/home')">Tavern 同学社区</div>
      <div class="app-nav desktop-nav">
        <template v-if="authStore.isAuthenticated && authStore.isReviewApproved">
          <el-button text @click="$router.push('/activities')">活动</el-button>
          <el-button text @click="$router.push('/albums')">相册</el-button>
          <el-button text @click="$router.push('/announcements')">公告</el-button>
          <el-button text @click="$router.push('/birthdays')">生日</el-button>
          <el-button text @click="$router.push('/classmates')">通讯录</el-button>
          <el-badge :value="unreadNotificationCount" :hidden="unreadNotificationCount === 0" :max="99" class="nav-badge">
            <el-button text @click="$router.push('/notifications')">系统通知</el-button>
          </el-badge>
          <el-button v-if="authStore.isModeratorOrAbove" text @click="$router.push('/admin/reports')">举报处理</el-button>
        </template>
        <template v-if="!authStore.isAuthenticated">
          <el-button text @click="$router.push('/register')">注册</el-button>
          <el-button text @click="$router.push('/login')">登录</el-button>
        </template>
        <template v-if="authStore.isAuthenticated">
          <el-button v-if="!authStore.isReviewApproved" text @click="$router.push('/review-status')">审核状态</el-button>
          <el-dropdown trigger="click" @command="handleUserMenuCommand">
            <span class="user-avatar-trigger">
              <UserAvatar :src="profileAvatarUrl" :size="32" />
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="authStore.isReviewApproved" command="profile">编辑个人资料</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>

      <div class="mobile-nav">
        <UserAvatar v-if="authStore.isAuthenticated" :src="profileAvatarUrl" :size="30" />
        <el-button text class="mobile-menu-button" @click="mobileMenuVisible = true">菜单</el-button>
      </div>
    </el-header>

    <el-drawer v-model="mobileMenuVisible" title="菜单" direction="rtl" size="78%">
      <div class="mobile-menu">
        <template v-if="authStore.isAuthenticated && authStore.isReviewApproved">
          <el-button text @click="go('/activities')">活动</el-button>
          <el-button text @click="go('/albums')">相册</el-button>
          <el-button text @click="go('/announcements')">公告</el-button>
          <el-button text @click="go('/birthdays')">生日</el-button>
          <el-button text @click="go('/classmates')">通讯录</el-button>
          <el-badge :value="unreadNotificationCount" :hidden="unreadNotificationCount === 0" :max="99" class="mobile-badge">
            <el-button text @click="go('/notifications')">系统通知</el-button>
          </el-badge>
          <el-button v-if="authStore.isModeratorOrAbove" text @click="go('/admin/reports')">举报处理</el-button>
          <el-divider />
          <el-button text @click="go('/profile/edit')">编辑个人资料</el-button>
        </template>
        <template v-if="authStore.isAuthenticated && !authStore.isReviewApproved">
          <el-button text @click="go('/review-status')">审核状态</el-button>
        </template>
        <template v-if="!authStore.isAuthenticated">
          <el-button text @click="go('/register')">注册</el-button>
          <el-button text @click="go('/login')">登录</el-button>
        </template>
        <template v-if="authStore.isAuthenticated">
          <el-divider />
          <el-button text type="danger" @click="logoutFromMobile">退出</el-button>
        </template>
      </div>
    </el-drawer>

    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import UserAvatar from '@/components/UserAvatar.vue'
import { fetchUnreadNotificationCount } from '@/api/notifications'
import { fetchMyProfile } from '@/api/profile'
import { startRealtimeEvents, stopRealtimeEvents, useRealtimeEvent } from '@/composables/useRealtimeEvents'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const profileAvatarUrl = ref('')
const profileNickname = ref('')
const mobileMenuVisible = ref(false)
const unreadNotificationCount = ref(0)

async function loadProfileAvatar() {
  if (!authStore.isAuthenticated) {
    profileAvatarUrl.value = ''
    profileNickname.value = ''
    return
  }
  try {
    const profile = await fetchMyProfile()
    profileAvatarUrl.value = profile.avatar_url || ''
    profileNickname.value = profile.nickname || ''
  } catch {
    profileAvatarUrl.value = ''
    profileNickname.value = ''
  }
}

async function loadUnreadNotificationCount() {
  if (!authStore.isAuthenticated || !authStore.isReviewApproved) {
    unreadNotificationCount.value = 0
    return
  }
  try {
    unreadNotificationCount.value = await fetchUnreadNotificationCount()
  } catch {
    unreadNotificationCount.value = 0
  }
}

function refreshRealtimeConnection() {
  stopRealtimeEvents()
  if (authStore.isAuthenticated && authStore.isReviewApproved && authStore.isAccountNormal) {
    startRealtimeEvents()
    loadUnreadNotificationCount()
  }
}

function go(path: string) {
  mobileMenuVisible.value = false
  router.push(path)
}

function handleUserMenuCommand(command: string) {
  if (command === 'profile') {
    router.push('/profile/edit')
    return
  }
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function logoutFromMobile() {
  mobileMenuVisible.value = false
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadProfileAvatar()
  loadUnreadNotificationCount()
  refreshRealtimeConnection()
})
watch(() => authStore.currentUser?.account_id, () => {
  loadProfileAvatar()
  refreshRealtimeConnection()
})
useRealtimeEvent((event) => {
  if (event.type === 'notification.created' || event.type === 'notification.read') {
    loadUnreadNotificationCount()
  }
})
</script>

<style scoped>
.user-avatar-trigger {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  outline: none;
}
.mobile-nav {
  display: none;
  align-items: center;
  gap: 8px;
}
.mobile-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mobile-menu .el-button {
  justify-content: flex-start;
  width: 100%;
  margin-left: 0;
  font-size: 16px;
}
.nav-badge {
  display: inline-flex;
  align-items: center;
}
.mobile-badge {
  width: 100%;
}
.mobile-badge :deep(.el-badge__content) {
  right: 8px;
}
@media (max-width: 768px) {
  .desktop-nav {
    display: none;
  }
  .mobile-nav {
    display: flex;
  }
  .mobile-menu-button {
    padding: 8px 10px;
  }
}
</style>
