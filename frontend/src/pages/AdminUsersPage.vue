<template>
  <section class="page-card">
    <h1>用户管理</h1>
    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="账号状态" clearable @change="load">
        <el-option label="正常" value="normal" />
        <el-option label="已限制" value="restricted" />
        <el-option label="已封禁" value="banned" />
      </el-select>
      <el-select v-model="roleFilter" placeholder="角色" clearable @change="load" style="margin-left:8px">
        <el-option label="普通同学" value="classmate" />
        <el-option label="管理会员" value="moderator" />
        <el-option label="超级管理员" value="super_admin" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="users" stripe>
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column prop="role_display" label="角色" width="100" />
      <el-table-column prop="account_status_display" label="状态" width="100" />
      <el-table-column prop="review_status_display" label="审核" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="编辑用户" width="400px">
      <el-form v-if="editUser" label-position="top">
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width:100%">
            <el-option label="普通同学" value="classmate" />
            <el-option label="管理会员" value="moderator" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号状态">
          <el-select v-model="editForm.account_status" style="width:100%">
            <el-option label="正常" value="normal" />
            <el-option label="已限制" value="restricted" />
            <el-option label="已封禁" value="banned" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { fetchAdminUsers, updateAdminUser, type AdminUser } from '@/api/admin'

const loading = ref(false)
const saving = ref(false)
const users = ref<AdminUser[]>([])
const statusFilter = ref('')
const roleFilter = ref('')
const dialogVisible = ref(false)
const editUser = ref<AdminUser | null>(null)
const editForm = reactive({ role: '', account_status: '' })

async function load() {
  loading.value = true
  try {
    const resp = await fetchAdminUsers({ status: statusFilter.value || undefined, role: roleFilter.value || undefined })
    users.value = resp.results
  } finally { loading.value = false }
}

function openEdit(user: AdminUser) {
  editUser.value = user
  editForm.role = user.role
  editForm.account_status = user.account_status
  dialogVisible.value = true
}

async function save() {
  if (!editUser.value) return
  saving.value = true
  try {
    await updateAdminUser(editUser.value.account_id, { role: editForm.role, account_status: editForm.account_status })
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } finally { saving.value = false }
}

onMounted(() => load())
</script>

<style scoped>
.filter-bar { margin-bottom: 16px; }
</style>
