<template>
  <section class="page-card auth-card">
    <h1>注册账号</h1>
    <p class="muted">请使用邮箱注册，并填写真实身份资料。管理员审核通过后，才能进入班级社区。</p>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="name@example.com" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认密码" prop="password_confirm">
        <el-input v-model="form.password_confirm" type="password" show-password />
      </el-form-item>
      <el-form-item label="真实姓名" prop="real_name">
        <el-input v-model="form.real_name" />
        <div class="field-tip">用于身份审核和活动实名，不会默认公开。可在个人资料中设置是否展示。</div>
      </el-form-item>
      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="form.nickname" placeholder="同学之间怎么称呼你" />
        <div class="field-tip">发动态、评论时默认显示的名称。可随时在个人资料中修改。</div>
      </el-form-item>
      <el-form-item label="高三所在学校" prop="high_school">
        <el-input v-model="form.high_school" />
      </el-form-item>
      <el-form-item label="高三所在班级" prop="high_school_class">
        <el-input v-model="form.high_school_class" placeholder="例如：高三一班" />
      </el-form-item>
      <el-form-item label="其它信息（选填）" prop="extra_info">
        <el-input v-model="form.extra_info" type="textarea" :rows="3" placeholder="可填写班主任、座位、寝室、毕业后所在城市等辅助说明" />
      </el-form-item>
      <el-alert
        class="form-tip"
        title="注册后需等待管理员审核，审核通过后才算正式注册成功。"
        type="info"
        :closable="false"
        show-icon
      />
      <el-form-item>
        <el-checkbox v-model="agreedToTerms">
          我已阅读并同意
          <router-link class="convention-link" to="/community-convention" @click.stop>《社区公约》</router-link>
          ，理解本网站仅面向同班同学开放，注册信息将用于身份审核和社区治理。
        </el-checkbox>
      </el-form-item>
      <el-button type="primary" :loading="submitting" :disabled="!agreedToTerms" native-type="submit">提交注册</el-button>
      <el-button text @click="$router.push('/login')">已有账号，去登录</el-button>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { register, type RegisterPayload } from '@/api/auth'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const agreedToTerms = ref(false)

const form = reactive<RegisterPayload>({
  email: '',
  password: '',
  password_confirm: '',
  real_name: '',
  high_school: '',
  high_school_class: '',
  nickname: '',
  extra_info: '',
})

const rules: FormRules<RegisterPayload> = {
  email: [
    { required: true, message: '请填写邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请填写密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
  password_confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  real_name: [{ required: true, message: '请填写真实姓名', trigger: 'blur' }],
  nickname: [{ required: true, message: '请填写昵称', trigger: 'blur' }],
  high_school: [{ required: true, message: '请填写高三所在学校', trigger: 'blur' }],
  high_school_class: [{ required: true, message: '请填写高三所在班级', trigger: 'blur' }],
}

async function submit() {
  if (!agreedToTerms.value) {
    ElMessage.warning('请先勾选同意社区公约')
    return
  }
  await formRef.value?.validate()
  submitting.value = true
  try {
    await register(form)
    ElMessage.success('注册申请已提交，请等待管理员审核')
    router.push('/login')
  } catch {
    ElMessage.error('注册失败，请检查填写信息')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.field-tip { margin-top: 4px; color: #6b7280; font-size: 13px; line-height: 1.5; }
.convention-link { color: #2563eb; text-decoration: none; }
.convention-link:hover { text-decoration: underline; }
</style>
