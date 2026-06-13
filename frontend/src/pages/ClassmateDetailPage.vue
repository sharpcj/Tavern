<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="6" animated />
    <template v-else-if="classmate">
      <div class="detail-header">
        <el-avatar :src="classmate.avatar_url" :size="64">{{ classmate.real_name[0] }}</el-avatar>
        <div class="detail-title">
          <h1>{{ classmate.real_name }}<span v-if="classmate.nickname" class="nickname">（{{ classmate.nickname }}）</span></h1>
          <p class="muted">{{ classmate.city || '未填写城市' }} · {{ classmate.occupation || '未填写职业' }}</p>
        </div>
      </div>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="城市">{{ classmate.city || '-' }}</el-descriptions-item>
        <el-descriptions-item label="职业/行业">{{ classmate.occupation || '-' }}</el-descriptions-item>
        <el-descriptions-item label="生日月份">
          {{ classmate.birthday_month ? classmate.birthday_month + ' 月' : '未填写' }}
        </el-descriptions-item>
        <el-descriptions-item label="个人简介">{{ classmate.bio || '暂无简介' }}</el-descriptions-item>
      </el-descriptions>

      <h2 style="margin-top:24px">联系方式</h2>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="邮箱">
          {{ classmate.email || '未公开' }}
        </el-descriptions-item>
        <el-descriptions-item label="手机号">
          {{ classmate.phone || '未公开' }}
        </el-descriptions-item>
        <el-descriptions-item label="微信号">
          {{ classmate.wechat || '未公开' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-button style="margin-top:16px" @click="$router.back()">返回通讯录</el-button>
    </template>
    <el-empty v-else description="同学不存在" />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { fetchClassmateDetail, type ClassmateDetail } from '@/api/profile'

const route = useRoute()
const loading = ref(true)
const classmate = ref<ClassmateDetail | null>(null)

onMounted(async () => {
  try {
    classmate.value = await fetchClassmateDetail(route.params.accountId as string)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.detail-title h1 {
  margin: 0;
  font-size: 24px;
}
.nickname {
  font-size: 16px;
  color: #6b7280;
  font-weight: 400;
}
</style>
