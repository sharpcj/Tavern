<template>
  <section class="page-card">
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else-if="activity">
      <div class="header">
        <div class="header-tags">
          <el-tag :type="typeTag(activity.activity_type)">{{ activity.activity_type_display }}</el-tag>
          <el-tag :type="statusTag(activity.status)">{{ activity.status_display }}</el-tag>
        </div>
        <h1>{{ activity.title }}</h1>
        <p class="muted">发起人：{{ activity.initiator_name }} · {{ formatTime(activity.created_at) }}</p>
        <ReportButton target-type="activity" :object-id="activity.id" />
      </div>

      <div class="body-text">{{ activity.description }}</div>
      <template v-if="activity.activity_type === 'gathering'">
        <el-descriptions class="activity-info-desktop" :column="2" border>
          <el-descriptions-item label="地点">{{ activity.location || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ activity.start_time ? formatTime(activity.start_time) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="截止">{{ activity.deadline ? formatTime(activity.deadline) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="人数上限">{{ activity.max_participants || '不限' }}</el-descriptions-item>
        </el-descriptions>
        <div class="activity-info-mobile">
          <div class="info-item">
            <span>地点</span>
            <strong>{{ activity.location || '-' }}</strong>
          </div>
          <div class="info-item">
            <span>时间</span>
            <strong>{{ activity.start_time ? formatTime(activity.start_time) : '-' }}</strong>
          </div>
          <div class="info-item">
            <span>截止</span>
            <strong>{{ activity.deadline ? formatTime(activity.deadline) : '-' }}</strong>
          </div>
          <div class="info-item">
            <span>人数上限</span>
            <strong>{{ activity.max_participants || '不限' }}</strong>
          </div>
        </div>
      </template>

      <!-- Gathering: signup -->
      <template v-if="activity.activity_type === 'gathering'">
        <h2>报名名单 ({{ activity.signups.length }})</h2>
        <el-table class="responsive-table" :data="activity.signups" stripe>
          <el-table-column prop="real_name" label="姓名" />
          <el-table-column prop="participant_count" label="人数" width="80" />
          <el-table-column label="带家属" width="80"><template #default="{row}">{{ row.bring_guests ? '是' : '否' }}</template></el-table-column>
          <el-table-column prop="note" label="备注" />
        </el-table>
        <div class="mobile-record-list">
          <div v-if="activity.signups.length === 0" class="empty-record">暂无报名</div>
          <div v-for="signup in activity.signups" :key="`${signup.real_name}-${signup.created_at}`" class="record-card">
            <div class="record-card-header">
              <strong>{{ signup.real_name }}</strong>
              <span>{{ signup.participant_count }} 人</span>
            </div>
            <div class="record-line">
              <span>带家属</span>
              <strong>{{ signup.bring_guests ? '是' : '否' }}</strong>
            </div>
            <div class="record-note">
              <span>备注</span>
              <p>{{ signup.note || '无' }}</p>
            </div>
          </div>
        </div>
        <div v-if="activity.status === 'open'" class="action-bar">
          <el-button type="primary" @click="showSignup = true">我要报名</el-button>
        </div>
        <el-dialog v-model="showSignup" title="报名" width="400px" class="signup-dialog">
          <el-alert
            class="signup-tip"
            title="报名使用你的真实姓名，是否带家属由报名人自行选择。"
            type="info"
            :closable="false"
            show-icon
          />
          <el-form class="signup-form" :model="signupForm" label-position="top">
            <el-form-item label="参加人数"><el-input-number v-model="signupForm.participant_count" :min="1" /></el-form-item>
            <el-form-item label="带家属"><el-switch v-model="signupForm.bring_guests" /></el-form-item>
            <el-form-item label="备注"><el-input v-model="signupForm.note" /></el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer-actions">
              <el-button @click="showSignup = false">取消</el-button>
              <el-button type="primary" :loading="submitting" @click="doSignup">确认报名</el-button>
            </div>
          </template>
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
          <el-button class="vote-submit" type="primary" :loading="submitting" @click="doVote">提交投票</el-button>
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
        <el-table class="responsive-table" :data="activity.chain_records" stripe>
          <el-table-column prop="real_name" label="姓名" />
          <el-table-column label="参加" width="80"><template #default="{row}">{{ row.will_attend ? '是' : '否' }}</template></el-table-column>
          <el-table-column prop="participant_count" label="人数" width="80" />
          <el-table-column prop="note" label="备注" />
        </el-table>
        <div class="mobile-record-list">
          <div v-if="activity.chain_records.length === 0" class="empty-record">暂无接龙</div>
          <div v-for="record in activity.chain_records" :key="`${record.real_name}-${record.created_at}`" class="record-card">
            <div class="record-card-header">
              <strong>{{ record.real_name }}</strong>
              <span>{{ record.will_attend ? '参加' : '不参加' }}</span>
            </div>
            <div class="record-line">
              <span>人数</span>
              <strong>{{ record.participant_count }} 人</strong>
            </div>
            <div class="record-note">
              <span>备注</span>
              <p>{{ record.note || '无' }}</p>
            </div>
          </div>
        </div>
        <div v-if="activity.status === 'open'" class="action-bar">
          <el-button type="primary" @click="showChain = true">填写接龙</el-button>
        </div>
        <el-dialog v-model="showChain" title="填写接龙" width="400px" class="chain-dialog">
          <el-alert
            class="signup-tip"
            title="接龙使用你的真实姓名，填写内容会展示在活动接龙列表中。"
            type="info"
            :closable="false"
            show-icon
          />
          <el-form :model="chainForm" label-position="top">
            <el-form-item label="是否参加"><el-switch v-model="chainForm.will_attend" /></el-form-item>
            <el-form-item label="人数"><el-input-number v-model="chainForm.participant_count" :min="1" /></el-form-item>
            <el-form-item label="备注"><el-input v-model="chainForm.note" /></el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer-actions">
              <el-button @click="showChain = false">取消</el-button>
              <el-button type="primary" :loading="submitting" @click="doChain">确认</el-button>
            </div>
          </template>
        </el-dialog>
      </template>

      <el-button class="back-button" @click="$router.back()">返回列表</el-button>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchActivityDetail, signupActivity, voteActivity, fillChain, type ActivityDetail } from '@/api/activities'
import { useRealtimeEvent } from '@/composables/useRealtimeEvents'
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

async function load(showLoading = true) {
  if (showLoading) loading.value = true
  try { activity.value = await fetchActivityDetail(Number(route.params.id)) }
  finally { if (showLoading) loading.value = false }
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
useRealtimeEvent((event) => {
  if (event.type === 'activity.updated' && Number(event.target_id) === Number(route.params.id)) {
    load(false)
  }
})
</script>

<style scoped>
.header { display: grid; gap: 8px; }
.header-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.header h1 { margin: 0; overflow-wrap: anywhere; }
.header .muted { margin: 0; }
.body-text { line-height: 1.8; white-space: pre-wrap; margin: 16px 0; }
.activity-info-desktop { margin-top: 16px; }
.activity-info-mobile { display: none; }
.action-bar { margin-top: 16px; }
.vote-options { margin: 12px 0; }
.vote-opt { margin: 8px 0; }
.result-item { padding: 6px 0; }
.signup-tip { margin-bottom: 12px; }
.dialog-footer-actions { display: flex; justify-content: flex-end; gap: 8px; }
.mobile-record-list { display: none; }
.back-button { margin-top: 16px; }

@media (max-width: 640px) {
  :deep(.signup-dialog),
  :deep(.chain-dialog) {
    width: calc(100vw - 24px) !important;
    margin-top: 12vh;
  }

  .header h1 { font-size: 22px; line-height: 1.3; }
  .body-text { font-size: 15px; }
  .activity-info-desktop { display: none; }
  .activity-info-mobile {
    display: grid;
    gap: 8px;
    margin-top: 16px;
  }
  .info-item {
    display: grid;
    gap: 3px;
    padding: 10px 12px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #f9fafb;
  }
  .info-item span {
    color: #6b7280;
    font-size: 12px;
  }
  .info-item strong {
    color: #1f2937;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.5;
    overflow-wrap: anywhere;
  }
  :deep(.el-input-number) { width: 100%; }
  .vote-options { display: grid; gap: 12px; }
  .vote-opt {
    margin: 0;
    padding: 10px 12px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    line-height: 1.5;
  }
  .vote-opt :deep(.el-checkbox) {
    align-items: flex-start;
    height: auto;
    white-space: normal;
  }
  .vote-opt :deep(.el-checkbox__label) {
    min-width: 0;
    overflow-wrap: anywhere;
    line-height: 1.5;
  }
  .vote-submit { width: 100%; }
  .result-item { display: grid; gap: 4px; line-height: 1.5; }
  .action-bar .el-button { width: 100%; }
  .dialog-footer-actions { flex-direction: column-reverse; }
  .dialog-footer-actions .el-button { width: 100%; margin-left: 0; }
  .responsive-table { display: none; }
  .mobile-record-list {
    display: grid;
    gap: 10px;
  }
  .record-card {
    padding: 12px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #ffffff;
  }
  .record-card-header,
  .record-line {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    line-height: 1.5;
  }
  .record-card-header strong,
  .record-line strong {
    overflow-wrap: anywhere;
  }
  .record-card-header span,
  .record-line span,
  .record-note span {
    color: #6b7280;
    font-size: 13px;
  }
  .record-note {
    display: grid;
    gap: 4px;
    margin-top: 8px;
  }
  .record-note p {
    margin: 0;
    color: #374151;
    line-height: 1.6;
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }
  .empty-record {
    padding: 18px 12px;
    border: 1px dashed #d1d5db;
    border-radius: 8px;
    color: #6b7280;
    text-align: center;
  }
  .back-button { width: 100%; margin-left: 0; }
}
</style>
