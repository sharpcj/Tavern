<template>
  <section class="page-card">
    <h1>用户审核</h1>
    <el-table v-loading="loading" :data="users" stripe>
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column prop="high_school" label="高中" width="100" />
      <el-table-column prop="high_school_class" label="班级" width="80" />
      <el-table-column prop="extra_info" label="补充信息" />
      <el-table-column prop="review_status_display" label="审核状态" width="100" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button text size="small" type="success" @click="review(row.account_id, 'approve')">通过</el-button>
          <el-button text size="small" type="danger" @click="review(row.account_id, 'reject')">拒绝</el-button>
          <el-button text size="small" type="warning" @click="review(row.account_id, 'need_more_info')">补充资料</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { fetchPendingReviews, reviewUser, type AdminUser } from '@/api/admin'

const loading = ref(false)
const users = ref<AdminUser[]>([])

async function load() {
  loading.value = true
  try {
    const resp = await fetchPendingReviews()
    users.value = resp.results
  } finally { loading.value = false }
}

async function review(accountId: string, action: string) {
  try {
    await reviewUser(accountId, { action })
    ElMessage.success('审核完成')
    await load()
  } catch { ElMessage.error('操作失败') }
}

onMounted(() => load())
</script>
