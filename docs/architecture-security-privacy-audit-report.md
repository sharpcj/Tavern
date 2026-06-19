文章标题：Tavern 项目架构、安全与隐私合规审计报告

本报告基于对 Tavern 项目代码库的全面阅读和分析，从架构设计、前后端安全、隐私合规三个维度进行审计，梳理做得好的地方和存在的问题，并按风险等级给出改进建议。

# 一、审计范围与方法

审计范围覆盖项目全部后端代码（Django + DRF）和前端核心代码（Vue 3 + TypeScript），具体包括：

- 项目结构与 settings 配置（base / development / production）
- 自定义 User 模型与认证体系
- DRF 权限类、限流、分页、异常处理
- 全部 13 个 App 的 models、serializers、views
- 前端路由守卫、API 客户端、认证状态管理
- 部署配置（Docker Compose、Nginx、环境变量）
- 文件上传、媒体访问控制、日志审计

审计方法为代码静态分析，结合 Django 官方最佳实践和 OWASP 常见 Web 安全风险进行对照检查。

# 二、架构设计

## 做得好的地方

**项目结构清晰，符合 Django 惯例。** 项目根 `tavern/` 作为 Django project，`apps/` 下按领域拆分为 13 个 App，settings 按环境拆分为 base / development / production 三个文件，这是成熟 Django 项目的标准布局。

**自定义 User 模型实现正确。** 继承 `AbstractBaseUser` + `PermissionsMixin`，以 email 作为 `USERNAME_FIELD`，使用 `set_password()` 哈希存储密码，`UserManager` 正确实现了 `create_user` 和 `create_superuser`。在项目首次 migration 之前就完成了自定义 User 模型，避免了 Django 文档指出的后期迁移困难。

**App 模块化合理，边界清晰。** accounts / profiles / posts / comments / activities / albums / birthdays / announcements / reports / moderation / audit_logs / notifications / common 各司其职，与项目白皮书和模块规划文档的领域划分一致，没有出现跨 App 的循环依赖。

**DRF 配置完善且规范。** 全局默认认证类为 JWT + Session，默认权限类为 `IsAuthenticated`，默认分页类统一为 `StandardResultsSetPagination`（page_size=20，max=100），默认过滤后端为 `DjangoFilterBackend`。各 View 按需覆盖权限，符合 DRF 的"全局收紧、局部放宽"最佳实践。

**中间件顺序正确。** SecurityMiddleware → CorsMiddleware → SessionMiddleware → CommonMiddleware → CsrfViewMiddleware → AuthenticationMiddleware → MessageMiddleware → XFrameOptionsMiddleware，完全符合 Django 安全文档推荐的顺序，CORS 在 CSRF 之前，认证在 CSRF 之后。

**软删除设计良好。** `SoftDeletableModel` 抽象 Mixin 包含 `deleted_at`、`deleted_by`、`delete_reason` 三个字段，`soft_delete()` 方法自动联动 `ContentStatus.DELETED` 状态变更，符合 AGENTS.md 对软删除的要求。Post、Comment 等核心内容模型均继承此 Mixin。

**枚举使用规范。** 全部使用 `models.TextChoices` 定义状态和类型枚举，包括 ContentStatus（draft/published/hidden/deleted/pending_review）、DisplayMode（real_name/nickname）、UserRole、ReviewStatus、AccountStatus、ActivityType、ActivityStatus 等，避免了魔法字符串。

**GenericForeignKey 使用恰当。** Media（媒体文件元数据）、Report（举报）、AuditLog（操作日志）三个需要关联多种内容类型的模型正确使用了 GFK，没有滥用。

**UUID 作为外部标识。** `account_id` 使用 UUID 而非自增 ID 暴露给 API，有效防止了 ID 枚举攻击（IDOR）。

**JWT 配置合理。** access token 30 分钟，refresh token 7 天，开启 `ROTATE_REFRESH_TOKENS`（每次刷新发放新 token），认证头类型为 Bearer。

## 存在的问题

**admin_views.py 中存在动态导入反模式。** 文件 `apps/accounts/admin_views.py` 第 119 行使用了 `__import__("django").utils.timezone.now()`，而不是在文件顶部 `from django.utils import timezone`。这是代码质量问题，不影响运行但违反 Python 编码规范，降低了可读性。风险等级：低。

**manage.py 和 asgi.py 硬编码 development settings。** 两个文件都默认设置 `DJANGO_SETTINGS_MODULE` 为 `tavern.settings.development`。生产部署时通过 `.env.prod` 中的环境变量覆盖，实际运行不受影响。但如果在服务器上直接执行 `python manage.py` 而未设置环境变量，会意外加载开发配置。建议在 manage.py 中移除硬编码默认值，或改为读取环境变量。风险等级：低。

