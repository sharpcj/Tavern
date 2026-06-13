<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else-if="announcement">
      <div class="detail-header">
        <el-tag v-if="announcement.is_pinned" type="danger">置顶</el-tag>
        <el-tag v-if="announcement.require_read_confirm" :type="announcement.is_read ? 'success' : 'warning'">
          {{ announcement.is_read ? '已确认' : '待确认' }}
        </el-tag>
        <h1>{{ announcement.title }}</h1>
        <p class="muted">
          发布人：{{ announcement.publisher_name }} · 发布时间：{{ formatTime(announcement.created_at) }}
          <span v-if="announcement.expires_at"> · 有效期至：{{ formatTime(announcement.expires_at) }}</span>
        </p>
      </div>

      <article class="content">{{ announcement.content }}</article>

      <div class="actions">
        <el-button v-if="announcement.require_read_confirm && !announcement.is_read" type="primary" :loading="submitting" @click="confirmRead">
          确认已读
        </el-button>
        <el-button @click="$router.back()">返回</el-button>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { confirmAnnouncementRead, fetchAnnouncementDetail, type AnnouncementDetail } from '@/api/announcements'

const route = useRoute()
const loading = ref(true)
const submitting = ref(false)
const announcement = ref<AnnouncementDetail | null>(null)

async function load() {
  loading.value = true
  try {
    announcement.value = await fetchAnnouncementDetail(Number(route.params.id))
  } finally {
    loading.value = false
  }
}

async function confirmRead() {
  if (!announcement.value) return
  submitting.value = true
  try {
    announcement.value = await confirmAnnouncementRead(announcement.value.id)
    ElMessage.success('已确认阅读')
  } finally {
    submitting.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => load())
</script>

<style scoped>
.detail-header h1 { margin: 10px 0; }
.content { margin-top: 20px; line-height: 1.8; white-space: pre-wrap; }
.actions { margin-top: 24px; display: flex; gap: 8px; }
</style>
