<template>
  <section class="page-card">
    <h1>同学通讯录</h1>

    <el-row :gutter="12" class="search-bar">
      <el-col :span="8">
        <el-input v-model="searchText" placeholder="搜索姓名、城市、行业" clearable @clear="doSearch" @keyup.enter="doSearch" />
      </el-col>
      <el-col :span="4">
        <el-input v-model="filterCity" placeholder="城市" clearable @clear="doSearch" />
      </el-col>
      <el-col :span="4">
        <el-input v-model="filterOccupation" placeholder="行业" clearable @clear="doSearch" />
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="doSearch">搜索</el-button>
      </el-col>
    </el-row>

    <el-table :data="classmates" stripe v-loading="loading" @row-click="goDetail" style="cursor:pointer">
      <el-table-column label="头像" width="70">
        <template #default="{ row }">
          <el-avatar :src="row.avatar_url" :size="40">{{ row.real_name[0] }}</el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="real_name" label="姓名" width="120" />
      <el-table-column label="称呼" width="120">
        <template #default="{ row }">{{ row.nickname || '-' }}</template>
      </el-table-column>
      <el-table-column prop="city" label="城市" width="120" />
      <el-table-column prop="occupation" label="职业/行业" min-width="160" />
      <el-table-column label="生日月份" width="100">
        <template #default="{ row }">{{ row.birthday_month ? row.birthday_month + ' 月' : '-' }}</template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      class="pagination"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="loadPage"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchClassmates, type ClassmateListItem } from '@/api/profile'

const router = useRouter()
const loading = ref(false)
const classmates = ref<ClassmateListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const searchText = ref('')
const filterCity = ref('')
const filterOccupation = ref('')

async function loadPage(page: number = 1) {
  loading.value = true
  currentPage.value = page
  try {
    const resp = await fetchClassmates({
      search: searchText.value || undefined,
      city: filterCity.value || undefined,
      occupation: filterOccupation.value || undefined,
      page,
      page_size: pageSize,
    })
    classmates.value = resp.results
    total.value = resp.count
  } finally {
    loading.value = false
  }
}

function doSearch() {
  loadPage(1)
}

function goDetail(row: ClassmateListItem) {
  router.push(`/classmates/${row.account_id}`)
}

onMounted(() => loadPage())
</script>

<style scoped>
.search-bar {
  margin-bottom: 20px;
}
.pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>
