<template>
  <section class="page-card">
    <h1>活动管理</h1>
    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="活动状态" clearable @change="load">
        <el-option label="筹备中" value="preparing" />
        <el-option label="报名中" value="open" />
        <el-option label="已截止" value="closed" />
        <el-option label="已结束" value="finished" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="activities" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="initiator_name" label="发起人" width="100" />
      <el-table-column prop="status" label="状态" width="80" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-select v-model="statusMap[row.id]" size="small" style="width:100px" @change="(v: string) => changeStatus(row.id, v)">
            <el-option label="筹备中" value="preparing" />
            <el-option label="报名中" value="open" />
            <el-option label="已截止" value="closed" />
            <el-option label="已结束" value="finished" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
          <el-button text size="small" type="danger" @click="removeActivity(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { deleteActivity, fetchAdminActivities, updateActivityStatus, type AdminActivityItem } from '@/api/admin'

const loading = ref(false)
const statusFilter = ref('')
const activities = ref<AdminActivityItem[]>([])
const statusMap = reactive<Record<number, string>>({})

async function load() {
  loading.value = true
  try {
    const resp = await fetchAdminActivities({ status: statusFilter.value || undefined })
    activities.value = resp.results
    for (const a of activities.value) statusMap[a.id] = a.status
  } finally { loading.value = false }
}

async function changeStatus(id: number, status: string) {
  try {
    await updateActivityStatus(id, status)
    ElMessage.success('状态已更新')
  } catch { ElMessage.error('操作失败') }
}

async function removeActivity(id: number) {
  try {
    await ElMessageBox.confirm('确定删除此活动？', '确认', { type: 'warning' })
    await deleteActivity(id, '管理员删除')
    ElMessage.success('已删除')
    await load()
  } catch { /* cancelled */ }
}

onMounted(() => load())
</script>

<style scoped>
.filter-bar { margin-bottom: 16px; }
</style>
