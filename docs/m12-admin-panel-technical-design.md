文章标题：M12 管理后台整合技术方案

# 一、背景

M12 将此前分散在各模块的管理能力整合为统一管理后台。M11 已完成举报处理和操作日志基础，M12 在此基础上补齐用户管理、内容管理、活动管理等后台页面，形成完整的管理工作台。

# 二、需求范围

## 已具备的管理能力（来自 M02-M11）

| 能力 | 来源 | 状态 |
| --- | --- | --- |
| 用户审核（待审核列表、审核通过/拒绝） | M02 accounts/views.py | 已有 API，无前端页面 |
| 公告管理（发布、编辑、删除） | M08 | 已有 API 和前端页面 |
| 举报处理 | M11 | 已有 API 和 AdminReportsPage |
| 操作日志查看 | M11 | 已有 API，无前端页面 |

## M12 新增

| 能力 | 说明 |
| --- | --- |
| 管理后台布局 | 独立侧边栏导航，仅 moderator/super_admin 可见 |
| 用户管理页 | 全部用户列表、按状态/角色筛选、修改角色、限制/封禁/解封 |
| 内容管理页 | 动态、评论、照片、相册列表，支持隐藏/删除 |
| 活动管理页 | 活动列表、状态变更、删除活动 |
| 用户审核页 | 整合 M02 审核 API，提供审核操作界面 |
| 操作日志页 | 整合 M11 AuditLog API，提供日志查看界面 |
| 举报处理页 | 整合 M11 AdminReportsPage 到管理后台布局 |

## 边界决策

1. 管理后台使用独立路由 `/admin/*`，与普通用户页面分离
2. 管理后台使用独立布局 `AdminLayout.vue`，含侧边栏
3. 仅 `moderator` 和 `super_admin` 可访问管理后台
4. 用户角色变更仅 `super_admin` 可操作
5. 内容管理页使用 Tab 切换动态/评论/照片/相册，减少页面数量
6. 活动管理页复用 M07 活动列表 API，增加管理操作列

# 三、后端方案

## 新增 API

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /api/v1/admin/users/ | super_admin | 全部用户列表，支持 status/role 筛选 |
| PATCH | /api/v1/admin/users/{account_id}/ | super_admin | 修改用户角色、账号状态 |
| GET | /api/v1/admin/contents/posts/ | moderator+ | 全部动态列表，支持 status 筛选 |
| POST | /api/v1/admin/contents/posts/{id}/hide/ | moderator+ | 隐藏动态 |
| POST | /api/v1/admin/contents/posts/{id}/delete/ | moderator+ | 删除动态 |
| GET | /api/v1/admin/contents/comments/ | moderator+ | 全部评论列表 |
| POST | /api/v1/admin/contents/comments/{id}/hide/ | moderator+ | 隐藏评论 |
| POST | /api/v1/admin/contents/comments/{id}/delete/ | moderator+ | 删除评论 |
| GET | /api/v1/admin/contents/photos/ | moderator+ | 全部照片列表 |
| POST | /api/v1/admin/contents/photos/{id}/hide/ | moderator+ | 隐藏照片 |
| GET | /api/v1/admin/contents/albums/ | moderator+ | 全部相册列表 |
| POST | /api/v1/admin/contents/albums/{id}/hide/ | moderator+ | 隐藏相册 |
| GET | /api/v1/admin/activities/ | moderator+ | 全部活动列表 |
| POST | /api/v1/admin/activities/{id}/update-status/ | moderator+ | 更新活动状态 |
| POST | /api/v1/admin/activities/{id}/delete/ | super_admin | 删除活动 |

## 实现方式

- 在 `apps/accounts/` 新增 `admin_views.py` 放置用户管理 API
- 在 `apps/common/` 新增 `admin_views.py` 放置通用内容管理 API
- 在 `apps/activities/` 新增 `admin_views.py` 放置活动管理 API
- 所有管理操作写入 AuditLog

# 四、前端方案

## 路由

```text
/admin                 → AdminLayout（侧边栏布局）
/admin/users           → 用户管理
/admin/users/review    → 用户审核
/admin/contents        → 内容管理（Tab: 动态/评论/照片/相册）
/admin/activities      → 活动管理
/admin/announcements   → 公告管理（复用 M08 页面，调整布局）
/admin/reports         → 举报处理（复用 M11 页面）
/admin/audit-logs      → 操作日志
```

## 组件

- `AdminLayout.vue`：侧边栏 + 顶栏 + `<router-view>`
- `AdminUsersPage.vue`：用户列表、筛选、角色/状态修改弹窗
- `AdminReviewPage.vue`：待审核用户列表、审核操作
- `AdminContentsPage.vue`：Tab 切换动态/评论/照片/相册，隐藏/删除操作
- `AdminActivitiesPage.vue`：活动列表、状态变更、删除
- `AdminAuditLogsPage.vue`：操作日志列表

# 五、验收标准

- 管理后台仅 moderator/super_admin 可访问
- 用户管理可查看全部用户、修改角色和状态
- 用户审核可查看待审核用户并执行审核
- 内容管理可查看和隐藏/删除动态、评论、照片、相册
- 活动管理可查看全部活动、变更状态、删除活动
- 操作日志可查看关键操作记录
- 所有管理操作写入 AuditLog
- 后端检查、迁移检查、测试、OpenAPI、前端类型检查和构建全部通过
