<template>
  <section class="page-card">
    <h1>生日祝福</h1>
    <p class="muted">这里只展示本月生日同学和生日月份，不展示出生年份和具体日期。祝福内容公开在班级内部，不提供私信或小群祝福。</p>

    <h2>本月生日同学</h2>
    <div v-loading="loadingBirthdays">
      <el-empty v-if="!loadingBirthdays && birthdays.length === 0" description="本月暂无同学开启生日展示" />
      <div class="birthday-grid">
        <div v-for="item in birthdays" :key="item.account_id" class="birthday-card" :class="{ selected: selectedRecipient === item.account_id }" @click="selectRecipient(item.account_id)">
          <el-avatar :src="item.avatar_url" :size="48">{{ item.real_name.slice(0, 1) }}</el-avatar>
          <div>
            <strong>{{ item.real_name }}</strong>
            <span v-if="item.nickname" class="muted">（{{ item.nickname }}）</span>
            <div class="muted">{{ item.birthday_month }} 月生日<span v-if="item.city"> · {{ item.city }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="wish-form">
      <h2>送上祝福</h2>
      <el-form label-position="top" @submit.prevent="submitWish">
        <el-form-item label="祝福对象">
          <el-select v-model="selectedRecipient" placeholder="选择本月生日同学" style="width: 100%">
            <el-option v-for="item in birthdays" :key="item.account_id" :label="item.real_name" :value="item.account_id" />
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
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { createBirthdayWish, fetchBirthdayWishes, fetchCurrentMonthBirthdays, type BirthdayClassmate, type BirthdayWish } from '@/api/birthdays'

const loadingBirthdays = ref(false)
const loadingWishes = ref(false)
const submitting = ref(false)
const birthdays = ref<BirthdayClassmate[]>([])
const wishes = ref<BirthdayWish[]>([])
const selectedRecipient = ref('')
const wishForm = reactive({ content: '', display_mode: 'real_name' })

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

function selectRecipient(accountId: string) { selectedRecipient.value = accountId }

async function submitWish() {
  if (!selectedRecipient.value) {
    ElMessage.warning('请先选择祝福对象')
    return
  }
  if (!wishForm.content.trim()) {
    ElMessage.warning('请输入祝福内容')
    return
  }
  submitting.value = true
  try {
    await createBirthdayWish({
      recipient_account_id: selectedRecipient.value,
      content: wishForm.content,
      display_mode: wishForm.display_mode,
    })
    ElMessage.success('祝福已发布')
    wishForm.content = ''
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
