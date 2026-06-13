<template>
  <section class="page-card">
    <h1>高中同班同学社区网站</h1>
    <p>当前已进入账号注册与身份审核阶段。注册申请提交后，需要管理员审核通过后才算正式注册成功。</p>
    <div class="actions">
      <el-button type="primary" @click="$router.push('/register')">注册账号</el-button>
      <el-button @click="$router.push('/login')">登录查看审核状态</el-button>
    </div>
  </section>
</template>
