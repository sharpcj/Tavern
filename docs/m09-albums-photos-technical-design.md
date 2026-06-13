文章标题：M09 相册与回忆照片技术方案

# 一、背景

M09 实现班级相册与回忆照片模块，用于保存高中校园、毕业照、老师合影、聚会照片、同学近况和班级纪念等图片内容。

根据白皮书，相册模块需要支持创建相册、上传图片、图片说明、相册分类、照片评论、管理员审核或删除照片，并支持按活动关联照片。相册属于班级内部内容，必须遵守已审核用户访问、图片上传安全、内容可管理和隐私优先原则。

M09 依赖 M05 通用内容与媒体基础、M06 评论/内容展示经验和 M07 活动模块。M05 已提供 `Media` 元数据模型、上传校验工具、`ContentStatus`、`DisplayMode` 和软删除能力，本模块将在此基础上实现真实图片上传和相册业务。

# 二、需求描述

## 需求来源

| 来源 | 需求内容 |
| --- | --- |
| 白皮书 | 创建相册、上传图片、图片说明、相册分类、评论照片、管理员审核或删除照片、按活动关联照片 |
| 模块规划 | 相册模型、照片上传、照片评论、活动照片关联、相册管理、前端相册页面 |
| M05 | 媒体元数据、上传安全校验、内容状态、软删除、展示身份工具 |
| 用户确认 | M09 实现本地图片上传；照片评论在 albums 内实现 PhotoComment；相册可选关联活动；已审核同学可创建相册和上传照片；API 层做访问控制，文件访问先使用开发期 media URL |

## 本阶段范围

M09 实现：

- 相册模型 `Album`
- 照片模型 `Photo`
- 照片评论模型 `PhotoComment`
- 图片上传 API，使用本地 `media/` 存储并记录 `common.Media` 元数据
- 相册列表、详情、创建、编辑、删除 API
- 照片上传、详情、删除 API
- 照片评论发布和删除 API
- 相册可选关联活动
- 前端相册列表、创建相册、相册详情/照片墙、上传照片、照片详情评论

M09 不实现：

- 对象存储接入
- 生产级媒体鉴权下载/防盗链
- 专门的管理后台页面
- 举报处理闭环（留到 M11）

# 三、技术方案

## 数据模型

### 相册 Album

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `title` | CharField | 相册标题 |
| `description` | TextField | 相册说明 |
| `category` | CharField choices | 相册分类 |
| `creator` | FK User | 创建人 |
| `creator_name_snapshot` | CharField | 创建人姓名快照 |
| `activity` | FK Activity null | 可选关联活动 |
| `cover_photo` | FK Photo null | 封面照片 |
| `status` | CharField | 内容状态 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

相册分类：

- `campus`：高中校园
- `graduation`：毕业照
- `teacher`：老师合影
- `gathering`：聚会照片
- `classmate_life`：同学近况
- `memory`：班级纪念

### 照片 Photo

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `album` | FK Album | 所属相册 |
| `uploader` | FK User | 上传人 |
| `uploader_name_snapshot` | CharField | 上传人姓名快照 |
| `media` | OneToOne Media | 媒体元数据 |
| `caption` | TextField | 图片说明 |
| `display_mode` | CharField | 图片说明展示身份：真实姓名 / 昵称 |
| `status` | CharField | 内容状态 |
| `created_at` | DateTime | 上传时间 |
| `updated_at` | DateTime | 更新时间 |

### 照片评论 PhotoComment

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `photo` | FK Photo | 所属照片 |
| `author` | FK User | 评论作者 |
| `content` | TextField | 评论内容 |
| `display_mode` | CharField | 展示身份：真实姓名 / 昵称 |
| `status` | CharField | 内容状态 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

## API

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/albums/` | IsApprovedClassmate | 相册列表，支持分类和活动筛选 |
| `POST` | `/api/v1/albums/` | IsApprovedClassmate | 创建相册 |
| `GET` | `/api/v1/albums/{id}/` | IsApprovedClassmate | 相册详情，含照片列表 |
| `PATCH` | `/api/v1/albums/{id}/` | 创建人 | 编辑相册基本信息 |
| `DELETE` | `/api/v1/albums/{id}/` | 创建人或管理会员以上 | 软删除相册 |
| `POST` | `/api/v1/albums/{id}/photos/` | IsApprovedClassmate | 上传照片 |
| `GET` | `/api/v1/photos/{id}/` | IsApprovedClassmate | 照片详情，含评论 |
| `DELETE` | `/api/v1/photos/{id}/` | 上传人或管理会员以上 | 软删除照片 |
| `POST` | `/api/v1/photos/{id}/comments/` | IsApprovedClassmate | 发布照片评论 |
| `DELETE` | `/api/v1/photo-comments/{id}/` | 作者或管理会员以上 | 删除照片评论 |

## 前端

新增路由：

| 路由 | 页面 |
| --- | --- |
| `/albums` | 相册列表页 |
| `/albums/create` | 创建相册页 |
| `/albums/:id` | 相册详情页 / 照片墙 |
| `/photos/:id` | 照片详情页 / 评论区 |

## 图片上传安全

M09 使用 M05 的上传校验工具：

- 限制文件大小，默认 10MB
- 限制图片 MIME 类型：JPEG、PNG、GIF、WebP
- 上传后记录 `Media` 元数据
- API 只允许已审核用户上传
- 本阶段返回开发期 `media.url`，生产期再接受控访问或对象存储

# 四、异常和边界场景

| 场景 | 处理 |
| --- | --- |
| 未审核用户访问相册 | 403 |
| 上传非图片文件 | 400 |
| 上传超过大小限制 | 400 |
| 删除他人相册 | 403，管理会员以上除外 |
| 删除他人照片 | 403，管理会员以上除外 |
| 查看已删除相册或照片 | 404 |
| 相册关联不存在的活动 | 400 |
| 照片评论为空 | 400 |

# 五、风险与取舍

| 风险 / 取舍 | 影响 | 解决措施 | 验证方式 |
| --- | --- | --- | --- |
| 本阶段使用本地 media 文件 | 生产环境扩展性有限 | 后续部署阶段接对象存储或 Nginx 受控访问 | 本地上传测试 |
| 照片评论未复用 comments.Comment 表 | 短期有一套独立评论模型 | 避免改动 M06 动态评论表结构，后续 M11 举报治理统一抽象内容对象 | 回归 M06 测试 |
| 文件 URL 先开发期直出 | 生产隐私保护不足 | API 层先严格限制列表/详情；生产期补媒体鉴权 | 权限测试 + 后续部署方案 |

# 六、验收标准

- 已审核用户可以创建相册
- 已审核用户可以上传图片到相册
- 图片上传会生成 `Media` 元数据
- 相册可按分类和活动筛选
- 相册详情展示照片墙
- 照片详情展示说明和评论
- 用户可以评论照片
- 用户可删除自己的相册、照片和评论
- 管理会员和超级管理员可删除不合适相册、照片和评论
- `python manage.py check`、`makemigrations --check --dry-run`、`python manage.py test`、OpenAPI、前端 typecheck 和 build 全部通过
