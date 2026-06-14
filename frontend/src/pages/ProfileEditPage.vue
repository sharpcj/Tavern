<template>
  <section class="page-card">
    <h1>编辑个人资料</h1>
    <p class="muted">以下信息将展示在同学通讯录中。联系方式默认仅自己可见，你可以根据需要调整可见范围。</p>

    <el-skeleton v-if="loading" :rows="8" animated />
    <el-form v-else ref="formRef" :model="form" label-position="top" @submit.prevent="submit">
      <h2>公开资料</h2>

      <el-form-item label="真实姓名">
        <el-input :model-value="form.real_name" disabled />
        <div class="field-tip">真实姓名用于身份审核和活动实名，注册后不可修改。如需更正请联系管理员。</div>
      </el-form-item>

      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="form.nickname" placeholder="同学之间怎么称呼你" />
        <div class="field-tip">发动态、评论时默认显示的名称，可随时修改。</div>
      </el-form-item>

      <el-form-item label="头像">
        <div class="avatar-upload-row">
          <UserAvatar :src="avatarPreviewUrl || form.avatar_url" :size="72" />
          <div class="avatar-upload-actions">
            <input type="file" accept="image/jpeg,image/png,image/gif,image/webp" @change="onAvatarChange" />
            <div class="field-tip">仅支持 JPG、PNG、GIF、WebP，文件不超过 512 KB，宽高不超过 1024 像素。</div>
          </div>
        </div>
      </el-form-item>
      <el-form-item label="头像公开展示">
        <el-switch v-model="form.avatar_visible" active-text="公开" inactive-text="不公开" />
        <div class="field-tip">关闭后，其他同学在通讯录、同学详情、生日等页面会看到默认头像；你自己仍可在个人资料页看到已上传头像。</div>
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
      <el-form-item label="生日板块展示">
        <el-switch v-model="form.show_birthday" active-text="展示生日月份" inactive-text="不展示" />
        <div class="field-tip">开启后，你只会在对应月份出现在"本月生日同学"列表中，系统不会展示年份和具体日期。</div>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import UserAvatar from '@/components/UserAvatar.vue'
import { fetchClassmates, fetchMyProfile, updateMyProfile, type ClassmateListItem, type ProfileData, type ProfileUpdatePayload } from '@/api/profile'

const formRef = ref<FormInstance>()
const loading = ref(true)
const submitting = ref(false)
const searchLoading = ref(false)
const searchResults = ref<ClassmateListItem[]>([])
const selectedAvatar = ref<File | null>(null)
const avatarPreviewUrl = ref('')

const allowedAvatarTypes = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp'])
const maxAvatarSize = 512 * 1024

const form = reactive<ProfileData>({
  real_name: '',
  nickname: '',
  email: '',
  avatar_url: '',
  avatar_visible: true,
  city: '',
  occupation: '',
  bio: '',
  birthday_month: null,
  show_birthday: false,
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

function clearAvatarPreview() {
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value)
    avatarPreviewUrl.value = ''
  }
}

function onAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!allowedAvatarTypes.has(file.type)) {
    ElMessage.warning('请选择 JPG、PNG、GIF 或 WebP 图片')
    return
  }
  if (file.size > maxAvatarSize) {
    ElMessage.warning('头像图片不能超过 512 KB')
    return
  }
  selectedAvatar.value = file
  clearAvatarPreview()
  avatarPreviewUrl.value = URL.createObjectURL(file)
}

async function submit() {
  submitting.value = true
  try {
    const payload: ProfileUpdatePayload = {
      nickname: form.nickname,
      city: form.city,
      occupation: form.occupation,
      bio: form.bio,
      avatar_visible: form.avatar_visible,
      birthday_month: form.birthday_month,
      show_birthday: form.show_birthday,
      phone: form.phone,
      phone_visibility: form.phone_visibility,
      wechat: form.wechat,
      wechat_visibility: form.wechat_visibility,
      email_visibility: form.email_visibility,
      contact_visible_to: form.contact_visible_to,
      avatar: selectedAvatar.value,
    }
    const updated = await updateMyProfile(payload)
    Object.assign(form, updated)
    selectedAvatar.value = null
    clearAvatarPreview()
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

onBeforeUnmount(() => clearAvatarPreview())
</script>

<style scoped>
.field-tip { margin-top: 6px; color: #6b7280; font-size: 13px; }
.avatar-upload-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.avatar-upload-actions {
  flex: 1;
}
</style>
