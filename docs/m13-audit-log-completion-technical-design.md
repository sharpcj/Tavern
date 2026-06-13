文章标题：M13 操作日志与审计完善技术方案

# 一、背景

M11 建立了 AuditLog 基础模型和 write_audit_log 工具，M12 管理后台的部分操作已接入日志。但日志覆盖仍不完整，部分操作使用了不精确的 action 类型。

M13 的目标是补齐缺失的日志接入点，统一日志 action 类型，确保关键管理操作可追溯。

# 二、当前日志覆盖分析

## 已覆盖

| 操作 | 接入点 | action 类型 |
| --- | --- | --- |
| 提交举报 | reports/views.py | REPORT_CREATED |
| 处理举报 | moderation/services.py | REPORT_HANDLED |
| 隐藏内容 | moderation/services.py | CONTENT_HIDDEN |
| 删除内容 | moderation/services.py | CONTENT_DELETED |
| 警告用户 | moderation/services.py | USER_WARNED |
| 限制用户 | moderation/services.py | USER_RESTRICTED |
| 封禁用户 | moderation/services.py | USER_BANNED |
| 管理员隐藏动态 | common/admin_views.py | CONTENT_HIDDEN |
| 管理员删除动态 | common/admin_views.py | CONTENT_DELETED |
| 管理员隐藏评论 | common/admin_views.py | CONTENT_HIDDEN |
| 管理员删除评论 | common/admin_views.py | CONTENT_DELETED |
| 管理员隐藏照片 | common/admin_views.py | CONTENT_HIDDEN |
| 管理员隐藏相册 | common/admin_views.py | CONTENT_HIDDEN |
| 用户审核 | accounts/admin_views.py | REPORT_HANDLED（不精确） |
| 角色变更 | accounts/admin_views.py | USER_WARNED（不精确） |
| 账号状态变更 | accounts/admin_views.py | USER_WARNED/RESTRICTED/BANNED |
| 活动状态变更 | activities/admin_views.py | REPORT_HANDLED（不精确） |
| 活动删除 | activities/admin_views.py | CONTENT_DELETED |

## 缺失

| 操作 | 说明 |
| --- | --- |
| 公告发布 | announcements 模块未接入日志 |
| 公告编辑 | announcements 模块未接入日志 |
| 公告删除 | announcements 模块未接入日志 |
| 活动状态变更（用户侧） | 发起人修改活动状态未记录 |

# 三、方案

## 新增 AuditAction

```python
USER_REVIEWED = "user_reviewed", "审核用户"
ROLE_CHANGED = "role_changed", "角色变更"
ACCOUNT_STATUS_CHANGED = "account_status_changed", "账号状态变更"
ANNOUNCEMENT_CREATED = "announcement_created", "发布公告"
ANNOUNCEMENT_UPDATED = "announcement_updated", "编辑公告"
ANNOUNCEMENT_DELETED = "announcement_deleted", "删除公告"
ACTIVITY_STATUS_CHANGED = "activity_status_changed", "活动状态变更"
ACTIVITY_DELETED = "activity_deleted", "删除活动"
```

## 接入点修改

| 文件 | 修改 |
| --- | --- |
| audit_logs/models.py | 新增 8 个 AuditAction |
| accounts/admin_views.py | 审核用 USER_REVIEWED，角色变更用 ROLE_CHANGED，状态变更用 ACCOUNT_STATUS_CHANGED |
| activities/admin_views.py | 状态变更用 ACTIVITY_STATUS_CHANGED，删除用 ACTIVITY_DELETED |
| announcements/views.py | 发布/编辑/删除接入日志 |

## 边界决策

1. 用户侧操作（如自己删动态、自己报名活动）不记录 AuditLog，只记录管理操作
2. 活动发起人修改活动状态不记录 AuditLog（属于用户侧操作）
3. 公告的发布/编辑/删除全部记录（因为只有管理员可操作）
4. 不新增数据库迁移（只改 choices 枚举值，不改变表结构）

# 四、验收标准

- AuditAction 枚举覆盖所有管理操作类型
- 用户审核使用 USER_REVIEWED
- 角色变更使用 ROLE_CHANGED
- 账号状态变更使用 ACCOUNT_STATUS_CHANGED
- 公告发布/编辑/删除记录日志
- 活动状态变更（管理侧）使用 ACTIVITY_STATUS_CHANGED
- 活动删除使用 ACTIVITY_DELETED
- 后端检查、测试、OpenAPI、前端构建全部通过
