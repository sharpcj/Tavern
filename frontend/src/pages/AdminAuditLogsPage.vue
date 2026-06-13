<template>
  <section class="page-card">
    <h1>操作日志</h1>
    <el-table v-loading="loading" :data="logs" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="actor_name" label="操作者" width="100" />
      <el-table-column prop="action" label="操作类型" width="140" />
      <el-table-column prop="target_type" label="对象类型" width="140" />
      <el-table-column prop="target_object_id" label="对象ID" width="80" />
      <el-table-column prop="reason" label="原因" />
      <el-table-column label="时间" width="160">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient } from '@/api/client'

interface AuditLogItem {
  id: number
  actor_name: string
  action: string
  target_type: string | null
  target_object_id: number | null
  reason: string
  created_at: string
}

const loading = ref(false)
const logs = ref<AuditLogItem[]>([])

async function load() {
  loading.value = true
  try {
    const resp = await apiClient.get<{ count: number; results: AuditLogItem[] }>('/v1/admin/audit-logs/')
    logs.value = resp.data.results
  } finally { loading.value = false }
}

onMounted(() => load())
</script>
