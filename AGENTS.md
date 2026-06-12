# AGENTS.md

本文件是本项目给 AI 编码 Agent 的全局工作规则。任何 Agent 在本仓库内进行代码生成、修改、重构、测试、部署配置或文档维护时，都必须优先阅读并遵守本文件。

## 1. 项目定位

本项目是一个面向高中同班同学的内部社区网站，用于同学身份审核、生活分享、评论互动、活动组织、公告发布、相册沉淀、生日祝福、举报处理和后台治理。

项目以 `classmate-community-whitepaper.md` 作为产品与治理总纲。该白皮书描述了项目的核心原则、功能边界、隐私要求、免责声明、禁止事项和第一版上线范围。

除非用户明确要求修改白皮书，否则 Agent 不得修改以下文件：

- `classmate-community-whitepaper.md`

如果实现过程中发现白皮书与技术实现存在冲突，先向用户说明冲突和建议处理方式，不要擅自改动白皮书内容。

## 2. 核心产品原则

所有实现都必须符合以下原则：

1. 身份可信：用户注册必须填写真实姓名，并通过管理员审核后才能访问站内内容。
2. 访问受限：网站不是公开论坛，未登录和未审核用户不得访问内部内容。
3. 分享自愿：用户可以选择是否完善资料、是否公开联系方式、是否展示生日月份。
4. 隐私优先：默认采取保守隐私策略，联系方式、审核材料、举报记录、管理日志不得向普通用户展示。
5. 内容可管：动态、评论、照片、活动说明、生日祝福等内容必须可举报、可管理、可追溯。
6. 不做私信和小群：禁止实现站内私信、临时小群、私密群聊、点对点聊天等不可控沟通功能。
7. 活动实名：凡涉及活动发起、报名、接龙、费用确认、现场名单统计等行为，必须使用真实姓名，不支持匿名参与。
8. 匿名仅用于前台展示：动态、评论、照片说明、生日祝福可以选择匿名展示，但后台必须保留真实账号以便治理追溯。
9. 生日最小展示：生日祝福板块只允许展示生日月份和本月生日同学，不得展示出生年份和具体日期。
10. 数据可备份、可恢复：数据库、上传文件和关键配置必须考虑备份与恢复。

## 3. 技术栈约束

本项目采用以下技术栈：

### 后端

- Python
- Django
- Django REST Framework
- MySQL
- Redis，作为缓存、限流和 Celery broker 的预留组件
- Celery，第一版可以预留，涉及异步任务时再启用
- JWT 认证，优先使用 `djangorestframework-simplejwt`
- OpenAPI 文档，优先使用 `drf-spectacular`

### 前端

- 前后端分离架构
- 推荐 Vue 3 + TypeScript + Vite
- 推荐使用 Pinia、Vue Router、Element Plus 或 Naive UI
- 前端不得绕过后端权限判断。所有敏感权限必须由后端校验。

### 数据库

- 正式目标数据库是 MySQL
- 本地早期原型可以使用 SQLite，但核心业务开发和上线前必须使用 MySQL 验证
- 数据库字符集必须使用 `utf8mb4`
- 不得把生产数据库作为本地开发调试库

### 部署

- 推荐 Docker Compose 部署
- 开发期可以本机运行 Django 和前端，MySQL/Redis 使用 Docker
- 上线期推荐 Nginx + Django/Gunicorn + MySQL + Redis 的 Docker Compose 结构
- 不使用 Kubernetes，除非用户明确要求

## 4. 推荐仓库结构

如需初始化项目，优先采用以下结构：

```text
Tavern/
  AGENTS.md
  classmate-community-whitepaper.md
  backend/
    manage.py
    pyproject.toml
    uv.lock
    config/
    apps/
      accounts/
      profiles/
      posts/
      comments/
      activities/
      albums/
      birthdays/
      announcements/
      reports/
      moderation/
      audit_logs/
      notifications/
      common/
  frontend/
    package.json
    src/
  deploy/
    docker-compose.dev.yml
    docker-compose.prod.yml
    nginx/
  docs/
```

