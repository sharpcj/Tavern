<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-title" @click="$router.push('/')">Tavern 同学社区</div>
      <div class="app-nav">
        <el-button text @click="$router.push('/register')">注册</el-button>
        <el-button text @click="$router.push('/login')">登录</el-button>
        <el-button text @click="$router.push('/review-status')">审核状态</el-button>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>
