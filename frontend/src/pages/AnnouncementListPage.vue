<template>
  <section class="page-card">
    <div class="feed-header">
      <h1>公告</h1>
      <el-button v-if="authStore.isModeratorOrAbove" type="primary" @click="$router.push('/announcements/create')">发布公告</el-button>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!loading && announcements.length === 0" description="暂无公告" />
      <div v-for="item in announcements" :key="item.id" class="announcement-card" @click="$router.push(`/announcements/${item.id}`)">
        <div class="card-header">
          <el-tag v-if="item.is_pinned" type="danger" size="small">置顶</el-tag>
          <el-tag v-if="item.require_read_confirm" :type="item.is_read ? 'success' : 'warning'" size="small">
            {{ item.is_read ? '已确认' : '待确认' }}
          </el-tag>
          <span class="card-title">{{ item.title }}</span>
        </div>
        <div class="card-meta">
          <span>发布人：{{ item.publisher_name }}</span>
          <span>发布时间：{{ formatTime(item.created_at) }}</span>
          <span v-if="item.expires_at">有效期至：{{ formatTime(item.expires_at) }}</span>
        </div>
      </div>
    </div>

    <el-pagination v-if="total > pageSize" class="pagination" :current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="loadPage" />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchAnnouncements, type AnnouncementListItem } from '@/api/announcements'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const announcements = ref<AnnouncementListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

async function load(showLoading = true) {
  if (showLoading) loading.value = true
  try {
    const resp = await fetchAnnouncements({ page: currentPage.value, page_size: pageSize })
    announcements.value = resp.results
    total.value = resp.count
  } finally {
    if (showLoading) loading.value = false
  }
}

function loadPage(page: number) {
  currentPage.value = page
  load()
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => load())
useRealtimeEvent((event) => {
  if (event.type === 'announcement.created') {
    currentPage.value = 1
    load(false)
  }
})
</script>

<style scoped>
.feed-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.feed-header h1 { margin: 0; }
.announcement-card { padding: 16px; margin-bottom: 10px; border: 1px solid #e5e7eb; border-radius: 12px; cursor: pointer; transition: box-shadow 0.2s; }
.announcement-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.card-title { font-weight: 600; font-size: 16px; }
.card-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #6b7280; }
.pagination { margin-top: 20px; justify-content: center; }
</style>
