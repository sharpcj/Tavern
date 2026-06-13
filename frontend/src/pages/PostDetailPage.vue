<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="6" animated />
    <template v-else-if="post">
      <div class="post-header">
        <el-tag v-if="post.is_pinned" type="danger" size="small">置顶</el-tag>
        <h1>{{ post.display_name }} 的动态</h1>
        <div class="post-meta">
          <el-tag size="small">{{ post.category_display }}</el-tag>
          <span class="post-time">{{ formatTime(post.created_at) }}</span>
          <span v-if="isAuthor" class="post-actions">
            <el-button text size="small" @click="startEdit">编辑</el-button>
            <el-button text size="small" type="danger" @click="doDelete">删除</el-button>
          </span>
          <ReportButton target-type="post" :object-id="post.id" />
        </div>
      </div>

      <div v-if="editing" class="edit-area">
        <el-input v-model="editContent" type="textarea" :rows="4" />
        <div style="margin-top:8px">
          <el-button size="small" type="primary" :loading="saving" @click="saveEdit">保存</el-button>
          <el-button size="small" @click="editing = false">取消</el-button>
        </div>
      </div>
      <div v-else class="post-body">{{ post.content }}</div>

      <div v-if="post.images.length" class="post-images">
        <img v-for="(url, i) in post.images" :key="i" :src="url" class="post-image" />
      </div>

      <el-divider />

      <h2>评论 ({{ comments.length }})</h2>
      <div class="comment-form">
        <el-input v-model="newComment" type="textarea" :rows="2" placeholder="发表评论..." />
        <div class="comment-form-actions">
          <el-radio-group v-model="commentMode" size="small">
            <el-radio value="real_name">真实姓名</el-radio>
            <el-radio value="nickname">昵称</el-radio>
          </el-radio-group>
          <el-button type="primary" size="small" :loading="postingComment" @click="submitComment">发表</el-button>
        </div>
      </div>

      <div v-if="comments.length === 0" class="muted" style="margin-top:16px">暂无评论</div>
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-header">
          <span class="comment-author">{{ comment.display_name }}</span>
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <el-button v-if="comment.author_id === authStore.currentUser?.account_id" text size="small" type="danger" @click="deleteCommentItem(comment.id)">删除</el-button>
          <ReportButton target-type="comment" :object-id="comment.id" />
          <el-button text size="small" @click="startReply(comment.id)">回复</el-button>
        </div>
        <div class="comment-content">{{ comment.content }}</div>

        <div v-if="replyingTo === comment.id" class="reply-form">
          <el-input v-model="replyContent" type="textarea" :rows="2" placeholder="回复..." />
          <div class="comment-form-actions">
            <el-radio-group v-model="commentMode" size="small">
              <el-radio value="real_name">真实姓名</el-radio>
              <el-radio value="nickname">昵称</el-radio>
            </el-radio-group>
            <el-button size="small" type="primary" :loading="postingReply" @click="submitReply(comment.id)">回复</el-button>
            <el-button size="small" @click="replyingTo = null">取消</el-button>
          </div>
        </div>

        <div v-if="comment.replies.length" class="replies">
          <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
            <span class="comment-author">{{ reply.display_name }}</span>
            <span class="comment-time">{{ formatTime(reply.created_at) }}</span>
            <el-button v-if="reply.author_id === authStore.currentUser?.account_id" text size="small" type="danger" @click="deleteCommentItem(reply.id)">删除</el-button>
            <ReportButton target-type="comment" :object-id="reply.id" />
            <div class="comment-content">{{ reply.content }}</div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  createComment,
  deleteComment,
  deletePost,
  fetchComments,
  fetchPostDetail,
  replyToComment,
  updatePost,
  type CommentItem,
  type PostDetail,
} from '@/api/posts'
import { useAuthStore } from '@/stores/auth'
import ReportButton from '@/components/ReportButton.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const post = ref<PostDetail | null>(null)
const comments = ref<CommentItem[]>([])
const newComment = ref('')
const commentMode = ref<'real_name' | 'nickname'>('real_name')
const postingComment = ref(false)
const replyingTo = ref<number | null>(null)
const replyContent = ref('')
const postingReply = ref(false)
const editing = ref(false)
const editContent = ref('')
const saving = ref(false)

const isAuthor = ref(false)

async function load() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    post.value = await fetchPostDetail(id)
    isAuthor.value = post.value.author_id === authStore.currentUser?.account_id
    comments.value = await fetchComments(id)
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  if (!newComment.value.trim()) return
  postingComment.value = true
  try {
    await createComment(post.value!.id, { content: newComment.value, display_mode: commentMode.value })
    newComment.value = ''
    comments.value = await fetchComments(post.value!.id)
  } finally {
    postingComment.value = false
  }
}

function startReply(commentId: number) {
  replyingTo.value = commentId
  replyContent.value = ''
}

async function submitReply(commentId: number) {
  if (!replyContent.value.trim()) return
  postingReply.value = true
  try {
    await replyToComment(commentId, { content: replyContent.value, display_mode: commentMode.value })
    replyingTo.value = null
    comments.value = await fetchComments(post.value!.id)
  } finally {
    postingReply.value = false
  }
}

async function deleteCommentItem(commentId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条评论？', '确认', { type: 'warning' })
    await deleteComment(commentId)
    comments.value = await fetchComments(post.value!.id)
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

function startEdit() {
  editContent.value = post.value!.content
  editing.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    post.value = await updatePost(post.value!.id, { content: editContent.value })
    editing.value = false
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function doDelete() {
  try {
    await ElMessageBox.confirm('确定删除这条动态？', '确认', { type: 'warning' })
    await deletePost(post.value!.id)
    ElMessage.success('已删除')
    router.push('/')
  } catch { /* cancelled */ }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => load())
</script>

<style scoped>
.post-header h1 {
  margin: 8px 0;
  font-size: 22px;
}
.post-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #6b7280;
}
.post-actions {
  margin-left: auto;
}
.post-body {
  line-height: 1.8;
  white-space: pre-wrap;
  color: #1f2937;
}
.post-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.post-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
}
.edit-area {
  margin-bottom: 16px;
}
.comment-form {
  margin: 16px 0;
}
.comment-form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.comment-item {
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.comment-author {
  font-weight: 600;
  font-size: 14px;
}
.comment-time {
  font-size: 12px;
  color: #9ca3af;
  flex: 1;
}
.comment-content {
  line-height: 1.6;
  color: #374151;
}
.replies {
  margin-left: 24px;
  margin-top: 8px;
  padding-left: 12px;
  border-left: 2px solid #e5e7eb;
}
.reply-item {
  padding: 8px 0;
}
.reply-form {
  margin: 8px 0 8px 24px;
}
</style>
