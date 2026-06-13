文章标题：M11 举报、治理与操作日志技术方案

# 一、背景

M11 实现站内举报、内容治理和操作日志能力。此前 M06 动态评论、M07 活动、M09 相册照片、M10 生日祝福都已经形成主要内容对象，M11 需要把这些对象纳入统一举报和治理流程。

根据白皮书，每条动态、评论、照片、活动说明和生日祝福留言都应提供举报入口。管理员后台需要展示举报列表，并支持忽略、删除内容、隐藏内容、要求发布者修改、警告用户、限制发言、封禁账号等处理方式。处理结果必须记录管理日志，便于后续追溯。

# 二、需求描述

## 覆盖对象

M11 覆盖以下举报对象：

| 对象 | 模型 | 作者字段 |
| --- | --- | --- |
| 动态 | `posts.Post` | `author` |
| 动态评论 / 回复 | `comments.Comment` | `author` |
| 照片 | `albums.Photo` | `uploader` |
| 活动说明 | `activities.Activity` | `initiator` |
| 生日祝福 | `birthdays.BirthdayWish` | `author` |

本阶段不把相册整体作为直接举报对象，照片是相册模块内的主要治理对象。

## 处理动作

| 动作 | 说明 |
| --- | --- |
| `ignore` | 忽略举报，仅记录处理说明 |
| `hide_content` | 隐藏内容，内容状态改为 `hidden` |
| `delete_content` | 删除内容，优先调用软删除能力 |
| `request_revision` | 要求发布者修改，仅记录治理动作 |
| `warn_user` | 警告用户，仅记录治理动作 |
| `restrict_user` | 将内容作者账号状态改为 `restricted` |
| `ban_user` | 将内容作者账号状态改为 `banned` |

# 三、技术方案

## 通用引用方式

举报对象使用 Django `ContentType + object_id` 建模：

- `Report.content_type`
- `Report.object_id`
- `Report.content_object`

这样后续新增内容对象时，不需要为每种对象新增一组字段。

## 数据模型

### AuditLog

记录关键管理操作。

| 字段 | 说明 |
| --- | --- |
| `actor` | 操作者 |
| `action` | 操作类型 |
| `target_content_type` / `target_object_id` | 操作对象 |
| `reason` | 操作原因 |
| `metadata` | 扩展信息 |
| `created_at` | 操作时间 |

### Report

记录用户举报。

| 字段 | 说明 |
| --- | --- |
| `reporter` | 举报人 |
| `content_type` / `object_id` | 被举报对象 |
| `reason` | 举报原因 |
| `description` | 补充说明 |
| `status` | `pending` / `processing` / `resolved` / `ignored` |
| `handled_by` / `handled_at` | 处理人和处理时间 |
| `handle_note` | 处理说明 |

### ModerationAction

记录针对举报产生的治理动作。

| 字段 | 说明 |
| --- | --- |
| `report` | 关联举报 |
| `action_type` | 治理动作 |
| `actor` | 处理人 |
| `target_user` | 被处理用户 |
| `reason` | 处理原因 |
| `metadata` | 扩展信息 |
| `created_at` | 创建时间 |

## API

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/reports/` | 已审核用户 | 提交举报 |
| `GET` | `/api/v1/admin/reports/` | 管理会员以上 | 举报列表 |
| `GET` | `/api/v1/admin/reports/{id}/` | 管理会员以上 | 举报详情 |
| `POST` | `/api/v1/admin/reports/{id}/handle/` | 管理会员以上 | 处理举报 |
| `GET` | `/api/v1/admin/audit-logs/` | 管理会员以上 | 操作日志列表 |

## 通用治理工具

新增工具函数：

- `get_content_owner(obj)`：识别内容作者
- `apply_moderation_action(report, action_type, actor, reason)`：执行治理动作
- `write_audit_log(...)`：记录操作日志

内容隐藏与删除策略：

- 如果对象有 `status` 且支持 `ContentStatus`，隐藏时设为 `hidden`
- 如果对象支持 `soft_delete()`，删除时调用软删除
- 活动对象没有 `ContentStatus`，删除/隐藏类处理先将活动状态设为 `cancelled`，并记录操作日志

# 四、前端方案

## 普通用户举报入口

在以下页面增加举报入口：

- 动态详情页
- 照片详情页
- 活动详情页
- 生日祝福页

用户选择举报理由并填写说明后提交。

## 轻量管理页

新增 `/admin/reports`：

- 展示举报列表
- 按状态筛选
- 查看举报对象类型、举报人、原因、处理状态
- 选择处理动作并填写处理说明

# 五、异常和边界场景

| 场景 | 处理 |
| --- | --- |
| 举报不存在或已删除对象 | 400 |
| 重复举报同一对象 | 允许提交，便于反映多人反馈 |
| 普通用户访问管理接口 | 403 |
| 处理已结束举报 | 400，避免重复处理 |
| 无法识别内容作者 | 处理内容状态但不做用户限制/封禁 |
| 活动对象被删除处理 | 状态改为取消，保留活动记录 |

# 六、验收标准

- 已审核用户可以提交举报
- 管理会员和超级管理员可以查看举报列表和详情
- 管理会员和超级管理员可以处理举报
- 处理举报会生成 `ModerationAction`
- 提交举报和处理举报会生成 `AuditLog`
- 隐藏、删除、限制、封禁动作会修改对应内容或用户状态
- 普通用户不能访问管理举报接口
- 前端主要内容页面有举报入口
- 前端管理页可以完成举报处理
- 后端检查、迁移检查、测试、OpenAPI、前端类型检查和构建全部通过
