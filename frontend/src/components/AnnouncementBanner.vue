<template>
  <section class="page-card announcement-banner" v-if="announcements.length > 0">
    <div class="banner-header">
      <strong>最新公告</strong>
      <el-button text size="small" @click="$router.push('/announcements')">查看全部</el-button>
    </div>
    <div v-for="item in announcements" :key="item.id" class="banner-item" @click="$router.push(`/announcements/${item.id}`)">
      <el-tag size="small" :type="item.is_pinned ? 'danger' : 'info'">{{ item.is_pinned ? '置顶' : '公告' }}</el-tag>
      <span class="title">{{ item.title }}</span>
      <el-tag v-if="item.require_read_confirm && !item.is_read" size="small" type="warning">待确认</el-tag>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchAnnouncements, type AnnouncementListItem } from '@/api/announcements'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'

const announcements = ref<AnnouncementListItem[]>([])

async function load() {
  const resp = await fetchAnnouncements({ page: 1, page_size: 50 })
  announcements.value = [...resp.results]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3)
}

onMounted(() => load())
useRealtimeEvent((event) => {
  if (event.type === 'announcement.created' || event.type === 'notification.created') {
    load()
  }
})
</script>

<style scoped>
.announcement-banner { margin-bottom: 16px; border-color: #fbbf24; background: #fffbeb; }
.banner-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.banner-item { display: flex; gap: 8px; align-items: center; padding: 8px 0; cursor: pointer; }
.banner-item + .banner-item { border-top: 1px solid #fde68a; }
.title { font-weight: 600; }
</style>
