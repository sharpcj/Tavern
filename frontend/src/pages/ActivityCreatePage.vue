<template>
  <section class="page-card">
    <h1>发起活动</h1>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="活动类型" prop="activity_type">
        <el-radio-group v-model="form.activity_type">
          <el-radio v-for="t in ACTIVITY_TYPES" :key="t.value" :value="t.value">{{ t.label }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="活动标题" />
      </el-form-item>
      <el-form-item label="说明" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="4" placeholder="活动详细说明" />
      </el-form-item>

      <template v-if="form.activity_type === 'gathering'">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="地点"><el-input v-model="form.location" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="开始时间" prop="start_time"><el-input v-model="form.start_time" type="datetime-local" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="人数上限"><el-input-number v-model="form.max_participants" :min="1" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item label="报名截止时间" prop="deadline">
              <el-input
                v-model="form.deadline"
                type="datetime-local"
                :disabled="!form.start_time"
                :min="deadlineMin"
                placeholder="请先选择开始时间"
              />
              <div class="field-tip">截止时间必须晚于开始时间。</div>
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <template v-if="form.activity_type === 'voting'">
        <el-form-item label="允许多选"><el-switch v-model="form.is_multi_choice" /></el-form-item>
        <el-form-item label="展示投票参与人"><el-switch v-model="form.show_voter_names" /></el-form-item>
        <el-form-item label="允许修改投票"><el-switch v-model="form.allow_vote_change" /></el-form-item>
        <el-form-item label="截止时间"><el-input v-model="form.deadline" type="datetime-local" /></el-form-item>
        <el-form-item label="投票选项">
          <div v-for="(opt, i) in voteOptionTexts" :key="i" class="vote-option-row">
            <el-input v-model="voteOptionTexts[i]" :placeholder="`选项 ${i + 1}`" />
            <el-button v-if="voteOptionTexts.length > 2" @click="voteOptionTexts.splice(i, 1)">删除</el-button>
          </div>
          <el-button @click="voteOptionTexts.push('')">添加选项</el-button>
        </el-form-item>
      </template>

      <template v-if="form.activity_type === 'chain'">
        <el-form-item label="截止时间"><el-input v-model="form.deadline" type="datetime-local" /></el-form-item>
      </template>

      <el-form-item label="联系人信息"><el-input v-model="form.contact_info" placeholder="选填" /></el-form-item>

      <div class="form-actions">
        <el-button type="primary" :loading="submitting" native-type="submit">发布活动</el-button>
        <el-button @click="$router.back()">取消</el-button>
      </div>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createActivity, ACTIVITY_TYPES, type ActivityCreatePayload } from '@/api/activities'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const voteOptionTexts = ref(['', ''])

const form = reactive<ActivityCreatePayload>({
  title: '', activity_type: 'gathering', description: '',
  location: '', start_time: '', deadline: '',
  max_participants: undefined, allow_guests: false, contact_info: '',
  is_multi_choice: false, show_voter_names: false, allow_vote_change: true,
})
const deadlineMin = computed(() => form.start_time || undefined)

const rules: FormRules<ActivityCreatePayload> = {
  title: [{ required: true, message: '请输入标题' }],
  activity_type: [{ required: true }],
  description: [{ required: true, message: '请输入说明' }],
  start_time: [{ validator: validateGatheringStartTime, trigger: 'change' }],
  deadline: [{ validator: validateGatheringDeadline, trigger: 'change' }],
}

watch(() => form.start_time, (startTime) => {
  if (form.deadline && startTime && new Date(form.deadline) <= new Date(startTime)) {
    form.deadline = ''
  }
})

function validateGatheringStartTime(_rule: unknown, value: string | undefined, callback: (error?: Error) => void) {
  if (form.activity_type === 'gathering' && !value) {
    callback(new Error('请先选择开始时间'))
    return
  }
  callback()
}

function validateGatheringDeadline(_rule: unknown, value: string | undefined, callback: (error?: Error) => void) {
  if (form.activity_type !== 'gathering') {
    callback()
    return
  }
  if (!form.start_time) {
    callback(new Error('请先选择开始时间'))
    return
  }
  if (!value) {
    callback(new Error('请选择报名截止时间'))
    return
  }
  if (new Date(value) <= new Date(form.start_time)) {
    callback(new Error('截止时间必须晚于开始时间'))
    return
  }
  callback()
}

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload = { ...form }
    if (form.activity_type === 'voting') {
      payload.vote_options = voteOptionTexts.value.filter(t => t.trim())
      payload.start_time = undefined
      payload.max_participants = undefined
      payload.allow_guests = undefined
    } else if (form.activity_type === 'chain') {
      payload.start_time = undefined
      payload.max_participants = undefined
      payload.allow_guests = undefined
      payload.is_multi_choice = undefined
      payload.show_voter_names = undefined
      payload.allow_vote_change = undefined
    }
    if (form.activity_type === 'gathering' && form.start_time) payload.start_time = new Date(form.start_time).toISOString()
    if (form.deadline) payload.deadline = new Date(form.deadline).toISOString()
    await createActivity(payload)
    ElMessage.success('活动已发布')
    router.push('/activities')
  } catch { ElMessage.error('发布失败') }
  finally { submitting.value = false }
}
</script>

<style scoped>
.field-tip { margin-top: 4px; color: #6b7280; font-size: 13px; line-height: 1.5; }
.vote-option-row { display: flex; gap: 8px; margin-bottom: 8px; }
.form-actions { display: flex; gap: 8px; }

@media (max-width: 640px) {
  :deep(.el-radio-group) { display: grid; gap: 8px; }
  :deep(.el-input-number) { width: 100%; }
  .vote-option-row { flex-direction: column; }
  .vote-option-row .el-button { width: 100%; margin-left: 0; }
  .form-actions { flex-direction: column; }
  .form-actions .el-button { width: 100%; margin-left: 0; }
}
</style>
