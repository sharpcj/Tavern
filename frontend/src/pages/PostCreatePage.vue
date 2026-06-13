<template>
  <section class="page-card">
    <h1>发布动态</h1>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="内容" prop="content">
        <el-input v-model="form.content" type="textarea" :rows="6" placeholder="分享你的近况、回忆或想法..." />
      </el-form-item>
      <el-form-item label="图片（选填）">
        <input type="file" accept="image/jpeg,image/png,image/gif,image/webp" multiple @change="onFileChange" />
        <div class="field-tip">可一次选择多张图片，仅支持 JPG、PNG、GIF、WebP，单张不超过 10 MB。</div>
        <div v-if="selectedFiles.length" class="selected-files">
          <el-tag v-for="file in selectedFiles" :key="`${file.name}-${file.size}`" closable @close="removeFile(file)">
            {{ file.name }}
          </el-tag>
        </div>
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="分类" prop="category">
            <el-select v-model="form.category" placeholder="选择分类">
              <el-option v-for="cat in POST_CATEGORIES" :key="cat.value" :label="cat.label" :value="cat.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="展示身份" prop="display_mode">
            <el-radio-group v-model="form.display_mode">
              <el-radio value="real_name">真实姓名</el-radio>
              <el-radio value="nickname">昵称</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>
      <el-button type="primary" :loading="submitting" native-type="submit">发布</el-button>
      <el-button @click="$router.back()">取消</el-button>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createPost, POST_CATEGORIES, type PostCreatePayload } from '@/api/posts'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const selectedFiles = ref<File[]>([])

const allowedImageTypes = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp'])

const form = reactive<PostCreatePayload>({
  content: '',
  uploaded_images: [],
  category: 'chat',
  display_mode: 'real_name',
})

const rules: FormRules<PostCreatePayload> = {
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  const validFiles: File[] = []
  for (const file of files) {
    if (!allowedImageTypes.has(file.type)) {
      ElMessage.warning(`${file.name} 不是支持的图片格式`)
      continue
    }
    validFiles.push(file)
  }
  selectedFiles.value = validFiles
  form.uploaded_images = validFiles
  input.value = ''
}

function removeFile(file: File) {
  selectedFiles.value = selectedFiles.value.filter(item => item !== file)
  form.uploaded_images = selectedFiles.value
}

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    await createPost({ ...form, uploaded_images: selectedFiles.value })
    ElMessage.success('发布成功')
    router.push('/')
  } catch {
    ElMessage.error('发布失败，请确认图片格式正确且单张不超过 10 MB')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.field-tip { margin-top: 6px; color: #6b7280; font-size: 13px; }
.selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
</style>
