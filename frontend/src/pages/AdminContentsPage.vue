<template>
  <section class="page-card">
    <h1>内容管理</h1>
    <el-tabs v-model="activeTab" @tab-change="loadTab">
      <el-tab-pane label="动态" name="posts" />
      <el-tab-pane label="评论" name="comments" />
      <el-tab-pane label="照片" name="photos" />
      <el-tab-pane label="相册" name="albums" />
    </el-tabs>

    <el-table v-loading="loading" :data="items" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="作者" width="100">
        <template #default="{ row }">{{ row.author_name || row.uploader_name || row.creator_name }}</template>
      </el-table-column>
      <el-table-column label="内容">
        <template #default="{ row }">{{ row.content || row.caption || row.title || '' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button text size="small" type="warning" @click="hideItem(row.id)">隐藏</el-button>
          <el-button text size="small" type="danger" @click="deleteItem(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  deleteComment, deletePost, fetchAdminAlbums, fetchAdminComments,
  fetchAdminPhotos, fetchAdminPosts, hideAlbum, hideComment, hidePhoto, hidePost,
  type AdminContentItem,
} from '@/api/admin'

const loading = ref(false)
const activeTab = ref('posts')
const items = ref<AdminContentItem[]>([])

async function loadTab() {
  loading.value = true
  try {
    let resp
    switch (activeTab.value) {
      case 'posts': resp = await fetchAdminPosts(); break
      case 'comments': resp = await fetchAdminComments(); break
      case 'photos': resp = await fetchAdminPhotos(); break
      case 'albums': resp = await fetchAdminAlbums(); break
    }
    items.value = resp?.results ?? []
  } finally { loading.value = false }
}

async function hideItem(id: number) {
  try {
    await ElMessageBox.confirm('确定隐藏？', '确认', { type: 'warning' })
    switch (activeTab.value) {
      case 'posts': await hidePost(id); break
      case 'comments': await hideComment(id); break
      case 'photos': await hidePhoto(id); break
      case 'albums': await hideAlbum(id); break
    }
    ElMessage.success('已隐藏')
    await loadTab()
  } catch { /* cancelled */ }
}

async function deleteItem(id: number) {
  try {
    await ElMessageBox.confirm('确定删除？此操作不可撤销。', '确认', { type: 'warning' })
    switch (activeTab.value) {
      case 'posts': await deletePost(id); break
      case 'comments': await deleteComment(id); break
    }
    ElMessage.success('已删除')
    await loadTab()
  } catch { /* cancelled */ }
}

onMounted(() => loadTab())
</script>
