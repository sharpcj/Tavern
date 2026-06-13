<template>
  <section class="page-card">
    <div class="feed-header">
      <h1>班级相册</h1>
      <el-button type="primary" @click="$router.push('/albums/create')">创建相册</el-button>
    </div>

    <el-radio-group v-model="activeCategory" class="filter-bar" @change="loadAlbums">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button v-for="cat in ALBUM_CATEGORIES" :key="cat.value" :value="cat.value">{{ cat.label }}</el-radio-button>
    </el-radio-group>

    <div v-loading="loading">
      <el-empty v-if="!loading && albums.length === 0" description="暂无相册" />
      <div class="album-grid">
        <div v-for="album in albums" :key="album.id" class="album-card" @click="$router.push(`/albums/${album.id}`)">
          <div class="cover">
            <img v-if="album.cover_url" :src="album.cover_url" alt="cover" />
            <span v-else>暂无照片</span>
          </div>
          <div class="album-info">
            <el-tag size="small" type="info">{{ album.category_display }}</el-tag>
            <h3>{{ album.title }}</h3>
            <p>{{ truncate(album.description || '暂无说明', 40) }}</p>
            <small>{{ album.photo_count }} 张照片 · {{ album.creator_name }}</small>
          </div>
        </div>
      </div>
    </div>

    <el-pagination v-if="total > pageSize" class="pagination" :current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="loadPage" />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ALBUM_CATEGORIES, fetchAlbums, type AlbumListItem } from '@/api/albums'

const loading = ref(false)
const albums = ref<AlbumListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const activeCategory = ref('')

async function loadAlbums() {
  loading.value = true
  try {
    const resp = await fetchAlbums({ category: activeCategory.value || undefined, page: currentPage.value, page_size: pageSize })
    albums.value = resp.results
    total.value = resp.count
  } finally { loading.value = false }
}

function loadPage(page: number) { currentPage.value = page; loadAlbums() }
function truncate(text: string, max: number) { return text.length > max ? `${text.slice(0, max)}...` : text }

onMounted(() => loadAlbums())
</script>

<style scoped>
.feed-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.feed-header h1 { margin: 0; }
.filter-bar { margin-bottom: 20px; }
.album-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.album-card { border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: #fff; cursor: pointer; transition: box-shadow .2s; }
.album-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.cover { height: 150px; display: flex; align-items: center; justify-content: center; background: #f3f4f6; color: #9ca3af; }
.cover img { width: 100%; height: 100%; object-fit: cover; }
.album-info { padding: 12px; }
.album-info h3 { margin: 8px 0; }
.album-info p { color: #6b7280; min-height: 22px; }
.album-info small { color: #9ca3af; }
.pagination { margin-top: 20px; justify-content: center; }
</style>
