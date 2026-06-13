<template>
  <section class="page-card">
    <div class="feed-header">
      <h1>班级活动</h1>
      <el-button type="primary" @click="$router.push('/activities/create')">发起活动</el-button>
    </div>

    <el-radio-group v-model="activeStatus" class="filter-bar" @change="load">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="open">报名中</el-radio-button>
      <el-radio-button value="closed">已截止</el-radio-button>
      <el-radio-button value="finished">已结束</el-radio-button>
    </el-radio-group>

    <div v-loading="loading">
      <el-empty v-if="!loading && activities.length === 0" description="暂无活动" />
      <div v-for="act in activities" :key="act.id" class="activity-card" @click="$router.push(`/activities/${act.id}`)">
        <div class="card-header">
          <el-tag :type="typeTag(act.activity_type)" size="small">{{ act.activity_type_display }}</el-tag>
          <el-tag :type="statusTag(act.status)" size="small">{{ act.status_display }}</el-tag>
          <span class="card-title">{{ act.title }}</span>
        </div>
        <div class="card-meta">
          <span>发起人：{{ act.initiator_name }}</span>
          <span v-if="act.location">地点：{{ act.location }}</span>
          <span v-if="act.start_time">时间：{{ formatTime(act.start_time) }}</span>
          <span v-if="act.activity_type === 'gathering'">{{ act.signup_count }} 人已报名</span>
        </div>
      </div>
    </div>

    <el-pagination v-if="total > pageSize" class="pagination" :current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="loadPage" />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchActivities, type ActivityListItem } from '@/api/activities'

const loading = ref(false)
const activities = ref<ActivityListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const activeStatus = ref('')

async function load() {
  loading.value = true
  try {
    const resp = await fetchActivities({ status: activeStatus.value || undefined, page: currentPage.value, page_size: pageSize })
    activities.value = resp.results
    total.value = resp.count
  } finally { loading.value = false }
}

function loadPage(p: number) { currentPage.value = p; load() }

function typeTag(t: string) { return t === 'gathering' ? 'success' : t === 'voting' ? 'warning' : 'info' }
function statusTag(s: string) { return s === 'open' ? 'success' : s === 'closed' ? 'info' : s === 'finished' ? '' : 'danger' }

function formatTime(iso: string) { return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }

onMounted(() => load())
</script>

<style scoped>
.feed-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.feed-header h1 { margin: 0; }
.filter-bar { margin-bottom: 20px; }
.activity-card { padding: 16px; margin-bottom: 10px; border: 1px solid #e5e7eb; border-radius: 12px; cursor: pointer; transition: box-shadow 0.2s; }
.activity-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.card-title { font-weight: 600; font-size: 16px; }
.card-meta { display: flex; gap: 16px; font-size: 13px; color: #6b7280; }
.pagination { margin-top: 20px; justify-content: center; }
</style>
