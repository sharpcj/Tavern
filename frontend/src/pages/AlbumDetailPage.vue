<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else-if="album">
      <div class="feed-header">
        <div>
          <el-tag type="info">{{ album.category_display }}</el-tag>
          <h1>{{ album.title }}</h1>
          <p class="muted">创建人：{{ album.creator_name }} · {{ album.photo_count }} 张照片</p>
        </div>
        <el-button type="primary" @click="showUpload = true">上传照片</el-button>
      </div>
      <p class="description">{{ album.description || '暂无说明' }}</p>

      <el-empty v-if="album.photos.length === 0" description="这个相册还没有照片" />
      <div class="photo-grid">
        <div v-for="photo in album.photos" :key="photo.id" class="photo-card" @click="$router.push(`/photos/${photo.id}`)">
          <img :src="photo.image_url" :alt="photo.caption" />
          <div class="photo-caption">{{ photo.caption || '暂无说明' }}</div>
        </div>
      </div>

      <el-dialog v-model="showUpload" title="上传照片" width="500px">
        <el-form label-position="top">
          <el-form-item label="图片">
            <input type="file" accept="image/jpeg,image/png,image/gif,image/webp" @change="onFileChange" />
            <div class="field-tip">仅支持 JPG、PNG、GIF、WebP 图片，单张不超过 10 MB。</div>
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="uploadForm.caption" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="展示身份">
            <el-radio-group v-model="uploadForm.display_mode">
              <el-radio value="real_name">真实姓名</el-radio>
              <el-radio value="nickname">昵称</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showUpload = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitUpload">上传</el-button>
        </template>
      </el-dialog>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchAlbumDetail, uploadPhoto, type AlbumDetail } from '@/api/albums'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'

const route = useRoute()
const loading = ref(true)
const submitting = ref(false)
const showUpload = ref(false)
const album = ref<AlbumDetail | null>(null)
const selectedFile = ref<File | null>(null)
const uploadForm = reactive({ caption: '', display_mode: 'real_name' })

const allowedImageTypes = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp'])

async function load() {
  loading.value = true
  try { album.value = await fetchAlbumDetail(Number(route.params.id)) }
  finally { loading.value = false }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  if (!file) {
    selectedFile.value = null
    return
  }
  if (!allowedImageTypes.has(file.type)) {
    selectedFile.value = null
    input.value = ''
    ElMessage.warning('只能上传 JPG、PNG、GIF 或 WebP 图片')
    return
  }
  selectedFile.value = file
}

async function submitUpload() {
  if (!album.value || !selectedFile.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  submitting.value = true
  try {
    await uploadPhoto(album.value.id, { image: selectedFile.value, caption: uploadForm.caption, display_mode: uploadForm.display_mode })
    ElMessage.success('照片已上传')
    showUpload.value = false
    selectedFile.value = null
    uploadForm.caption = ''
    await load()
  } catch {
    ElMessage.error('上传失败，请确认文件是有效图片且不超过 10 MB')
  } finally { submitting.value = false }
}

onMounted(() => load())
useRealtimeEvent((event) => {
  if (event.type === 'album.photo.created' && Number(event.payload.album_id) === Number(route.params.id)) {
    load()
  }
})
</script>

<style scoped>
.feed-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.feed-header h1 { margin: 8px 0; }
.description { color: #4b5563; line-height: 1.7; white-space: pre-wrap; }
.photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 16px; }
.photo-card { border-radius: 10px; overflow: hidden; border: 1px solid #e5e7eb; cursor: pointer; background: #fff; }
.photo-card img { width: 100%; height: 150px; object-fit: cover; display: block; }
.photo-caption { padding: 8px; color: #4b5563; font-size: 13px; }
.field-tip { margin-top: 6px; color: #6b7280; font-size: 13px; }
</style>
