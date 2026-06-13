<template>
  <section class="page-card">
    <h1>发布动态</h1>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="内容" prop="content">
        <el-input v-model="form.content" type="textarea" :rows="6" placeholder="分享你的近况、回忆或想法..." />
      </el-form-item>
      <el-form-item label="图片链接（选填，每行一个）">
        <el-input v-model="imageText" type="textarea" :rows="3" placeholder="https://example.com/photo1.jpg" />
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
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createPost, POST_CATEGORIES, type PostCreatePayload } from '@/api/posts'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const imageText = ref('')

const form = reactive<PostCreatePayload>({
  content: '',
  images: [],
  category: 'chat',
  display_mode: 'real_name',
})

const rules: FormRules<PostCreatePayload> = {
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

const parsedImages = computed(() =>
  imageText.value
    .split('\n')
    .map(s => s.trim())
    .filter(s => s.startsWith('http://') || s.startsWith('https://'))
)

async function submit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    await createPost({ ...form, images: parsedImages.value })
    ElMessage.success('发布成功')
    router.push('/')
  } catch {
    ElMessage.error('发布失败')
  } finally {
    submitting.value = false
  }
}
</script>
