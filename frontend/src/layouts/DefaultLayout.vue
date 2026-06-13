<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-title" @click="$router.push('/')">Tavern 同学社区</div>
      <div class="app-nav">
        <template v-if="authStore.isAuthenticated && authStore.isReviewApproved">
          <el-button text @click="$router.push('/classmates')">通讯录</el-button>
          <el-button text @click="$router.push('/activities')">活动</el-button>
          <el-button text @click="$router.push('/announcements')">公告</el-button>
          <el-button text @click="$router.push('/albums')">相册</el-button>
          <el-button text @click="$router.push('/birthdays')">生日</el-button>
          <el-button text @click="$router.push('/profile/edit')">编辑资料</el-button>
        </template>
        <template v-if="!authStore.isAuthenticated">
          <el-button text @click="$router.push('/register')">注册</el-button>
          <el-button text @click="$router.push('/login')">登录</el-button>
        </template>
        <template v-if="authStore.isAuthenticated">
          <el-button text @click="$router.push('/review-status')">审核状态</el-button>
          <el-button text @click="logout">退出</el-button>
        </template>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>
