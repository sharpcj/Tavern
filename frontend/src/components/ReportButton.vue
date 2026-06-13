<template>
  <el-button text size="small" type="warning" @click="dialogVisible = true">举报</el-button>
  <el-dialog v-model="dialogVisible" title="举报内容" width="420px">
    <el-form label-position="top">
      <el-form-item label="举报理由">
        <el-select v-model="form.reason" style="width: 100%">
          <el-option v-for="item in REPORT_REASONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="补充说明">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选，说明具体情况" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">提交举报</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { createReport, REPORT_REASONS, type ReportTargetType } from '@/api/reports'

const props = defineProps<{
  targetType: ReportTargetType
  objectId: number
}>()

const dialogVisible = ref(false)
const submitting = ref(false)
const form = reactive({ reason: 'other', description: '' })

async function submit() {
  submitting.value = true
  try {
    await createReport({ target_type: props.targetType, object_id: props.objectId, reason: form.reason, description: form.description })
    ElMessage.success('举报已提交，管理员会尽快处理')
    dialogVisible.value = false
    form.reason = 'other'
    form.description = ''
  } finally {
    submitting.value = false
  }
}
</script>