如果项目已有结构，Agent 应先阅读现有目录和配置，再提出兼容现有结构的修改方案，不要盲目重建项目。

## 5. Python 环境规则

优先使用 `uv` 管理 Python 虚拟环境和依赖。

推荐命令：

```bash
cd backend
uv venv
uv add django djangorestframework django-cors-headers djangorestframework-simplejwt drf-spectacular django-filter Pillow mysqlclient
```

如果 `mysqlclient` 安装失败，可以提示用户安装系统依赖，或在开发期临时使用 `PyMySQL`。不要在未说明原因的情况下随意切换数据库驱动。

不要求使用 Miniconda。除非用户明确要求，否则不要引入 Conda 环境。

## 6. 后端设计规则

### 认证与账号

1. 用户注册必须包含真实姓名字段。
2. 用户必须经过审核后才能访问内部 API。
3. 用户状态至少应支持：待审核、审核通过、审核拒绝、需补充资料、已限制、已封禁。
4. 用户角色至少应支持：普通同学、管理会员、超级管理员。
5. 不得允许待审核、审核拒绝、已封禁用户访问动态、活动、相册、通讯录等内部资源。
6. 不得在普通用户接口中泄露审核备注、举报记录、后台日志等管理信息。

### 权限

权限判断必须放在后端，不能只依赖前端隐藏按钮。

必须区分：

- 未登录用户
- 待审核用户
- 普通同学
- 管理会员
- 超级管理员
- 被限制用户
- 被封禁用户

管理接口必须独立命名和授权，例如 `/api/v1/admin/...`。

### 隐私字段

以下信息默认不得向普通用户公开：

- 手机号
- 微信号
- 邮箱
- 审核材料
- 审核备注
- 举报记录
- 管理日志
- 封禁原因详情
- 登录 IP、设备信息等安全日志

公开任何联系方式前，必须检查用户的可见范围设置。

### 匿名展示

动态、评论、照片说明、生日祝福可以支持匿名展示，但实现时必须满足：

1. 数据库保存真实作者 `author_id`。
2. 前台根据 `display_mode` 决定展示真实姓名、昵称或匿名。
3. 管理员处理举报时可以看到真实作者。
4. API 返回字段必须根据当前用户角色过滤，不得把真实作者信息泄露给普通用户。

### 活动实名

活动相关记录必须使用真实姓名，包括：

- 活动发起人
- 报名人
- 接龙填写人
- 费用确认人
- 投票参与者，如果投票规则要求展示参与者

建议活动参与记录保存 `real_name_snapshot`，避免用户后续修改真实姓名导致历史活动记录混乱。

### 生日数据

生日字段只存储月份，例如 `birthday_month`，取值范围 1-12。

禁止设计和实现以下字段：

- `birth_year`
- `birth_day`
- `birthday`
- `full_birthday`
- 身份证号推导生日

生日祝福板块只展示本月生日同学，不展示年份和具体日期。

### 内容治理

以下对象必须支持举报和管理处理：

- 动态
- 评论和回复
- 照片或相册说明
- 活动说明
- 生日祝福留言

管理处理必须记录操作日志，包括操作者、操作对象、操作类型、操作时间、原因和必要的 metadata。

## 7. 数据模型规则

实现模型时优先遵循以下领域边界：

- `accounts`：用户、认证、角色、审核状态
- `profiles`：同学资料、通讯录、隐私设置
- `posts`：动态
- `comments`：评论和回复
- `activities`：活动、报名、投票、接龙
- `albums`：相册、照片
- `birthdays`：生日月份、生日祝福
- `announcements`：公告、置顶、已读
- `reports`：举报
- `moderation`：内容处理、限制、封禁
- `audit_logs`：操作日志
- `notifications`：系统通知，不得实现私信
- `common`：通用基类、权限、工具函数

模型设计应优先使用显式状态字段，不要用模糊布尔值堆叠复杂状态。

例如内容状态可以使用：

