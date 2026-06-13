<template>
  <section class="page-card">
    <h1>审核状态</h1>
    <el-skeleton v-if="loading" :rows="4" animated />
    <template v-else-if="authStore.currentUser">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="账号标识">{{ authStore.currentUser.account_id }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ authStore.currentUser.email }}</el-descriptions-item>
        <el-descriptions-item label="真实姓名">{{ authStore.currentUser.real_name }}</el-descriptions-item>
        <el-descriptions-item label="高三所在学校">{{ authStore.currentUser.high_school }}</el-descriptions-item>
        <el-descriptions-item label="高三所在班级">{{ authStore.currentUser.high_school_class }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">
          <el-tag :type="tagType">{{ authStore.currentUser.review_status_display }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="authStore.currentUser.review_message" label="审核说明">
          {{ authStore.currentUser.review_message }}
        </el-descriptions-item>
      </el-descriptions>
      <el-alert class="form-tip" :title="statusTip" type="info" :closable="false" show-icon />
      <el-button @click="reload">刷新状态</el-button>
      <el-button text @click="logout">退出登录</el-button>
    </template>
    <el-empty v-else description="请先登录">
      <el-button type="primary" @click="$router.push('/login')">去登录</el-button>
    </el-empty>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const tagType = computed(() => {
  switch (authStore.currentUser?.review_status) {
    case 'approved':
      return 'success'
    case 'rejected':
      return 'danger'
    case 'need_more_info':
      return 'warning'
    default:
      return 'info'
  }
})

const statusTip = computed(() => {
  switch (authStore.currentUser?.review_status) {
    case 'approved':
      return '账号已审核通过，后续内部社区模块上线后即可访问。'
    case 'rejected':
      return '账号审核未通过，如需申诉请联系管理员。'
    case 'need_more_info':
      return '管理员需要你补充资料，补充资料入口将在后续模块完善。'
    default:
      return '账号正在等待管理员审核，请耐心等待。'
  }
})

async function reload() {
  loading.value = true
  try {
    await authStore.loadCurrentUser()
  } finally {
    loading.value = false
  }
}

function logout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  await reload()
})
</script>
