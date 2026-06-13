<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-title" @click="$router.push('/')">Tavern 同学社区</div>
      <div class="app-nav desktop-nav">
        <template v-if="authStore.isAuthenticated && authStore.isReviewApproved">
          <el-button text @click="$router.push('/activities')">活动</el-button>
          <el-button text @click="$router.push('/albums')">相册</el-button>
          <el-button text @click="$router.push('/announcements')">公告</el-button>
          <el-button text @click="$router.push('/birthdays')">生日</el-button>
          <el-button text @click="$router.push('/classmates')">通讯录</el-button>
          <el-button text @click="$router.push('/notifications')">系统通知</el-button>
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
              <el-avatar :size="32" :src="profileAvatarUrl">
                {{ avatarText }}
              </el-avatar>
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
        <el-avatar v-if="authStore.isAuthenticated" :size="30" :src="profileAvatarUrl">
          {{ avatarText }}
        </el-avatar>
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
          <el-button text @click="go('/notifications')">系统通知</el-button>
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { fetchMyProfile } from '@/api/profile'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const profileAvatarUrl = ref('')
const profileNickname = ref('')
const mobileMenuVisible = ref(false)

const avatarText = computed(() => {
  const name = profileNickname.value || authStore.currentUser?.nickname || authStore.currentUser?.real_name || authStore.currentUser?.email || '我'
  return name.slice(0, 1)
})

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

onMounted(() => loadProfileAvatar())
watch(() => authStore.currentUser?.account_id, () => loadProfileAvatar())
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
