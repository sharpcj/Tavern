<template>
  <section class="page-card">
    <h1>创建相册</h1>
    <p class="muted">相册内容仅对审核通过的同学开放。上传涉及他人的照片前，请尊重当事人的感受。</p>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="分类" prop="category">
        <el-select v-model="form.category" style="width: 100%">
          <el-option v-for="cat in ALBUM_CATEGORIES" :key="cat.value" :label="cat.label" :value="cat.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="说明">
        <el-input v-model="form.description" type="textarea" :rows="4" />
      </el-form-item>
      <el-form-item label="关联活动 ID（选填）">
        <el-input-number v-model="activityId" :min="1" />
      </el-form-item>

      <el-button type="primary" :loading="submitting" native-type="submit">创建</el-button>
      <el-button @click="$router.back()">取消</el-button>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ALBUM_CATEGORIES, createAlbum, type AlbumPayload } from '@/api/albums'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const activityId = ref<number | undefined>()

const form = reactive<AlbumPayload>({ title: '', description: '', category: 'memory', activity: null })
const rules: FormRules<AlbumPayload> = {
  title: [{ required: true, message: '请输入标题' }],
  category: [{ required: true, message: '请选择分类' }],
}

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const album = await createAlbum({ ...form, activity: activityId.value ?? null })
    ElMessage.success('相册已创建')
    router.push(`/albums/${album.id}`)
  } finally { submitting.value = false }
}
</script>
