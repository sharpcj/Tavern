<template>
  <section class="page-card">
    <h1>生日祝福</h1>
    <p class="muted">这里只展示本月生日同学和生日月份，不展示出生年份和具体日期。祝福内容公开在班级内部，不提供私信或小群祝福。</p>

    <h2>本月生日同学</h2>
    <div v-loading="loadingBirthdays">
      <el-empty v-if="!loadingBirthdays && birthdays.length === 0" description="本月暂无同学开启生日展示" />
      <div class="birthday-grid">
        <div v-for="item in birthdays" :key="item.account_id" class="birthday-card" :class="{ selected: selectedRecipientIds.includes(item.account_id) }" @click="toggleRecipient(item.account_id)">
          <UserAvatar :src="item.avatar_url" :size="48" />
          <div>
            <strong>{{ item.display_name }}</strong>
            <div class="muted">{{ item.birthday_month }} 月生日<span v-if="item.city"> · {{ item.city }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="wish-form">
      <h2>送上祝福</h2>
      <el-form label-position="top" @submit.prevent="submitWish">
        <el-form-item label="祝福对象">
          <el-select v-model="selectedRecipientIds" multiple clearable collapse-tags collapse-tags-tooltip placeholder="可选择多个本月生日同学，也可以不选" style="width: 100%">
            <el-option v-for="item in birthdays" :key="item.account_id" :label="item.display_name" :value="item.account_id" />
          </el-select>
          <div class="field-tip">不选择具体同学时，祝福会发布给“本月生日同学”，不会产生定向通知。</div>
        </el-form-item>
        <el-form-item label="快捷祝福语">
          <el-select v-model="selectedQuickWish" clearable placeholder="选择一条默认祝福语，或直接手动输入" style="width: 100%" @change="applyQuickWish">
            <el-option v-for="phrase in defaultBirthdayWishes" :key="phrase" :label="phrase" :value="phrase" />
          </el-select>
        </el-form-item>
        <el-form-item label="祝福内容">
          <el-input v-model="wishForm.content" type="textarea" :rows="3" placeholder="写一句生日祝福" />
        </el-form-item>
        <el-form-item label="展示身份">
          <el-radio-group v-model="wishForm.display_mode">
            <el-radio value="real_name">真实姓名</el-radio>
            <el-radio value="nickname">昵称</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-button type="primary" :loading="submitting" @click="submitWish">发布祝福</el-button>
      </el-form>
    </div>

    <div class="wish-list">
      <h2>祝福留言</h2>
      <div v-loading="loadingWishes">
        <el-empty v-if="!loadingWishes && wishes.length === 0" description="暂无祝福留言" />
        <div v-for="wish in wishes" :key="wish.id" class="wish-item">
          <div class="wish-meta">
            <strong>{{ wish.display_name }}</strong>
            <span>祝 {{ wish.recipient_name }}</span>
            <span>{{ formatTime(wish.created_at) }}</span>
          </div>
          <div class="wish-content">{{ wish.content }}</div>
          <ReportButton target-type="birthday_wish" :object-id="wish.id" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import UserAvatar from '@/components/UserAvatar.vue'
import { createBirthdayWish, fetchBirthdayWishes, fetchCurrentMonthBirthdays, type BirthdayClassmate, type BirthdayWish } from '@/api/birthdays'

const loadingBirthdays = ref(false)
const loadingWishes = ref(false)
const submitting = ref(false)
const birthdays = ref<BirthdayClassmate[]>([])
const wishes = ref<BirthdayWish[]>([])
const selectedRecipientIds = ref<string[]>([])
const selectedQuickWish = ref('')
const wishForm = reactive({ content: '', display_mode: 'real_name' })
const defaultBirthdayWishes = [
  '愿你新的一岁平安顺遂，日子明亮又自在。',
  '生日快乐，愿每一个小愿望都慢慢实现。',
  '祝你一路有光，所遇皆暖，所行皆坦。',
  '愿今天的快乐延续到往后的每一天。',
  '新的一岁，愿你有热爱、有收获，也有好好休息的余地。',
  '祝你生日快乐，生活有惊喜，心里有底气。',
  '愿这一岁比上一岁更从容，也更接近想成为的自己。',
  '祝福送到，愿你健康、开心、被生活温柔以待。',
  '愿你新的一岁，眼里有星河，身边有良友。',
  '生日快乐，愿岁月不负努力，也不缺温柔。',
]

async function loadBirthdays() {
  loadingBirthdays.value = true
  try {
    const resp = await fetchCurrentMonthBirthdays()
    birthdays.value = resp.results
  } finally { loadingBirthdays.value = false }
}

async function loadWishes() {
  loadingWishes.value = true
  try {
    const resp = await fetchBirthdayWishes({ page_size: 50 })
    wishes.value = resp.results
  } finally { loadingWishes.value = false }
}

function toggleRecipient(accountId: string) {
  if (selectedRecipientIds.value.includes(accountId)) {
    selectedRecipientIds.value = selectedRecipientIds.value.filter(id => id !== accountId)
  } else {
    selectedRecipientIds.value = [...selectedRecipientIds.value, accountId]
  }
}

function applyQuickWish(value: string) {
  if (value) wishForm.content = value
}

async function submitWish() {
  if (!wishForm.content.trim()) {
    ElMessage.warning('请输入祝福内容')
    return
  }
  submitting.value = true
  try {
    await createBirthdayWish({
      recipient_account_ids: selectedRecipientIds.value,
      content: wishForm.content,
      display_mode: wishForm.display_mode,
    })
    ElMessage.success('祝福已发布')
    wishForm.content = ''
    selectedQuickWish.value = ''
    await loadWishes()
  } finally { submitting.value = false }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  await Promise.all([loadBirthdays(), loadWishes()])
})
</script>

<style scoped>
.birthday-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 12px 0 24px; }
.birthday-card { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; cursor: pointer; }
.birthday-card.selected { border-color: #409eff; background: #ecf5ff; }
.wish-form { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; }
.wish-list { margin-top: 24px; }
.wish-item { padding: 12px 0; border-top: 1px solid #e5e7eb; }
.wish-meta { display: flex; flex-wrap: wrap; gap: 8px; color: #6b7280; font-size: 13px; margin-bottom: 6px; }
.wish-content { line-height: 1.7; white-space: pre-wrap; }
</style>
