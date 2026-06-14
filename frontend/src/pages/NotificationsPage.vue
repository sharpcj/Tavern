<template>
  <section class="page-card">
    <div class="feed-header">
      <div>
        <h1>通知中心</h1>
        <p class="muted">这里只展示系统通知，不支持私信、回复或聊天。</p>
      </div>
      <el-button type="primary" :disabled="unreadCount === 0" @click="markAllRead">全部已读</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="load">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane :label="`未读 (${unreadCount})`" name="unread" />
    </el-tabs>

    <div v-loading="loading">
      <el-empty v-if="notifications.length === 0" description="暂无通知" />
      <div
        v-for="item in notifications"
        :key="item.id"
        class="notification-item"
        :class="{ unread: !item.is_read, clickable: Boolean(item.target_url) }"
        @click="openNotification(item)"
      >
        <div class="notification-header">
          <el-tag size="small" :type="item.is_read ? 'info' : 'danger'">{{ item.is_read ? '已读' : '未读' }}</el-tag>
          <strong>{{ item.title }}</strong>
          <span class="time">{{ formatTime(item.created_at) }}</span>
        </div>
        <div class="type">{{ item.notification_type_display }}</div>
        <div class="content">{{ item.content }}</div>
        <el-button v-if="!item.is_read" text size="small" type="primary" @click.stop="markRead(item.id)">标记已读</el-button>
        <el-button v-if="item.target_url" text size="small" type="primary" @click.stop="openNotification(item)">查看详情</el-button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchNotifications, fetchUnreadNotificationCount, markAllNotificationsRead, markNotificationRead, type NotificationItem } from '@/api/notifications'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'

const router = useRouter()
const loading = ref(false)
const activeTab = ref('all')
const notifications = ref<NotificationItem[]>([])
const unreadCount = ref(0)

async function load() {
  loading.value = true
  try {
    const [list, count] = await Promise.all([
      fetchNotifications({ unread: activeTab.value === 'unread' }),
      fetchUnreadNotificationCount(),
    ])
    notifications.value = list.results
    unreadCount.value = count
  } finally { loading.value = false }
}

async function markRead(id: number) {
  await markNotificationRead(id)
  ElMessage.success('已标记为已读')
  await load()
}

async function openNotification(item: NotificationItem) {
  if (!item.is_read) {
    await markNotificationRead(item.id)
    item.is_read = true
    unreadCount.value = Math.max(unreadCount.value - 1, 0)
  }
  if (item.target_url) {
    await router.push(item.target_url)
  }
}

async function markAllRead() {
  const result = await markAllNotificationsRead()
  ElMessage.success(`已标记 ${result.updated} 条通知`)
  await load()
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(() => load())
useRealtimeEvent((event) => {
  if (event.type === 'notification.created' || event.type === 'notification.read') {
    load()
  }
})
</script>

<style scoped>
.notification-item { padding: 14px 0; border-bottom: 1px solid #e5e7eb; }
.notification-item.clickable { cursor: pointer; }
.notification-item.clickable:hover { background: #f8fafc; border-radius: 8px; padding-left: 8px; padding-right: 8px; }
.notification-item.unread { background: #fff7ed; padding-left: 8px; border-radius: 8px; }
.notification-header { display: flex; align-items: center; gap: 8px; }
.time { margin-left: auto; font-size: 12px; color: #9ca3af; }
.type { margin-top: 6px; color: #6b7280; font-size: 13px; }
.content { margin: 8px 0; line-height: 1.7; white-space: pre-wrap; }
</style>
