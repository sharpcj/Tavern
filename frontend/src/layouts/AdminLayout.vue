<template>
  <el-container class="admin-layout">
    <el-aside width="200px" class="admin-sidebar">
      <h2 class="admin-title">管理后台</h2>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/admin/users">用户管理</el-menu-item>
        <el-menu-item index="/admin/users/review">用户审核</el-menu-item>
        <el-menu-item index="/admin/contents">内容管理</el-menu-item>
        <el-menu-item index="/admin/activities">活动管理</el-menu-item>
        <el-menu-item index="/admin/reports">举报处理</el-menu-item>
        <el-menu-item index="/admin/audit-logs">操作日志</el-menu-item>
      </el-menu>
      <div class="admin-back">
        <el-button text @click="$router.push('/')">← 返回前台</el-button>
      </div>
    </el-aside>
    <el-main class="admin-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.admin-layout { min-height: 100vh; }
.admin-sidebar { background: #1f2937; color: #fff; display: flex; flex-direction: column; }
.admin-title { padding: 16px; font-size: 18px; color: #fff; margin: 0; }
.admin-back { margin-top: auto; padding: 16px; }
.admin-main { background: #f9fafb; padding: 24px; }
</style>
