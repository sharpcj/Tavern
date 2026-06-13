<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else-if="photo">
      <div class="photo-view">
        <img :src="photo.image_url" :alt="photo.caption" />
      </div>
      <p class="caption">{{ photo.caption || '暂无说明' }}</p>
      <p class="muted">上传人：{{ photo.display_name }} · {{ formatTime(photo.created_at) }}</p>

      <div class="comment-box">
        <h2>评论</h2>
        <el-form :model="commentForm" label-position="top" @submit.prevent="submitComment">
          <el-form-item label="评论内容">
            <el-input v-model="commentForm.content" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="展示身份">
            <el-radio-group v-model="commentForm.display_mode">
              <el-radio value="real_name">真实姓名</el-radio>
              <el-radio value="nickname">昵称</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="submitComment">发表评论</el-button>
        </el-form>

        <div v-if="photo.comments.length === 0" class="empty-comments">暂无评论</div>
        <div v-for="comment in photo.comments" :key="comment.id" class="comment-item">
          <div class="comment-meta">{{ comment.display_name }} · {{ formatTime(comment.created_at) }}</div>
          <div>{{ comment.content }}</div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { createPhotoComment, fetchPhotoDetail, type PhotoDetail } from '@/api/albums'

const route = useRoute()
const loading = ref(true)
const submitting = ref(false)
const photo = ref<PhotoDetail | null>(null)
const commentForm = reactive({ content: '', display_mode: 'real_name' })

async function load() {
  loading.value = true
  try { photo.value = await fetchPhotoDetail(Number(route.params.id)) }
  finally { loading.value = false }
}

async function submitComment() {
  if (!photo.value || !commentForm.content.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  submitting.value = true
  try {
    await createPhotoComment(photo.value.id, { ...commentForm })
    ElMessage.success('评论已发布')
    commentForm.content = ''
    await load()
  } finally { submitting.value = false }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => load())
</script>

<style scoped>
.photo-view { display: flex; justify-content: center; background: #111827; border-radius: 12px; overflow: hidden; }
.photo-view img { max-width: 100%; max-height: 70vh; object-fit: contain; }
.caption { margin-top: 16px; white-space: pre-wrap; line-height: 1.7; }
.comment-box { margin-top: 24px; }
.comment-item { padding: 12px 0; border-top: 1px solid #e5e7eb; }
.comment-meta { color: #6b7280; font-size: 13px; margin-bottom: 4px; }
.empty-comments { color: #9ca3af; padding: 12px 0; }
</style>
