<template>
  <section class="page-card">
    <h1>编辑个人资料</h1>
    <p class="muted">以下信息将展示在同学通讯录中。联系方式默认仅自己可见，你可以根据需要调整可见范围。</p>

    <el-skeleton v-if="loading" :rows="8" animated />
    <el-form v-else ref="formRef" :model="form" label-position="top" @submit.prevent="submit">
      <h2>公开资料</h2>
      <el-form-item label="头像链接">
        <el-input v-model="form.avatar_url" placeholder="https://example.com/avatar.jpg" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="当前城市">
            <el-input v-model="form.city" placeholder="例如：北京" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="职业或行业">
            <el-input v-model="form.occupation" placeholder="例如：软件工程师" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="个人简介">
        <el-input v-model="form.bio" type="textarea" :rows="3" placeholder="简单介绍一下自己" />
      </el-form-item>
      <el-form-item label="生日月份">
        <el-select v-model="form.birthday_month" placeholder="选择月份（选填）" clearable>
          <el-option v-for="m in 12" :key="m" :label="`${m} 月`" :value="m" />
        </el-select>
      </el-form-item>

      <h2>联系方式</h2>
      <el-alert class="form-tip" title="联系方式默认仅自己可见。选择「所有人可见」后，所有审核通过的同学都能看到。选择「指定同学可见」后，只有你选择的同学能看到。" type="info" :closable="false" show-icon />

      <el-form-item label="手机号">
        <el-input v-model="form.phone" placeholder="选填" />
      </el-form-item>
      <el-form-item label="手机号可见范围">
        <el-radio-group v-model="form.phone_visibility">
          <el-radio value="everyone">所有人可见</el-radio>
          <el-radio value="selected">指定同学可见</el-radio>
          <el-radio value="only_me">仅自己可见</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="微信号">
        <el-input v-model="form.wechat" placeholder="选填" />
      </el-form-item>
      <el-form-item label="微信号可见范围">
        <el-radio-group v-model="form.wechat_visibility">
          <el-radio value="everyone">所有人可见</el-radio>
          <el-radio value="selected">指定同学可见</el-radio>
          <el-radio value="only_me">仅自己可见</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="邮箱可见范围">
        <el-radio-group v-model="form.email_visibility">
          <el-radio value="everyone">所有人可见</el-radio>
          <el-radio value="selected">指定同学可见</el-radio>
          <el-radio value="only_me">仅自己可见</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="showContactSelector" label="指定可见的同学">
        <el-select
          v-model="form.contact_visible_to"
          multiple
          filterable
          remote
          reserve-keyword
          placeholder="搜索并选择同学"
          :remote-method="searchClassmates"
          :loading="searchLoading"
          value-key="account_id"
        >
          <el-option
            v-for="item in searchResults"
            :key="item.account_id"
            :label="`${item.real_name}${item.nickname ? '（' + item.nickname + '）' : ''}`"
            :value="item.account_id"
          />
        </el-select>
      </el-form-item>

      <el-button type="primary" :loading="submitting" native-type="submit">保存</el-button>
    </el-form>
  </section>
</template>

<script setup lang="ts">
import type { FormInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchClassmates, fetchMyProfile, updateMyProfile, type ClassmateListItem, type ProfileData } from '@/api/profile'

const formRef = ref<FormInstance>()
const loading = ref(true)
const submitting = ref(false)
const searchLoading = ref(false)
const searchResults = ref<ClassmateListItem[]>([])

const form = reactive<ProfileData>({
  real_name: '',
  nickname: '',
  email: '',
  avatar_url: '',
  city: '',
  occupation: '',
  bio: '',
  birthday_month: null,
  phone: '',
  phone_visibility: 'only_me',
  wechat: '',
  wechat_visibility: 'only_me',
  email_visibility: 'only_me',
  contact_visible_to: [],
  created_at: '',
  updated_at: '',
})

const showContactSelector = computed(() =>
  form.phone_visibility === 'selected' ||
  form.wechat_visibility === 'selected' ||
  form.email_visibility === 'selected'
)

async function searchClassmates(query: string) {
  if (!query) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const resp = await fetchClassmates({ search: query, page_size: 20 })
    searchResults.value = resp.results
  } finally {
    searchLoading.value = false
  }
}

async function submit() {
  submitting.value = true
  try {
    const payload: Partial<ProfileData> = {
      avatar_url: form.avatar_url,
      city: form.city,
      occupation: form.occupation,
      bio: form.bio,
      birthday_month: form.birthday_month,
      phone: form.phone,
      phone_visibility: form.phone_visibility,
      wechat: form.wechat,
      wechat_visibility: form.wechat_visibility,
      email_visibility: form.email_visibility,
      contact_visible_to: form.contact_visible_to,
    }
    await updateMyProfile(payload)
    ElMessage.success('资料已保存')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const data = await fetchMyProfile()
    Object.assign(form, data)
  } catch {
    ElMessage.error('加载资料失败')
  } finally {
    loading.value = false
  }
})
</script>
