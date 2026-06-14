# Tavern —— 高中同班同学社区网站

Tavern 是一个面向高中同班同学的私密线上社区。它不是公开论坛，也不是泛社交平台，而是一个只服务于本班同学的长期空间，用于身份审核、生活分享、评论互动、活动组织、公告发布、相册沉淀、生日祝福、举报处理和后台治理。

当前项目已经完成第一版核心功能、实时刷新、P0 安全加固、头像上传与移动端体验优化。本文档按当前代码和最新需求更新。

## 核心原则

- 身份可信：注册必须填写真实姓名，经管理员审核后才能访问站内内容。
- 访问受限：未登录、未审核、被封禁用户不得访问内部内容。
- 分享自愿：用户可以选择是否完善资料、是否公开联系方式、是否展示生日月份。
- 隐私优先：联系方式、审核材料、举报记录、管理日志不向普通用户展示。
- 内容可管：动态、评论、照片、活动说明、生日祝福均可举报、可管理、可追溯。
- 不做私信和小群：不提供站内私信、临时小群、私密群聊、点对点聊天。
- 活动实名：活动发起、报名、接龙、投票、费用确认必须使用真实姓名。
- 身份展示：动态、评论、照片说明、生日祝福支持“真实姓名 / 昵称”展示，不做完全不可追溯匿名。
- 生日最小展示：只展示生日月份和本月生日同学，不展示出生年份和具体日期。
- 数据可恢复：生产部署包含数据库和媒体文件备份 / 恢复脚本。

产品与治理总纲见 `docs/classmate-community-whitepaper.md`。白皮书仍是产品原则来源；当前代码中的阶段性实现差异以各模块技术方案和本文档记录。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.14 + Django 6.0 + Django REST Framework |
| 认证 | JWT（djangorestframework-simplejwt，access + refresh） |
| API 文档 | OpenAPI 3（drf-spectacular，生产默认关闭） |
| 数据库 | MySQL 8.4（开发期可使用 SQLite；当前开发驱动为 PyMySQL） |
| 缓存 / 限流 | Redis 7.4 预留，DRF throttle 已配置 |
| 实时刷新 | SSE + cursor 补拉，支持前台实时刷新和断线补偿 |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router |
| 部署 | Docker Compose（Nginx + Gunicorn/Uvicorn 能力预留 + MySQL + Redis） |

## 项目结构

```text
Tavern/
├── AGENTS.md                           # AI 编码 Agent 工作规则
├── README.md                           # 项目说明
├── pyproject.toml                      # Python 项目配置（uv）
├── manage.py                           # Django 管理入口
├── tavern/                             # Django 项目配置
│   ├── asgi.py                         # ASGI 入口，SSE 调试建议使用 uvicorn
│   ├── urls.py                         # 根路由、OpenAPI、开发期 media 路由
│   └── settings/
│       ├── base.py                     # 基础配置
│       ├── development.py              # 开发配置
│       ├── test.py                     # 测试配置
│       └── production.py               # 生产配置
├── apps/                               # Django 应用模块
│   ├── accounts/                       # 用户、认证、角色、审核
│   ├── profiles/                       # 同学资料、通讯录、隐私设置、头像
│   ├── posts/                          # 首页动态
│   ├── comments/                       # 动态评论和扁平回复模型
│   ├── activities/                     # 活动、报名、投票、接龙
│   ├── albums/                         # 相册、照片、照片评论
│   ├── birthdays/                      # 生日月份、生日祝福
│   ├── announcements/                  # 公告、置顶、已读
│   ├── reports/                        # 举报
│   ├── moderation/                     # 内容处理、限制、封禁
│   ├── audit_logs/                     # 操作日志
│   ├── notifications/                  # 系统通知、SSE 实时事件
│   └── common/                         # 权限、分页、媒体、错误码、通用视图
├── frontend/                           # Vue 3 前端
│   └── src/
│       ├── api/                        # API 客户端与模块请求封装
│       ├── components/                 # 通用组件，如 UserAvatar、ReportButton
│       ├── layouts/                    # 前台 / 管理后台布局
│       ├── pages/                      # 页面组件
│       ├── router/                     # 路由与权限守卫
│       ├── stores/                     # Pinia 状态管理
│       └── styles/                     # 全局样式与移动端适配
├── deploy/                             # 部署配置
│   ├── docker-compose.dev.yml          # 开发环境 MySQL / Redis
│   ├── docker-compose.prod.yml         # 生产环境 Nginx / Django / MySQL / Redis
│   ├── Dockerfile                      # 生产镜像
│   ├── .env.prod.example               # 生产环境变量模板
│   ├── nginx/                          # Nginx 配置，生产不直接公开 /media/
│   └── scripts/                        # 数据库和媒体文件备份 / 恢复脚本
└── docs/                               # 白皮书、概要设计、模块方案和实时刷新方案
```

## 已实现功能

