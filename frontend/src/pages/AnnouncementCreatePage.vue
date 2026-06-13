<template>
  <section class="page-card">
    <h1>发布公告</h1>
    <p class="muted">公告仅管理员和管理会员可发布，用于班级重要事项。</p>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="内容" prop="content">
        <el-input v-model="form.content" type="textarea" :rows="8" />
      </el-form-item>
      <el-form-item label="状态">
        <el-radio-group v-model="form.status">
          <el-radio value="published">发布</el-radio>
          <el-radio value="hidden">隐藏</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="置顶">
        <el-switch v-model="form.is_pinned" />
      </el-form-item>
      <el-form-item label="需要已读确认">
        <el-switch v-model="form.require_read_confirm" />
      </el-form-item>
      <el-form-item label="有效期至">
        <el-input v-model="expiresAtInput" type="datetime-local" />
      </el-form-item>

      <el-button type="primary" :loading="submitting" native-type="submit">发布公告</el-button>
      <el-button @click="$router.back()">取消</el-button>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createAnnouncement, type AnnouncementPayload } from '@/api/announcements'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const expiresAtInput = ref('')

const form = reactive<AnnouncementPayload>({
  title: '',
  content: '',
  is_pinned: false,
  require_read_confirm: false,
  expires_at: null,
  status: 'published',
})

const rules: FormRules<AnnouncementPayload> = {
  title: [{ required: true, message: '请输入标题' }],
  content: [{ required: true, message: '请输入内容' }],
}

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload = { ...form, expires_at: expiresAtInput.value ? new Date(expiresAtInput.value).toISOString() : null }
    const created = await createAnnouncement(payload)
    ElMessage.success('公告已发布')
    router.push(`/announcements/${created.id}`)
  } finally {
    submitting.value = false
  }
}
</script>