```text
draft / published / hidden / deleted / pending_review
```

用户状态可以使用：

```text
pending / approved / rejected / need_more_info / restricted / banned
```

所有重要模型应包含：

```text
created_at
updated_at
```

软删除对象应包含：

```text
deleted_at
deleted_by
delete_reason
```

## 8. API 设计规则

所有业务 API 默认使用版本化路径：

```text
/api/v1/...
```

推荐接口分组：

```text
/api/v1/auth/
/api/v1/me/
/api/v1/classmates/
/api/v1/profiles/
/api/v1/posts/
/api/v1/comments/
/api/v1/activities/
/api/v1/albums/
/api/v1/birthdays/
/api/v1/announcements/
/api/v1/reports/
/api/v1/admin/
```

API 返回必须遵守最小必要原则：

1. 普通用户只能看到其权限允许的信息。
2. 管理员接口和普通接口分离。
3. 不得为了前端方便一次性返回敏感字段。
4. 列表接口必须分页。
5. 搜索和筛选参数必须白名单化。
6. 错误码应稳定、可读，便于前端和未来移动端处理。

推荐统一错误码示例：

```text
ACCOUNT_PENDING_REVIEW
ACCOUNT_REJECTED
ACCOUNT_BANNED
PERMISSION_DENIED
CONTENT_REMOVED
VALIDATION_ERROR
RATE_LIMITED
```

## 9. 前端实现规则

前端实现必须遵循以下规则：

1. 所有页面都应考虑移动端显示。
2. 未登录用户只能访问登录、注册、必要说明页和隐私政策页。
3. 待审核用户只能看到审核状态和补充资料页面。
4. 普通用户不得看到管理后台入口。
5. 即使前端隐藏按钮，后端仍必须做权限校验。
6. 展示匿名内容时，不得暴露真实作者信息。
7. 活动报名和接龙页面必须明确展示真实姓名参与规则。
8. 生日设置只能选择月份，不能输入年份和具体日期。
9. 联系方式默认不公开，用户主动选择后才展示。
10. 不得实现站内私信、小群、群聊、临时讨论组。

涉及隐私或匿名展示的 UI 必须有清晰提示，例如：

```text
匿名仅对普通同学展示，管理员在处理举报和安全事件时仍可追溯真实账号。
```

## 10. Docker 与部署规则

开发期推荐：

```text
Django：本机虚拟环境运行
前端：本机 Node.js 运行
MySQL：Docker
Redis：Docker
```

上线期推荐：

```text
Nginx
Django + Gunicorn
MySQL
Redis
Celery，按需启用
Celery Beat，按需启用
```

Docker 配置必须区分开发和生产：

- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `.env.dev`
- `.env.prod`

禁止将 `.env.prod`、数据库密码、JWT 密钥、Django Secret Key、云服务密钥提交到仓库。

生产环境必须考虑：

1. HTTPS
2. `DEBUG=False`
3. `ALLOWED_HOSTS` 明确配置
4. CORS 白名单
5. CSRF/JWT 安全策略
6. 静态文件和媒体文件路径
7. 数据库备份
8. 媒体文件备份
9. 日志轮转
10. 管理后台访问控制

## 11. 数据库与迁移规则

1. 正式开发和上线前必须在 MySQL 上运行迁移和测试。
2. 不得在生产数据库上直接试验 migration。
3. 涉及字段删除、类型变更、唯一约束、索引调整时，必须说明迁移风险。
4. 涉及历史数据修复时，必须编写可重复执行或有保护条件的数据迁移脚本。
5. 不得假设 SQLite 行为等同于 MySQL 行为。
6. 外键删除策略必须明确，例如 `PROTECT`、`CASCADE`、`SET_NULL`，不得随意使用。

## 12. 图片和文件上传规则

图片和文件上传必须满足：

