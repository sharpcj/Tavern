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
          <div class="comment-header">
            <span class="comment-author">{{ comment.display_name }}</span>
            <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            <el-button v-if="comment.author_id === authStore.currentUser?.account_id" text size="small" type="danger" @click="deleteCommentItem(comment.id)">删除</el-button>
            <ReportButton target-type="photo_comment" :object-id="comment.id" />
            <el-button text size="small" @click="startReply(comment.id, comment.display_name)">回复</el-button>
          </div>
          <div class="comment-content">{{ comment.content }}</div>

          <div v-if="replyingTo === comment.id" class="reply-form">
            <el-input v-model="replyContent" type="textarea" :rows="2" :placeholder="replyPlaceholder" />
            <div class="comment-form-actions">
              <el-radio-group v-model="commentForm.display_mode" size="small">
                <el-radio value="real_name">真实姓名</el-radio>
                <el-radio value="nickname">昵称</el-radio>
              </el-radio-group>
              <el-button size="small" type="primary" :loading="submittingReply" @click="submitReply(comment.id)">回复</el-button>
              <el-button size="small" @click="cancelReply">取消</el-button>
            </div>
          </div>

          <div v-if="comment.replies.length" class="replies">
            <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
              <div class="comment-header">
                <span class="comment-author">{{ reply.display_name }}</span>
                <span v-if="reply.reply_to_display_name" class="reply-to-text">回复 {{ reply.reply_to_display_name }}</span>
                <span class="comment-time">{{ formatTime(reply.created_at) }}</span>
                <el-button v-if="reply.author_id === authStore.currentUser?.account_id" text size="small" type="danger" @click="deleteCommentItem(reply.id)">删除</el-button>
                <ReportButton target-type="photo_comment" :object-id="reply.id" />
                <el-button text size="small" @click="startReply(reply.id, reply.display_name)">回复</el-button>
              </div>
              <div class="comment-content">{{ reply.content }}</div>

              <div v-if="replyingTo === reply.id" class="reply-form nested-reply-form">
                <el-input v-model="replyContent" type="textarea" :rows="2" :placeholder="replyPlaceholder" />
                <div class="comment-form-actions">
                  <el-radio-group v-model="commentForm.display_mode" size="small">
                    <el-radio value="real_name">真实姓名</el-radio>
                    <el-radio value="nickname">昵称</el-radio>
                  </el-radio-group>
                  <el-button size="small" type="primary" :loading="submittingReply" @click="submitReply(reply.id)">回复</el-button>
                  <el-button size="small" @click="cancelReply">取消</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createPhotoComment,
  deletePhotoComment,
  fetchAlbumDetail,
  fetchPhotoDetail,
  replyToPhotoComment,
  type PhotoDetail,
  type PhotoListItem,
} from '@/api/albums'
import ReportButton from '@/components/ReportButton.vue'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const submitting = ref(false)
const submittingReply = ref(false)
const photo = ref<PhotoDetail | null>(null)
const albumPhotos = ref<PhotoListItem[]>([])
const commentForm = reactive({ content: '', display_mode: 'real_name' as 'real_name' | 'nickname' })
const replyingTo = ref<number | null>(null)
const replyTargetName = ref('')
const replyContent = ref('')

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

const replyPlaceholder = computed(() => (replyTargetName.value ? `回复 ${replyTargetName.value}...` : '回复...'))

async function load(showLoading = true) {
  if (showLoading) loading.value = true
  try {
    const detail = await fetchPhotoDetail(Number(route.params.id))
    photo.value = detail
    const album = await fetchAlbumDetail(detail.album)
    albumPhotos.value = album.photos
  } finally { if (showLoading) loading.value = false }
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

function startReply(commentId: number, targetName: string) {
  replyingTo.value = commentId
  replyTargetName.value = targetName
  replyContent.value = ''
}

function cancelReply() {
  replyingTo.value = null
  replyTargetName.value = ''
  replyContent.value = ''
}

async function submitReply(commentId: number) {
  if (!replyContent.value.trim()) return
  submittingReply.value = true
  try {
    await replyToPhotoComment(commentId, { content: replyContent.value, display_mode: commentForm.display_mode })
    cancelReply()
    await load()
  } finally {
    submittingReply.value = false
  }
}

async function deleteCommentItem(commentId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条评论？', '确认', { type: 'warning' })
    await deletePhotoComment(commentId)
    await load()
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => load())
watch(() => route.params.id, () => load())
useRealtimeEvent((event) => {
  const currentPhotoId = Number(route.params.id)
  if (event.type === 'photo.comment.created' && Number(event.payload.photo_id) === currentPhotoId) {
    load(false)
  }
  if (event.type === 'album.photo.created' && photo.value && Number(event.payload.album_id) === photo.value.album) {
    load(false)
  }
})
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
.comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.comment-author { font-weight: 600; font-size: 14px; }
.reply-to-text { font-size: 13px; color: #6b7280; }
.comment-time { font-size: 12px; color: #9ca3af; flex: 1; }
.comment-content { line-height: 1.6; color: #374151; white-space: pre-wrap; }
.comment-form-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 8px; }
.replies { margin-left: 24px; margin-top: 8px; padding-left: 12px; border-left: 2px solid #e5e7eb; }
.reply-item { padding: 8px 0; }
.reply-form { margin: 8px 0 8px 24px; }
.nested-reply-form { margin-left: 0; }
.empty-comments { color: #9ca3af; padding: 12px 0; }
@media (max-width: 768px) {
  .photo-toolbar { gap: 8px; }
  .photo-toolbar .el-button { padding: 8px 10px; }
  .photo-view { min-height: 220px; padding: 8px; }
  .comment-header,
  .comment-form-actions { flex-wrap: wrap; }
  .comment-time { flex: initial; }
  .replies { margin-left: 8px; padding-left: 10px; }
  .reply-form { margin-left: 0; }
}
</style>
