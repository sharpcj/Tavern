<template>
  <section class="page-card auth-card">
    <h1>登录</h1>
    <p class="muted">登录后可查看账号审核状态。待审核用户暂不能访问内部社区内容。</p>

    <el-form :model="form" label-position="top" @submit.prevent="submit">
      <el-form-item label="邮箱" required>
        <el-input v-model="form.email" placeholder="name@example.com" />
      </el-form-item>
      <el-form-item label="密码" required>
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>
      <el-button type="primary" :loading="submitting" native-type="submit">登录</el-button>
      <el-button text @click="$router.push('/register')">还没有账号，去注册</el-button>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const submitting = ref(false)
const form = reactive({
  email: '',
  password: '',
})

async function submit() {
  if (!form.email || !form.password) {
    ElMessage.warning('请填写邮箱和密码')
    return
  }
  submitting.value = true
  try {
    await authStore.login(form.email, form.password)
    router.push('/review-status')
  } catch {
    ElMessage.error('登录失败，请检查邮箱和密码')
  } finally {
    submitting.value = false
  }
}
</script>
