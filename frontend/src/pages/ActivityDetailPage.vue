<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else-if="activity">
      <div class="header">
        <el-tag :type="typeTag(activity.activity_type)">{{ activity.activity_type_display }}</el-tag>
        <el-tag :type="statusTag(activity.status)" style="margin-left:8px">{{ activity.status_display }}</el-tag>
        <h1>{{ activity.title }}</h1>
        <p class="muted">发起人：{{ activity.initiator_name }} · {{ formatTime(activity.created_at) }}</p>
        <ReportButton target-type="activity" :object-id="activity.id" />
      </div>

      <div class="body-text">{{ activity.description }}</div>
      <el-descriptions v-if="activity.activity_type === 'gathering'" :column="2" border style="margin-top:16px">
        <el-descriptions-item label="地点">{{ activity.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ activity.start_time ? formatTime(activity.start_time) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="截止">{{ activity.deadline ? formatTime(activity.deadline) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="人数上限">{{ activity.max_participants || '不限' }}</el-descriptions-item>
      </el-descriptions>

      <!-- Gathering: signup -->
      <template v-if="activity.activity_type === 'gathering'">
        <h2>报名名单 ({{ activity.signups.length }})</h2>
        <el-table :data="activity.signups" stripe>
          <el-table-column prop="real_name" label="姓名" />
          <el-table-column prop="participant_count" label="人数" width="80" />
          <el-table-column label="带家属" width="80"><template #default="{row}">{{ row.bring_guests ? '是' : '否' }}</template></el-table-column>
          <el-table-column prop="note" label="备注" />
        </el-table>
        <div v-if="activity.status === 'open'" class="action-bar">
          <el-button type="primary" @click="showSignup = true">我要报名</el-button>
        </div>
        <el-dialog v-model="showSignup" title="报名" width="400px">
          <el-form :model="signupForm" label-position="top">
            <el-form-item label="参加人数"><el-input-number v-model="signupForm.participant_count" :min="1" /></el-form-item>
            <el-form-item label="带家属"><el-switch v-model="signupForm.bring_guests" /></el-form-item>
            <el-form-item label="备注"><el-input v-model="signupForm.note" /></el-form-item>
          </el-form>
          <template #footer><el-button @click="showSignup = false">取消</el-button><el-button type="primary" :loading="submitting" @click="doSignup">确认报名</el-button></template>
        </el-dialog>
      </template>

      <!-- Voting -->
      <template v-if="activity.activity_type === 'voting'">
        <h2>投票</h2>
        <div v-if="activity.status === 'open'" class="vote-options">
          <el-checkbox-group v-model="selectedOptions" :max="activity.is_multi_choice ? 99 : 1">
            <div v-for="opt in activity.vote_options" :key="opt.id" class="vote-opt">
              <el-checkbox :value="opt.id">{{ opt.text }}</el-checkbox>
            </div>
          </el-checkbox-group>
          <el-button type="primary" :loading="submitting" @click="doVote">提交投票</el-button>
        </div>
        <h3 style="margin-top:16px">投票结果</h3>
        <div v-for="r in activity.vote_results" :key="r.option_id" class="result-item">
          <span>{{ r.text }}：{{ r.count }} 票</span>
          <span v-if="r.voters" class="muted">（{{ r.voters.join('、') }}）</span>
        </div>
      </template>

      <!-- Chain -->
      <template v-if="activity.activity_type === 'chain'">
        <h2>接龙列表</h2>
        <el-table :data="activity.chain_records" stripe>
          <el-table-column prop="real_name" label="姓名" />
          <el-table-column label="参加" width="80"><template #default="{row}">{{ row.will_attend ? '是' : '否' }}</template></el-table-column>
          <el-table-column prop="participant_count" label="人数" width="80" />
          <el-table-column prop="note" label="备注" />
        </el-table>
        <div v-if="activity.status === 'open'" class="action-bar">
          <el-button type="primary" @click="showChain = true">填写接龙</el-button>
        </div>
        <el-dialog v-model="showChain" title="填写接龙" width="400px">
          <el-form :model="chainForm" label-position="top">
            <el-form-item label="是否参加"><el-switch v-model="chainForm.will_attend" /></el-form-item>
            <el-form-item label="人数"><el-input-number v-model="chainForm.participant_count" :min="1" /></el-form-item>
            <el-form-item label="备注"><el-input v-model="chainForm.note" /></el-form-item>
          </el-form>
          <template #footer><el-button @click="showChain = false">取消</el-button><el-button type="primary" :loading="submitting" @click="doChain">确认</el-button></template>
        </el-dialog>
      </template>

      <el-button style="margin-top:16px" @click="$router.back()">返回列表</el-button>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchActivityDetail, signupActivity, voteActivity, fillChain, type ActivityDetail } from '@/api/activities'
import ReportButton from '@/components/ReportButton.vue'

const route = useRoute()
const loading = ref(true)
const activity = ref<ActivityDetail | null>(null)
const submitting = ref(false)
const showSignup = ref(false)
const showChain = ref(false)
const selectedOptions = ref<number[]>([])
const signupForm = reactive({ participant_count: 1, bring_guests: false, note: '' })
const chainForm = reactive({ will_attend: true, participant_count: 1, note: '' })

async function load() {
  loading.value = true
  try { activity.value = await fetchActivityDetail(Number(route.params.id)) }
  finally { loading.value = false }
}

async function doSignup() {
  submitting.value = true
  try { await signupActivity(activity.value!.id, { ...signupForm }); showSignup.value = false; await load(); ElMessage.success('报名成功') }
  catch { ElMessage.error('报名失败') }
  finally { submitting.value = false }
}

async function doVote() {
  if (selectedOptions.value.length === 0) { ElMessage.warning('请选择选项'); return }
  submitting.value = true
  try { await voteActivity(activity.value!.id, selectedOptions.value); await load(); ElMessage.success('投票成功') }
  catch { ElMessage.error('投票失败') }
  finally { submitting.value = false }
}

async function doChain() {
  submitting.value = true
  try { await fillChain(activity.value!.id, { ...chainForm }); showChain.value = false; await load(); ElMessage.success('填写成功') }
  catch { ElMessage.error('填写失败') }
  finally { submitting.value = false }
}

function typeTag(t: string) { return t === 'gathering' ? 'success' : t === 'voting' ? 'warning' : 'info' }
function statusTag(s: string) { return s === 'open' ? 'success' : s === 'closed' ? 'info' : s === 'finished' ? '' : 'danger' }
function formatTime(iso: string) { return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }

onMounted(() => load())
</script>

<style scoped>
.header h1 { margin: 8px 0; }
.body-text { line-height: 1.8; white-space: pre-wrap; margin: 16px 0; }
.action-bar { margin-top: 16px; }
.vote-options { margin: 12px 0; }
.vote-opt { margin: 8px 0; }
.result-item { padding: 6px 0; }
</style>
