<template>
  <AnnouncementBanner />
  <section class="page-card">
    <div class="feed-header">
      <h1>班级动态</h1>
      <el-button type="primary" @click="$router.push('/posts/create')">发布动态</el-button>
    </div>

    <el-radio-group v-model="activeCategory" class="category-filter" @change="loadPosts()">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button v-for="cat in POST_CATEGORIES" :key="cat.value" :value="cat.value">{{ cat.label }}</el-radio-button>
    </el-radio-group>

    <el-alert
      v-if="pendingNewPostCount > 0"
      class="new-post-alert"
      :title="`有 ${pendingNewPostCount} 条新动态，点击刷新查看`"
      type="success"
      show-icon
      :closable="false"
      @click="refreshNewPosts()"
    />

    <div v-loading="loading">
      <el-empty v-if="!loading && posts.length === 0" description="还没有动态，来发布第一条吧" />
      <div v-for="post in posts" :key="post.id" class="post-card" @click="$router.push(`/posts/${post.id}`)">
        <div class="post-card-header">
          <el-tag v-if="post.is_pinned" type="danger" size="small">置顶</el-tag>
          <span class="post-author">{{ post.display_name }}</span>
          <span class="post-time">{{ formatTime(post.created_at) }}</span>
          <el-tag size="small" type="info">{{ post.category_display }}</el-tag>
        </div>
        <div class="post-content">{{ truncate(post.content, 200) }}</div>
        <div v-if="post.images.length" class="post-images">
          <img v-for="(url, i) in post.images.slice(0, 3)" :key="i" :src="url" class="post-thumb" />
        </div>
        <div class="post-meta">
          <span>{{ post.comment_count }} 条评论</span>
        </div>
      </div>
    </div>

    <el-pagination
      v-if="total > pageSize"
      class="pagination"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="loadPage"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import AnnouncementBanner from '@/components/AnnouncementBanner.vue'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'
import { fetchPosts, POST_CATEGORIES, type PostListItem } from '@/api/posts'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const posts = ref<PostListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const activeCategory = ref('')
const pendingNewPostCount = ref(0)

async function loadPosts(showLoading = true) {
  if (showLoading) loading.value = true
  try {
    const resp = await fetchPosts({
      category: activeCategory.value || undefined,
      page: currentPage.value,
      page_size: pageSize,
    })
    posts.value = resp.results
    total.value = resp.count
  } finally {
    if (showLoading) loading.value = false
  }
}

function loadPage(page: number) {
  currentPage.value = page
  pendingNewPostCount.value = 0
  loadPosts()
}

function refreshNewPosts(showLoading = true) {
  pendingNewPostCount.value = 0
  currentPage.value = 1
  loadPosts(showLoading)
}

function isCurrentUserPostEvent(payload: Record<string, unknown>) {
  return payload.author_account_id === authStore.currentUser?.account_id
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function truncate(text: string, max: number) {
  return text.length > max ? text.slice(0, max) + '...' : text
}

onMounted(() => loadPosts())
useRealtimeEvent((event) => {
  if (event.type === 'post.created') {
    if (isCurrentUserPostEvent(event.payload)) {
      refreshNewPosts(false)
      return
    }
    pendingNewPostCount.value += 1
    return
  }
  if (event.type === 'post.updated' || event.type === 'comment.created') {
    loadPosts(false)
  }
})
</script>

<style scoped>
.feed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.feed-header h1 {
  margin: 0;
}
.category-filter {
  margin-bottom: 20px;
}
.new-post-alert {
  margin-bottom: 16px;
  cursor: pointer;
}
.post-card {
  padding: 20px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.post-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.post-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
}
.post-author {
  font-weight: 600;
}
.post-time {
  color: #9ca3af;
  flex: 1;
}
.post-content {
  line-height: 1.7;
  color: #374151;
}
.post-images {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.post-thumb {
  width: 120px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
}
.post-meta {
  margin-top: 12px;
  font-size: 13px;
  color: #9ca3af;
}
.pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>