**Redis 配置了但未实际使用。** `REDIS_URL` 已在 base settings 中定义，但没有配置 Django `CACHES` 或 Celery。当前阶段可以接受（AGENTS.md 明确说 Celery 第一版可预留），但属于未完成项。风险等级：低。

**开发环境 `CORS_ALLOW_ALL_ORIGINS = True`。** 仅影响开发环境，生产配置中已正确限制。需确保不会误带入生产。风险等级：低。

# 三、前后端安全性

## 做得好的地方

**权限体系完整且层次分明。** 四层自定义权限类覆盖了全部角色场景：

- `IsApprovedClassmate`：审核通过且账号正常的用户
- `IsApprovedClassmateOrReadOnly`：被限制用户可读不可写
- `IsModeratorOrAbove`：管理会员及以上
- `IsSuperAdmin`：仅超级管理员

每层都检查认证状态、审核状态、账号状态和角色，拒绝时返回结构化错误码（ACCOUNT_PENDING_REVIEW、ACCOUNT_REJECTED、ACCOUNT_BANNED、ACCOUNT_RESTRICTED、PERMISSION_DENIED），前端可根据错误码做差异化提示。

**限流覆盖全面。** 8 个限流 scope 覆盖了关键端点：anon（匿名 60/min）、user（已认证 600/min）、auth（登录 10/min）、register（注册 5/hour）、upload（上传 30/hour）、comment（评论 120/hour）、report（举报 30/hour）、sse（实时推送 20/min）。注册和登录的低频率限制有效防止了暴力破解和批量注册。

**前端路由守卫完善。** `router.beforeEach` 检查了五种路由元数据（requiresAuth、requiresApproved、allowRestricted、requiresModerator、guestOnly），且正确区分了被封禁、待审核、被限制等不同状态的处理逻辑。已登录用户访问登录/注册页会自动重定向，被封禁用户只能看到审核状态页。

**生产环境 Django 安全配置到位。** `tavern/settings/production.py` 中启用了：

- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True` / `CSRF_COOKIE_SECURE = True`
- `SESSION_COOKIE_HTTPONLY = True` / `CSRF_COOKIE_HTTPONLY = True`
- HSTS 完整配置（max-age=31536000，includeSubDomains，preload）
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = "DENY"`

**Nginx 安全头齐全。** 生产 Nginx 配置中设置了：

- Content-Security-Policy（限制 script-src、frame-ancestors、base-uri、form-action）
- Strict-Transport-Security（与 Django 侧一致）
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
- TLS 1.2/1.3，禁用不安全加密套件

**媒体文件访问控制设计良好。** 上传的媒体文件不直接通过 `/media/` 路径暴露。Nginx 对 `/media/` 直接返回 404，所有媒体访问必须通过 `/api/v1/media/<id>/file/?token=...` 签名 URL。token 使用 Django signing 模块生成，有效期 1 小时，salt 独立。这确保了媒体文件访问必须经过后端权限检查。

**无 SQL 注入风险。** 全项目搜索未发现 `raw()`、`RawSQL`、`extra()` 等原始 SQL 用法，所有数据库查询均通过 Django ORM 完成。查询参数通过 ORM 的 filter 和 Q 对象传递，Django 自动进行参数化转义。

**文件上传安全校验多层。** 上传文件经过三层校验：MIME 类型白名单（仅允许 jpeg/png/gif/webp）、文件大小限制（通用 10MB，头像 512KB）、PIL 图片完整性校验（`Image.open().verify()`）。头像额外限制宽高不超过 1024px。

**Nginx 层限流补充。** 登录端点 `limit_req zone=auth_per_ip burst=5 nodelay`，SSE 连接 `limit_conn sse_per_ip 3`，通用 API `limit_req zone=api_per_ip burst=30 nodelay`。Nginx 限流在请求到达 Django 之前生效，降低了应用层压力。

**敏感配置文件已加入 .gitignore。** `.env*` 被 gitignore 规则排除（仅保留 `.env.example` 模板），数据库密码、JWT 密钥、Django Secret Key 不会提交到仓库。

## 存在的问题

**JWT Token 存储在 localStorage。** 文件：`frontend/src/stores/auth.ts` 第 10-11 行。access token 和 refresh token 都存储在 `localStorage` 中。如果发生 XSS 攻击，攻击者可以直接读取 token 并冒充用户。缓解因素：CSP 头已配置 `script-src 'self'`，限制了内联脚本和外部脚本加载，降低了 XSS 风险。但 localStorage 本质上是 JavaScript 可读的，不如 httpOnly cookie 安全。风险等级：中。

