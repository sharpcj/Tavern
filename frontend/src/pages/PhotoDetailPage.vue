<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else-if="photo">
      <div class="photo-toolbar">
        <el-button :disabled="!previousPhoto" @click="goToPhoto(previousPhoto?.id)">
          {{ previousPhoto ? '上一张' : '已是第一张' }}
        </el-button>
        <span class="photo-position">{{ photoPositionText }}</span>
        <el-button :disabled="!nextPhoto" @click="goToPhoto(nextPhoto?.id)">
          {{ nextPhoto ? '下一张' : '已是最后一张' }}
        </el-button>
      </div>

      <div class="photo-view">
        <img :src="photo.image_url" :alt="photo.caption || '相册照片'" />
      </div>
      <p class="caption">{{ photo.caption || '暂无说明' }}</p>
      <p class="muted">上传人：{{ photo.display_name }} · {{ formatTime(photo.created_at) }}</p>
      <ReportButton target-type="photo" :object-id="photo.id" />

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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createPhotoComment, fetchAlbumDetail, fetchPhotoDetail, type PhotoDetail, type PhotoListItem } from '@/api/albums'
import ReportButton from '@/components/ReportButton.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const submitting = ref(false)
const photo = ref<PhotoDetail | null>(null)
const albumPhotos = ref<PhotoListItem[]>([])
const commentForm = reactive({ content: '', display_mode: 'real_name' })

const currentIndex = computed(() => {
  if (!photo.value) return -1
  return albumPhotos.value.findIndex(item => item.id === photo.value?.id)
})

const previousPhoto = computed(() => {
  const index = currentIndex.value
  if (index <= 0) return null
  return albumPhotos.value[index - 1]
})

const nextPhoto = computed(() => {
  const index = currentIndex.value
  if (index < 0 || index >= albumPhotos.value.length - 1) return null
  return albumPhotos.value[index + 1]
})

const photoPositionText = computed(() => {
  const index = currentIndex.value
  if (index < 0 || albumPhotos.value.length === 0) return ''
  return `${index + 1} / ${albumPhotos.value.length}`
})

async function load() {
  loading.value = true
  try {
    const detail = await fetchPhotoDetail(Number(route.params.id))
    photo.value = detail
    const album = await fetchAlbumDetail(detail.album)
    albumPhotos.value = album.photos
  } finally { loading.value = false }
}

function goToPhoto(photoId?: number) {
  if (!photoId) return
  router.push(`/photos/${photoId}`)
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
watch(() => route.params.id, () => load())
</script>

<style scoped>
.photo-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 16px;
}
.photo-position {
  min-width: 64px;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
}
.photo-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 320px;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: auto;
}
.photo-view img {
  display: block;
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.caption { margin-top: 16px; white-space: pre-wrap; line-height: 1.7; }
.comment-box { margin-top: 24px; }
.comment-item { padding: 12px 0; border-top: 1px solid #e5e7eb; }
.comment-meta { color: #6b7280; font-size: 13px; margin-bottom: 4px; }
.empty-comments { color: #9ca3af; padding: 12px 0; }
</style>