| 模块 | 当前实现 |
| --- | --- |
| M01 工程基础设施 | Django 分层配置、uv 依赖、Vue 3 前端、OpenAPI、Docker 开发环境 |
| M02 账号与身份审核 | 邮箱登录、真实姓名注册、JWT、refresh token、审核状态、管理审核 |
| M03 权限与角色 | 普通同学 / 管理会员 / 超级管理员、账号限制 / 封禁、管理接口权限 |
| M04 个人资料与通讯录 | 资料维护、头像上传、通讯录、联系方式独立可见范围、生日月份设置 |
| M05 通用内容与媒体 | 内容状态、软删除、图片上传校验、媒体元数据、短期签名媒体访问 |
| M06 首页动态与评论 | 动态发布、本地图片上传、分类、置顶、两级展示的扁平回复、通知接入 |
| M07 活动模块 | 聚会报名、投票、接龙、实名快照、状态管理、管理删除 |
| M08 公告与置顶 | 公告发布、置顶、有效期、已读确认、首页最新公告展示 |
| M09 相册与照片 | 相册、照片上传、照片详情、上一张 / 下一张、照片评论与回复 |
| M10 生日祝福 | 本月生日同学、祝福留言、生日展示开关、祝福治理 |
| M11 举报与治理 | 动态、评论、照片、照片评论、活动、生日祝福等举报与处理 |
| M12 管理后台 | 用户审核、用户管理、内容管理、活动管理、举报处理、操作日志查看 |
| M13 操作日志 | 审核、角色、账号状态、公告、活动、内容治理、举报处理等日志 |
| M14 系统通知 | 审核结果、公告、评论 / 回复、活动状态通知，未读数和已读操作 |
| M15 部署与备份 | 生产 Docker Compose、Nginx、安全配置、数据库和媒体备份 / 恢复脚本 |
| 实时刷新 | SSE 事件流、`/events/since/` 补拉、动态 / 评论 / 公告 / 相册 / 通知刷新 |
| 体验优化 | 社区公约注册门控、移动端导航抽屉、举报弹框优化、头像兜底不暴露姓名首字 |

## 关键接口分组

| 分组 | 路径示例 | 说明 |
| --- | --- | --- |
| 健康检查 | `GET /api/v1/health/` | 生产容器健康检查 |
| 认证 | `/api/v1/auth/` | 注册、登录、刷新 token、当前用户 |
| 当前资料 | `/api/v1/me/profile/` | 个人资料、联系方式可见范围、头像 |
| 通讯录 | `/api/v1/classmates/` | 同学列表和详情，使用 `account_id` UUID |
| 动态 | `/api/v1/posts/` | 动态列表、详情、置顶、评论 |
| 活动 | `/api/v1/activities/` | 活动列表、详情、报名、投票、接龙 |
| 公告 | `/api/v1/announcements/` | 公告、置顶公告、已读确认 |
| 相册 | `/api/v1/albums/`、`/api/v1/photos/` | 相册、照片、照片评论 |
| 生日 | `/api/v1/birthdays/` | 本月生日、生日祝福 |
| 举报 | `/api/v1/reports/` | 普通用户提交举报 |
| 通知 | `/api/v1/notifications/` | 系统通知、未读数、已读 |
| 实时事件 | `/api/v1/events/stream/`、`/api/v1/events/since/` | SSE 与 cursor 补拉 |
| 受控媒体 | `/api/v1/media/<id>/file/?token=...` | 短期签名媒体访问 |
| 管理后台 | `/api/v1/admin/...` | 用户、内容、活动、举报、操作日志管理 |

## 快速开始

### 环境要求

- Python 3.14+
- Node.js 20+
- uv
- Docker 和 Docker Compose

### 1. 启动开发数据库

```bash
docker compose -f deploy/docker-compose.dev.yml up -d
```

### 2. 安装后端依赖

```bash
uv sync
```

### 3. 运行数据库迁移

```bash
uv run python manage.py migrate
```

### 4. 写入手动测试种子数据（可选）

```bash
uv run python manage.py seed_data --clean
```

种子账号统一密码为 `Pass1234!`，常用账号：

- `admin@tavern.local`：超级管理员
- `zhangwei@tavern.local`：管理会员
- `lina@tavern.local`：普通同学

### 5. 启动后端开发服务器

普通接口调试：

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

如果要调试 SSE 实时刷新，建议使用 ASGI / Uvicorn：

```bash
uv run uvicorn tavern.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### 6. 安装前端依赖并启动

```bash
cd frontend
npm install
npm run dev
```

启用 SSE 调试：

```bash
npm run dev:sse
```

### 7. 访问

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/api/docs/（开发环境默认开启，生产默认关闭）
- Django 管理后台：http://localhost:8000/admin/

手机同 Wi-Fi 调试时，前端 API 会默认使用当前访问主机名的 `8000` 端口；后端需监听 `0.0.0.0:8000`。

## 验证命令

### 后端

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
uv run python manage.py spectacular --file /tmp/tavern-schema.yml --validate
```

### 前端

```bash
cd frontend
npm run typecheck
npm run build
```

### 部署配置

```bash
docker compose -f deploy/docker-compose.dev.yml config
docker compose -f deploy/docker-compose.prod.yml config
```

## 生产部署概要

1. 复制并填写生产环境变量：

```bash
cp deploy/.env.prod.example deploy/.env.prod
```

2. 构建并启动：

```bash
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

3. 运行迁移：

```bash
docker compose -f deploy/docker-compose.prod.yml exec django python manage.py migrate --noinput
```

4. 执行数据库备份：

```bash
bash deploy/scripts/backup-db.sh
```

5. 执行媒体文件备份：

```bash
bash deploy/scripts/backup-media.sh
```

生产环境注意事项：

- `DEBUG=False`。
- `ENABLE_API_DOCS=False`，默认关闭 `/api/docs/` 和 `/api/schema/`。
- Nginx 不直接公开 `/media/`，媒体文件通过后端短期签名 URL 访问。
- 登录、注册、上传、评论、举报、SSE 等接口启用限流。
- 生产必须配置 HTTPS、明确 `ALLOWED_HOSTS`、CORS 白名单和安全响应头。

## 文档索引

- `docs/classmate-community-whitepaper.md`：产品与治理总纲。
- `docs/classmate-community-hld.md`：按当前代码更新后的概要设计。
- `docs/project-development-module-plan.md`：第一版模块规划与当前进展。
- `docs/m01-*.md` 至 `docs/m15-*.md`：各模块技术方案。
- `docs/realtime-events-sse-technical-design.md`：SSE 实时事件推送方案。

## 许可证

内部项目，仅供班级同学使用。