建议：考虑将 token 存储在 httpOnly cookie 中，或至少缩短 access token 有效期（当前 30 分钟已较短，可接受）。如果保持 localStorage 方案，需确保 CSP 头严格生效，并定期进行 XSS 审计。

**未启用 Token 黑名单。** 文件：`tavern/settings/base.py` 第 150 行，`BLACKLIST_AFTER_ROTATION = False`。refresh token 有效期 7 天，在此期间如果 token 被盗，攻击者可以持续刷新获取新的 access token。启用 blacklist 后，旧 refresh token 在刷新后立即失效，可以限制泄露窗口。风险等级：中。

建议：启用 `BLACKLIST_AFTER_ROTATION = True`，需要配置 `rest_framework_simplejwt.token_blacklist` app 并运行 migration。

**前端 axios 拦截器未做全局 401 自动刷新。** 文件：`frontend/src/api/client.ts`。API 调用返回 401 时不会自动尝试 refresh token，只在 `loadCurrentUser` 失败时才刷新。这意味着用户在浏览过程中 token 过期后，需要手动刷新页面才能恢复。风险等级：低。

建议：在 axios 响应拦截器中添加 401 处理逻辑，自动使用 refresh token 刷新后重试原请求。

**无邮件验证机制。** 注册时不需要验证邮箱所有权，可以用他人邮箱注册。在当前阶段（内部社区、管理员人工审核身份）可以接受，因为审核流程本身会核实身份。但长期来看，加入邮箱验证可以防止恶意注册和误操作。风险等级：中。

**无密码重置流程。** 当前没有 forgot-password / reset-password 功能。用户忘记密码后只能联系管理员处理。对于内部社区，短期内可接受，但会影响用户体验。风险等级：中。

# 四、隐私合规

## 做得好的地方

**密码从不明文存储。** 所有密码通过 Django 的 `set_password()` 方法处理，默认使用 PBKDF2 + SHA256 迭代哈希。所有 Serializer 中 password 字段均标记为 `write_only=True`，API 响应中绝不包含密码。注册时强制验证两次密码一致性，并启用 Django 全部四个密码强度验证器。

**联系方式三级可见性控制。** 手机号、微信号、邮箱三个联系方式各自独立设置可见范围：everyone（所有人可见）、selected（指定同学可见）、only_me（仅自己可见）。默认值均为 `only_me`，遵循"默认不公开"的保守隐私策略。

**Profile.can_view_contact() 方法实现正确。** 可见性判断逻辑完善：自己始终可见；everyone 模式对所有人可见；selected 模式检查 `contact_visible_to` M2M 关系；only_me 模式仅自己可见。`contact_visible_to` 的写入也做了校验，只能选择审核通过且账号正常的同学。

**Serializer 按角色严格过滤字段。** 三个层级的 Serializer 实现了字段级权限控制：

- `ClassmateListSerializer`：仅包含 account_id、real_name、nickname、avatar_url、city、occupation、bio、birthday_month，不包含任何联系方式。
- `ClassmateDetailSerializer`：联系方式通过 `SerializerMethodField` + `can_view_contact()` 动态返回，无权限时返回 null。
- `CurrentUserSerializer`：用户查看自己的信息，包含 email 但不包含 `review_note`、`reviewed_by` 等管理字段。
- `AdminUserListSerializer`：包含管理字段，但仅 IsSuperAdmin 权限可访问对应 View。

**生日数据最小化。** 仅存储 `birthday_month`（1-12），不存储出生年份和具体日期。`show_birthday` 布尔开关控制是否在生日板块展示。Serializer 中 `validate_birthday_month` 限制了取值范围。完全符合白皮书"生日最小展示"原则。

**活动实名快照机制。** Signup（报名）、VoteRecord（投票）、ChainRecord（接龙）都保存 `real_name_snapshot`，Activity 保存 `initiator_name_snapshot`。用户后续修改真实姓名不会导致历史活动记录出现不一致。符合白皮书"活动实名"要求。

**审核材料与用户提示分离。** `review_note`（内部审核备注）和 `review_message`（给用户的审核说明）分开存储。前者仅管理员可见，后者会展示给用户。审核操作记录审核人和审核时间。

