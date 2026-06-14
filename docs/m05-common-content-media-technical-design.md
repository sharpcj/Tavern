文章标题：M05 通用内容与媒体基础技术方案

# 一、背景

## 项目背景

根据 `project-development-module-plan.md`，M05「通用内容与媒体基础」是阶段 3 的公共能力模块，应在 M06「首页动态与评论」之前完成。但实际开发中 M06 先于 M05 实现，导致 `DisplayMode` 枚举、软删除字段、内容状态枚举等能力散落在 `apps/posts/` 和 `apps/comments/` 中，无法被后续 M09（相册）、M10（生日祝福）等模块复用。

M05 的目标是将这些公共能力提取到 `apps/common/`，并补充媒体元数据模型和上传安全校验工具，为后续内容模块提供统一基础。

## 系统背景

- `apps/common/` 已有权限类、异常处理、错误码、分页等公共能力。
- `apps/posts/models.py` 中定义了 `DisplayMode`、`PostStatus` 枚举和软删除字段。
- `apps/comments/models.py` 引用了 `apps.posts.models.DisplayMode`，并独立定义了 `CommentStatus`。
- 当前没有媒体元数据模型和上传校验工具。

# 二、需求描述

## 需求来源

| 来源 | 需求内容 |
| --- | --- |
| 模块规划 | 媒体元数据模型：上传人、文件路径、类型、大小、宽高、关联对象 |
| 模块规划 | 上传安全校验：限制文件大小、类型、数量，服务端校验图片 |
| 模块规划 | 媒体受控访问：图片和附件不提供永久公开敏感直链 |
| 模块规划 | 内容状态枚举：draft、published、hidden、deleted、pending_review |
| 模块规划 | 软删除基础字段：deleted_at、deleted_by、delete_reason |
| 模块规划 | 身份展示工具：根据 display_mode 返回真实姓名或昵称展示身份，后台保留真实作者 |
| 现有代码 | DisplayMode 枚举需从 posts 移到 common |
| 现有代码 | Post 和 Comment 的软删除字段需统一为公共 Mixin |

## 本阶段明确范围

M05 实现：

- 公共枚举：`ContentStatus`（draft / published / hidden / deleted / pending_review）、`DisplayMode`（real_name / nickname）
- 软删除抽象基类 `SoftDeletableModel`：提供 `deleted_at`、`deleted_by`、`delete_reason` 字段和 `soft_delete()` 方法
- 展示名称工具函数：根据 `display_mode` 和作者信息返回展示名称
- 媒体元数据模型 `Media`：上传人、文件、类型、大小、宽高、关联对象（GenericForeignKey）
- 上传安全校验工具：文件大小、类型白名单、图片校验
- 重构 `apps/posts/` 和 `apps/comments/` 使用 M05 公共能力

M05 不实现：

- 实际的文件上传接口（留到 M09 相册或后续文件上传模块）
- 媒体文件的物理存储和访问控制视图
- 前端页面变更

# 三、技术方案

## 方案描述

M05 在 `apps/common/` 中新增以下公共能力：

1. **`apps/common/enums.py`**：集中管理跨模块共享的枚举，包括 `ContentStatus` 和 `DisplayMode`。`DisplayMode` 从 `apps/posts/models.py` 移出。

2. **`apps/common/models.py`**：新增 `SoftDeletableModel` 抽象基类和 `Media` 媒体元数据模型。`SoftDeletableModel` 提供 `deleted_at`、`deleted_by`、`delete_reason` 三个字段和 `soft_delete(user, reason)` 方法。`Media` 使用 GenericForeignKey 关联任意业务对象。

3. **`apps/common/display.py`**：提供 `get_display_name(obj)` 工具函数，根据对象的 `display_mode` 和 `author` 返回展示名称。

4. **`apps/common/validators.py`**：提供文件上传校验工具函数，包括文件大小限制、MIME 类型白名单、图片格式校验。

5. 重构 `apps/posts/models.py` 和 `apps/comments/models.py`：使用 `apps.common.enums` 中的枚举和 `SoftDeletableModel` 基类。

## 关联模块具体方案描述

### 数据层 / 存储

**`ContentStatus` 枚举（`apps/common/enums.py`）：**

| 值 | 标签 | 说明 |
| --- | --- | --- |
| `draft` | 草稿 | 用户保存但未发布 |
| `published` | 已发布 | 正常可见 |
| `hidden` | 已隐藏 | 管理员隐藏，普通用户不可见 |
| `deleted` | 已删除 | 软删除 |
| `pending_review` | 待审核 | 内容待管理员审核 |

**`DisplayMode` 枚举（`apps/common/enums.py`）：**

| 值 | 标签 |
| --- | --- |
| `real_name` | 真实姓名 |
| `nickname` | 昵称 |

**`SoftDeletableModel` 抽象基类（`apps/common/models.py`）：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `deleted_at` | DateTime null | 删除时间 |
| `deleted_by` | FK User null | 删除操作人 |
| `delete_reason` | CharField blank | 删除原因 |

方法：
- `soft_delete(user, reason="")`：设置删除状态和时间戳

**`Media` 模型（`apps/common/models.py`）：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `uploader` | FK User | 上传人 |
| `file` | FileField | 文件 |
| `original_name` | CharField | 原始文件名 |
| `content_type` | CharField | MIME 类型 |
| `size` | PositiveIntegerField | 文件大小（字节） |
| `width` | PositiveIntegerField null | 图片宽度 |
| `height` | PositiveIntegerField null | 图片高度 |
| `content_object` | GenericForeignKey | 关联的业务对象 |
| `created_at` | DateTime | 上传时间 |

### 后端服务 / API

M05 不新增 API 接口。媒体上传接口留到后续模块实现。

### 前端 / 客户端

M05 不涉及前端变更。

### 基础设施 / 第三方依赖

M05 不新增外部依赖。图片校验使用 Python 标准库 `imghdr` 或 Pillow（已在依赖中）。

## 实施步骤

1. 创建 `apps/common/enums.py`，定义 `ContentStatus` 和 `DisplayMode`。
2. 更新 `apps/common/models.py`，添加 `SoftDeletableModel` 和 `Media`。
3. 创建 `apps/common/display.py`，实现 `get_display_name()`。
4. 创建 `apps/common/validators.py`，实现上传校验工具。
5. 重构 `apps/posts/models.py`：移除 `DisplayMode` 和 `PostStatus`，改用 `apps.common.enums`；`Post` 继承 `SoftDeletableModel`。
6. 重构 `apps/comments/models.py`：移除 `CommentStatus`，改用 `apps.common.enums`；`Comment` 继承 `SoftDeletableModel`。
7. 更新所有引用 `apps.posts.models.DisplayMode` 的代码。
8. 生成迁移并运行测试。

## 验收标准

- `DisplayMode` 和 `ContentStatus` 枚举在 `apps/common/enums.py` 中定义，posts 和 comments 从 common 导入。
- `Post` 和 `Comment` 继承 `SoftDeletableModel`，删除操作使用 `soft_delete()` 方法。
- `Media` 模型可用，支持 GenericForeignKey 关联。
- 上传校验工具函数可用。
- 现有 41 个测试全部通过。
- `python manage.py check`、`makemigrations --check --dry-run`、OpenAPI 生成、前端构建通过。
