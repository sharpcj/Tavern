# Tavern —— 高中同班同学社区网站

一个面向高中同班同学的私密线上社区。不是公开论坛，不是泛社交平台，而是一个只服务于本班同学的长期空间，用于分享近况、沉淀回忆、组织活动、发布公告、维护同学通讯录。

## 核心原则

- 身份可信：注册必须填写真实姓名，经管理员审核后才能访问站内内容
- 访问受限：未登录和未审核用户不得访问内部内容，站点不被搜索引擎收录
- 分享自愿：用户可以选择是否完善资料、是否公开联系方式、是否展示生日月份
- 隐私优先：联系方式、审核材料、举报记录、管理日志不向普通用户展示
- 内容可管：动态、评论、照片、活动说明、生日祝福均可举报、可管理、可追溯
- 不做私信和小群：不提供站内私信、临时小群、私密群聊、点对点聊天
- 活动实名：活动发起、报名、接龙、费用确认必须使用真实姓名
- 生日最小展示：只展示生日月份和本月生日同学，不展示出生年份和具体日期

详细产品原则见 `classmate-community-whitepaper.md`。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.14 + Django 6.0 + Django REST Framework |
| 认证 | JWT（djangorestframework-simplejwt） |
| API 文档 | OpenAPI 3（drf-spectacular） |
| 数据库 | MySQL 8.4（开发期兼容 SQLite） |
| 缓存 | Redis 7.4 |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router |
| 部署 | Docker Compose（Nginx + Gunicorn + MySQL + Redis） |

## 项目结构

```text
Tavern/
├── classmate-community-whitepaper.md   # 产品与治理总纲
├── AGENTS.md                           # AI 编码 Agent 工作规则
├── pyproject.toml                      # Python 项目配置（uv）
├── tavern/                             # Django 项目配置
│   └── settings/
│       ├── base.py                     # 基础配置
│       ├── development.py              # 开发配置
│       ├── test.py                     # 测试配置
│       └── production.py               # 生产配置
├── apps/                               # Django 应用模块
│   ├── accounts/                       # 用户、认证、角色、审核
│   ├── profiles/                       # 同学资料、通讯录、隐私设置
│   ├── posts/                          # 首页动态
│   ├── comments/                       # 评论和回复
│   ├── activities/                     # 活动、报名、投票、接龙
│   ├── albums/                         # 相册、照片
│   ├── birthdays/                      # 生日月份、生日祝福
│   ├── announcements/                  # 公告、置顶、已读
│   ├── reports/                        # 举报
│   ├── moderation/                     # 内容处理、限制、封禁
│   ├── audit_logs/                     # 操作日志
│   ├── notifications/                  # 系统通知
│   └── common/                         # 通用基类、权限、工具函数
├── frontend/                           # Vue 3 前端
│   └── src/
│       ├── api/                        # API 客户端
│       ├── components/                 # 通用组件
│       ├── layouts/                    # 布局组件
│       ├── pages/                      # 页面组件
│       ├── router/                     # 路由配置
│       └── stores/                     # Pinia 状态管理
├── deploy/                             # 部署配置
│   ├── docker-compose.dev.yml          # 开发环境
│   ├── docker-compose.prod.yml         # 生产环境
│   ├── Dockerfile                      # 生产镜像
│   ├── nginx/                          # Nginx 配置
│   ├── scripts/                        # 备份/恢复脚本
│   └── .env.prod.example              # 生产环境变量模板
└── docs/                               # 技术方案文档
    ├── classmate-community-hld.md      # 概要设计
    ├── project-development-module-plan.md  # 模块规划
    └── mXX-*.md                        # 各模块技术方案
```

## 功能模块

| 模块 | 说明 |
| --- | --- |
| M01 工程基础设施 | 后端工程结构、前端工程、配置分层、Docker 开发环境 |
| M02 账号与身份审核 | 注册、登录、JWT、真实姓名、邀请码、管理员审核 |
| M03 权限与角色 | 角色、账号状态、权限类、隐私字段过滤、统一错误码 |
| M04 个人资料与通讯录 | 资料维护、通讯录、搜索筛选、联系方式可见范围 |
| M05 通用内容与媒体 | 上传校验、媒体元数据、内容状态、软删除、展示模式 |
| M06 首页动态与评论 | 动态发布、图片、标签、置顶、评论、回复 |
| M07 活动模块 | 聚会报名、投票、接龙、活动状态、实名快照 |
| M08 公告与置顶 | 公告发布、置顶、有效期、已读确认 |
| M09 相册与回忆照片 | 相册、照片上传、照片说明、照片评论、活动关联 |
| M10 生日祝福板块 | 本月生日同学、生日祝福、生日展示开关 |
| M11 举报与治理 | 举报入口、举报列表、处理动作、操作日志 |
| M12 管理后台 | 用户审核、用户管理、内容管理、活动管理 |
| M13 操作日志与审计 | 审核、删除、封禁、角色变更、公告等日志 |
| M14 系统通知 | 审核结果、公告、评论回复、活动状态通知 |
| M15 部署与备份 | Docker Compose、Nginx、备份恢复、安全配置 |

## 快速开始

### 环境要求

- Python 3.14+
- Node.js 20+
- uv（Python 包管理器）
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

### 4. 启动后端开发服务器

```bash
uv run python manage.py runserver
```

### 5. 安装前端依赖并启动

```bash
cd frontend
npm install
npm run dev
```

### 6. 访问

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/api/docs/
- 管理后台：http://localhost:8000/admin/

## 验证命令

### 后端

```bash
uv run python manage.py check          # 系统检查
uv run python manage.py test           # 运行测试（当前 90 个）
uv run python manage.py spectacular --file /tmp/schema.yml --validate  # OpenAPI 验证
```

### 前端

```bash
cd frontend
npm run typecheck   # 类型检查
npm run build       # 生产构建
```

### 部署

```bash
docker compose -f deploy/docker-compose.dev.yml config   # 开发配置验证
docker compose -f deploy/docker-compose.prod.yml config  # 生产配置验证
```

## 生产部署

1. 复制环境变量模板并填入真实值：

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

4. 数据库备份：

```bash
bash deploy/scripts/backup-db.sh
```

## 文档

- `classmate-community-whitepaper.md` —— 产品与治理总纲
- `AGENTS.md` —— AI 编码 Agent 工作规则
- `docs/classmate-community-hld.md` —— 概要设计文档
- `docs/project-development-module-plan.md` —— 模块开发规划
- `docs/mXX-*.md` —— 各模块技术方案文档

## 许可证

内部项目，仅供班级同学使用。