**操作日志完整可追溯。** AuditLog 模型记录操作者（actor）、操作类型（action，15 种枚举值）、目标对象（GenericFK）、原因（reason）、扩展信息（metadata JSON）和操作时间。覆盖了审核、角色变更、状态变更、内容处理、公告管理、活动管理等所有管理操作。`write_audit_log()` 辅助函数统一了日志写入方式。

**未实现私信和群聊。** 系统通知（Notification）是单向的，类型限定为审核结果、公告通知、评论回复、活动状态、系统通知五种。没有私信、小群、群聊、临时讨论组等双向通信功能。完全符合白皮书"不做私信和小群"原则。

**媒体文件不直接暴露。** 签名 URL 机制确保只有通过权限检查的用户才能访问媒体文件。Nginx 层对 `/media/` 直接返回 404，无法绕过应用层权限。

**头像可见性控制。** `ProfileAvatarUrlMixin.to_representation()` 检查 `avatar_visible` 字段，不可见时返回空字符串。用户可以选择不公开展示头像。

## 存在的问题

**CurrentUserSerializer 暴露了 email 字段。** 文件：`apps/accounts/serializers.py` 第 74 行。用户查看自己的信息时可以看到自己的邮箱，这是正常行为。但需确保前端不会将 email 展示给其他用户——当前前端代码中，`ClassmateDetailPage` 使用的是 `ClassmateDetailSerializer`，其 email 通过 `can_view_contact()` 过滤，所以没有问题。风险等级：低。

**日志脱敏未显式配置。** AGENTS.md 要求不在日志中记录明文密码、JWT token、手机号、微信号、邮箱。当前代码中未见违反（密码通过 `write_only` 不进入日志，ORM 查询不产生敏感 SQL），但没有显式的 Django logging 配置和敏感信息过滤器。建议在 production settings 中配置 logging，添加脱敏 filter。风险等级：低。

**举报记录中 reporter 身份对管理员可见。** Report 模型保存了 reporter 外键，管理员可以看到举报人身份。这在治理场景下是必要的（管理员需要评估举报真实性、防止恶意举报），但需确保普通用户无法通过任何接口获取他人的举报记录。当前代码中举报相关 View 均使用 `IsApprovedClassmate` 或管理员权限，普通用户只能查看自己的举报。风险等级：低。

# 五、问题汇总与改进建议

## P1（建议近期修复）

| 编号 | 问题 | 文件位置 | 建议 |
|------|------|----------|------|
| P1-1 | JWT Token 存储在 localStorage | `frontend/src/stores/auth.ts:10-11` | 评估迁移到 httpOnly cookie 或保持现状并确保 CSP 严格生效 |
| P1-2 | 未启用 Token 黑名单 | `tavern/settings/base.py:150` | 启用 `BLACKLIST_AFTER_ROTATION = True`，配置 `token_blacklist` app |
| P1-3 | 无邮件验证 | 全局 | 在注册流程中加入邮箱验证链接 |
| P1-4 | 无密码重置 | 全局 | 实现 forgot-password / reset-password 流程 |

## P2（建议后续迭代改进）

| 编号 | 问题 | 文件位置 | 建议 |
|------|------|----------|------|
| P2-1 | admin_views.py 动态导入反模式 | `apps/accounts/admin_views.py:119` | 改为顶部 `from django.utils import timezone` |
| P2-2 | manage.py 硬编码 development settings | `manage.py:9` | 移除默认值或改为读取 `DJANGO_SETTINGS_MODULE` 环境变量 |
| P2-3 | 前端 axios 未全局处理 401 | `frontend/src/api/client.ts` | 在响应拦截器中添加自动 refresh token 逻辑 |
| P2-4 | 日志脱敏未显式配置 | `tavern/settings/production.py` | 配置 Django logging，添加敏感信息 filter |
| P2-5 | Redis 已配置但未使用 | `tavern/settings/base.py:172` | 按需配置 CACHES 和 Celery |

# 六、总体评价

Tavern 项目在架构设计、安全防护和隐私合规三个维度均表现良好，没有发现严重（P0）级别的安全漏洞或架构缺陷。

架构方面，项目遵循了 Django 和 DRF 的最佳实践，代码组织清晰，App 边界合理，配置分层规范。安全方面，权限体系完整、限流覆盖全面、生产环境安全配置到位、媒体文件访问控制设计良好。隐私方面，密码哈希存储、联系方式三级可见性、字段级权限过滤、生日数据最小化、活动实名快照等设计均符合白皮书要求。

当前发现的问题主要集中在 JWT 存储方式、Token 黑名单、邮件验证等中低风险改进项，适合在后续迭代中按优先级逐步完善。整体来看，项目具备良好的工程基础，可以支撑后续模块的持续开发。