1. 限制文件大小。
2. 限制文件类型。
3. 不信任客户端传来的 MIME 类型。
4. 对图片进行安全校验和必要压缩。
5. 不把上传文件直接放到可执行目录。
6. 媒体文件访问必须考虑权限控制。
7. 不生成永久公开的敏感图片直链。
8. 支持后续迁移到对象存储。

第一版可以使用服务器本地 `media/`，但必须在部署方案中考虑备份。

## 13. 安全规则

必须避免以下问题：

- SQL 注入
- XSS
- CSRF
- 越权访问
- IDOR，直接对象引用漏洞
- 任意文件上传
- 敏感信息泄露
- 管理接口未授权访问
- 批量爬取通讯录或相册
- 过度返回用户隐私字段

所有通过 ID 访问的资源，都必须检查当前用户是否有权访问该对象。

不要在日志中记录：

- 明文密码
- JWT token
- 手机号完整值
- 微信号完整值
- 邮箱完整值
- 敏感审核材料

必要时进行脱敏。

## 14. 测试和验证规则

Agent 完成任何代码修改后，必须尽可能运行相应验证命令，并在回复中报告真实结果。

后端常用验证：

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

如果使用 pytest：

```bash
pytest
```

前端常用验证：

```bash
npm run typecheck
npm run lint
npm run build
```

或使用 pnpm：

```bash
pnpm typecheck
pnpm lint
pnpm build
```

部署配置验证：

```bash
docker compose -f deploy/docker-compose.dev.yml config
docker compose -f deploy/docker-compose.prod.yml config
```

如果验证失败，必须说明失败原因和下一步建议。禁止伪造测试通过结果。

## 15. 开发流程规则

处理任务时优先遵循以下流程：

1. 阅读相关文档和现有代码。
2. 明确要实现的白皮书条款或业务规则。
3. 设计模型、权限、API 和前端交互。
4. 小步修改，不做无关重构。
5. 增加必要测试。
6. 运行验证命令。
7. 总结改动、验证结果和风险。

除非用户明确要求，不要一次性实现过多模块。

优先按以下顺序推进第一版：

1. 项目基础设施。
2. 账号注册、登录、身份审核。
3. 权限与角色。
4. 个人资料和通讯录。
5. 首页动态和评论。
6. 活动模块。
7. 公告、相册、生日祝福。
8. 举报、管理后台、操作日志。
9. 部署和备份。

## 16. 禁止实现的功能

除非用户明确推翻白皮书原则，否则不得实现：

- 站内私信
- 小群
- 群聊
- 临时讨论组
- 点对点聊天
- 完全不可追溯的匿名发布
- 面向公众的开放浏览
- 陌生人社交
- 同城扩列
- 好友匹配
- 直播
- 短视频流
- 推荐算法驱动的信息流
- 复杂交易和支付担保

如果用户提出相关需求，Agent 应提醒这些需求与当前白皮书原则冲突，并请用户确认是否修改产品总纲。

## 17. 文档规则

1. 重要架构决策应写入 `docs/`。
2. API 变更应同步 OpenAPI 文档。
3. 部署步骤应写入 `docs/deployment.md` 或对应部署文档。
4. 不要擅自修改白皮书。
5. 如果必须生成面向用户的正式文档，应使用自然、清晰、少 AI 味的中文。

## 18. Agent 回复规则

Agent 在完成任务时，应向用户说明：

1. 修改了哪些文件。
2. 实现了哪些功能。
3. 运行了哪些验证命令。
4. 验证结果是什么。
5. 是否存在风险或未完成项。

不要只描述计划而不执行。不要编造命令输出。不要把未验证的内容说成已验证。

## 19. 当前项目阶段默认假设

除非用户另有说明，默认当前阶段是第一版开发前期，重点是：

- 搭建 Python + Django + DRF + MySQL 后端基础
- 搭建 Vue 3 前端基础
- 建立 Docker Compose 开发环境
- 明确账号审核、权限、隐私、活动实名和生日月份规则
- 为未来移动端 App 保留 REST API 能力

Agent 应优先保证项目能稳定、清晰、可持续地推进，而不是追求复杂架构或过度工程化。
