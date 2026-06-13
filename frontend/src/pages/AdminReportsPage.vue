<template>
  <section class="page-card">
    <h1>举报处理</h1>
    <el-radio-group v-model="activeStatus" class="filter-bar" @change="loadReports">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="pending">待处理</el-radio-button>
      <el-radio-button value="resolved">已处理</el-radio-button>
      <el-radio-button value="ignored">已忽略</el-radio-button>
    </el-radio-group>

    <el-table v-loading="loading" :data="reports" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="reporter_name" label="举报人" width="120" />
      <el-table-column prop="target_type" label="对象" width="150" />
      <el-table-column prop="target_label" label="内容摘要" />
      <el-table-column prop="reason_display" label="原因" width="140" />
      <el-table-column prop="status_display" label="状态" width="100" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button text type="primary" size="small" :disabled="row.status === 'resolved' || row.status === 'ignored'" @click="openHandle(row)">处理</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="处理举报" width="480px">
      <div v-if="selectedReport" class="report-detail">
        <p><strong>举报对象：</strong>{{ selectedReport.target_type }} #{{ selectedReport.object_id }}</p>
        <p><strong>内容摘要：</strong>{{ selectedReport.target_label }}</p>
        <p><strong>举报说明：</strong>{{ selectedReport.description || '无' }}</p>
      </div>
      <el-form label-position="top">
        <el-form-item label="处理动作">
          <el-select v-model="handleForm.action_type" style="width:100%">
            <el-option v-for="item in MODERATION_ACTIONS" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input v-model="handleForm.reason" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitHandle">确认处理</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { fetchAdminReports, handleReport, MODERATION_ACTIONS, type ReportItem } from '@/api/reports'

const loading = ref(false)
const submitting = ref(false)
const reports = ref<ReportItem[]>([])
const activeStatus = ref('pending')
const dialogVisible = ref(false)
const selectedReport = ref<ReportItem | null>(null)
const handleForm = reactive({ action_type: 'ignore', reason: '' })

async function loadReports() {
  loading.value = true
  try {
    const resp = await fetchAdminReports({ status: activeStatus.value || undefined, page_size: 50 })
    reports.value = resp.results
  } finally { loading.value = false }
}

function openHandle(report: ReportItem) {
  selectedReport.value = report
  handleForm.action_type = 'ignore'
  handleForm.reason = ''
  dialogVisible.value = true
}

async function submitHandle() {
  if (!selectedReport.value) return
  submitting.value = true
  try {
    await handleReport(selectedReport.value.id, { ...handleForm })
    ElMessage.success('举报已处理')
    dialogVisible.value = false
    await loadReports()
  } finally { submitting.value = false }
}

onMounted(() => loadReports())
</script>

<style scoped>
.filter-bar { margin: 12px 0 16px; }
.report-detail { color: #4b5563; line-height: 1.7; }
</style>
