文章标题：M08 公告与置顶技术方案

# 一、背景

M08 实现班级公告发布与管理能力。公告模块相对独立，依赖 M02（账号与角色）和 M03（权限基础），可与动态、活动模块并行开发。

根据白皮书，公告由管理员或管理会员发布，用于聚会通知、网站说明、规则更新、老师消息、纪念日提醒等场景。公告可置顶、可设有效期，重要公告支持用户确认已读。

# 二、需求描述

| 来源 | 需求内容 |
| --- | --- |
| 白皮书 | 公告由管理员或管理会员发布，可置顶、可设有效期，重要公告支持已读确认 |
| 模块规划 | 公告模型、列表与详情、发布管理、已读确认、前端公告页面 |
| 用户本轮确认 | super_admin 和 moderator 可发布/编辑/删除；实现已读确认和有效期；首页置顶展示 |

## 本阶段范围

M08 实现：
- Announcement 模型：标题、内容、发布人、置顶、有效期、需已读确认
- 公告 API：列表（分页）、详情、创建/编辑/删除（管理员/管理会员）
- 已读确认 API
- 首页置顶公告 API
- 前端：公告列表页、详情页、发布/编辑页、首页公告栏

M08 不实现：
- 公告评论
- 公告关联活动

# 三、技术方案

## 数据模型

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `title` | CharField | 公告标题 |
| `content` | TextField | 公告内容 |
| `publisher` | FK User | 发布人 |
| `publisher_name_snapshot` | CharField | 发布人姓名快照 |
| `is_pinned` | BooleanField | 是否置顶 |
| `pinned_at` | DateTime null | 置顶时间 |
| `require_read_confirm` | BooleanField | 是否需要已读确认 |
| `expires_at` | DateTime null | 过期时间 |
| `status` | CharField | published / hidden / deleted |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

## API

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/announcements/` | IsApprovedClassmate | 公告列表（分页） |
| `GET` | `/api/v1/announcements/pinned/` | IsApprovedClassmate | 当前有效置顶公告 |
| `GET` | `/api/v1/announcements/{id}/` | IsApprovedClassmate | 公告详情 |
| `POST` | `/api/v1/announcements/` | IsModeratorOrAbove | 发布公告 |
| `PATCH` | `/api/v1/announcements/{id}/` | IsModeratorOrAbove | 编辑公告 |
| `DELETE` | `/api/v1/announcements/{id}/` | IsModeratorOrAbove | 删除公告 |
| `POST` | `/api/v1/announcements/{id}/read-confirm/` | IsApprovedClassmate | 已读确认 |

## 前端

| 路由 | 页面 | 权限 |
| --- | --- | --- |
| `/announcements` | 公告列表页 | requiresAuth + requiresApproved |
| `/announcements/:id` | 公告详情页 | requiresAuth + requiresApproved |
| `/announcements/create` | 发布公告页 | requiresAuth + requiresApproved（仅管理员/管理会员可见入口） |
| 首页公告栏 | 动态列表页顶部 | 展示有效置顶公告 |

# 四、验收标准

- 管理员和管理会员可发布、编辑、删除公告
- 普通同学可查看公告列表和详情
- 置顶公告在首页顶部展示
- 过期公告不在列表和首页展示
- 已读确认功能可用
- 全部验证通过
