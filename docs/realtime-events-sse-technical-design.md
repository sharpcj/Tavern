文章标题：实时事件推送（SSE）技术方案

# 一、背景

当前 Tavern 已经完成动态、评论、活动、公告、相册、生日祝福、举报、管理后台、操作日志和系统通知等核心模块。现有前端主要依赖页面进入时主动拉取 REST API，其他同学发布动态、上传照片、评论或回复后，当前用户页面不会主动刷新，需要手动刷新页面才能看到最新内容。

这个问题会影响社区的互动体验，尤其是手机端浏览动态详情、照片详情或通知中心时，用户会误以为没有新内容。

本方案在不引入私信、小群、聊天能力的前提下，增加“服务端到客户端”的单向实时事件流。服务端只告诉客户端“某类内容发生了变化”，客户端再按当前页面调用已有 REST API 重新拉取数据。这样既能改善实时体验，也不会突破白皮书中“不做私信和小群”的产品边界。

# 二、需求范围

## 本阶段实现

| 能力 | 说明 |
| --- | --- |
| SSE 实时事件流 | 提供登录后可访问的事件流接口，向当前用户推送站内变化事件 |
| 事件补拉接口 | 提供按 cursor 拉取最近事件的接口，用于手机端切回前台、断线重连后的补偿刷新 |
| 事件发布服务 | 后端业务动作完成后统一发布事件，避免各模块直接拼接推送细节 |
| 前端实时事件客户端 | 登录后建立 SSE 连接，断线自动重连，页面切回前台后补拉 |
| 当前页面自动刷新 | 动态列表、动态详情、相册详情、照片详情、通知中心等页面收到相关事件后刷新数据 |
| 通知未读数刷新 | 系统通知产生、已读状态变化后刷新导航中的未读数量 |
| 手机端前台实时 | 手机浏览器前台打开页面时实时刷新，切后台后通过补拉恢复最新状态 |

## 本阶段不做

| 不做项 | 原因 |
| --- | --- |
| WebSocket 双向通信 | 当前需求是服务端单向通知客户端刷新，SSE 已足够 |
| 站内私信、聊天、群组 | 与白皮书“不提供私信和小群原则”冲突 |
| 锁屏后台系统通知 | 需要 Web Push、APNs、FCM 或厂商推送，属于后续独立能力 |
| 精确多人在线状态 | 容易引出聊天/在线社交语义，第一版不需要 |
| 客户端直接信任事件 payload | 事件只作为刷新信号，详情仍通过已有 REST API 和权限校验获取 |
| 向未审核、封禁用户推送内部事件 | 实时接口沿用已审核用户权限，不向无权用户开放 |

# 三、总体架构

本方案采用“事件存储 + SSE 流 + 补拉”的结构。

```text
业务动作完成
  ↓
实时事件服务 publish_event()
  ↓
RealtimeEvent 数据表记录事件
  ↓
SSE 长连接向在线用户推送事件
  ↓
前端根据事件类型刷新当前页面或未读数

手机切后台 / 网络断开 / SSE 重连
  ↓
前端携带 last_event_id 调用 since 接口
  ↓
补拉断线期间发生的事件
  ↓
刷新当前页面
```

本地开发和第一版部署阶段，可以先使用数据库作为事件补拉来源，并用轻量轮询方式驱动 SSE 连接读取新事件。项目已经预留 Redis，后续如果并发或多 worker 部署需要更低延迟，再把事件广播层替换为 Redis Pub/Sub 或 Channels layer。业务侧只调用 `publish_event()`，不感知底层实现变化。

# 四、数据模型

新增 `RealtimeEvent` 模型，建议放在 `apps/notifications` 中，因为它服务于系统通知和站内体验提醒，但不等同于用户可读通知。

| 字段 | 说明 |
| --- | --- |
| `id` | 自增主键，同时作为 SSE `id` 和补拉 cursor |
| `recipient` | 可选接收人；为空表示广播给所有已审核用户 |
| `event_type` | 事件类型，例如动态创建、评论创建、通知变化 |
| `target_type` | 目标对象类型，例如 `post`、`comment`、`album`、`photo`、`notification` |
| `target_id` | 目标对象 ID，字符串保存，兼容不同主键类型 |
| `payload` | 最小必要 JSON，不放敏感信息 |
| `created_at` | 事件创建时间 |

索引建议：

- `(recipient, id)`：查询某个用户的个人事件。
- `(id)`：按 cursor 补拉。
- `(event_type, created_at)`：后续排查和调试。

事件保留策略：

- 第一版不做清理任务，数据量可控。
- 后续可增加定期清理，例如只保留最近 7-30 天事件。
- 事件不是审计日志，不承担治理追溯职责；治理追溯仍以 `audit_logs` 为准。

# 五、后端 API

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/v1/events/stream/` | 已审核用户 | SSE 实时事件流 |
| GET | `/api/v1/events/since/?cursor=123` | 已审核用户 | 补拉 cursor 之后的事件 |

## SSE 事件格式

```text
id: 124
event: post.created
data: {"id":124,"type":"post.created","target_type":"post","target_id":"1","payload":{},"created_at":"2026-06-14T10:00:00+08:00"}

```

## 补拉响应格式

```json
{
  "results": [
    {
      "id": 124,
      "type": "post.created",
      "target_type": "post",
      "target_id": "1",
      "payload": {},
      "created_at": "2026-06-14T10:00:00+08:00"
    }
  ],
  "latest_cursor": 124
}
```

## 权限原则

- SSE 和补拉接口必须使用 `IsApprovedClassmate`。
- 用户只能看到：
  - `recipient` 为自己的事件。
  - `recipient` 为空的全站广播事件。
- 封禁、未审核、拒绝用户不能访问实时接口。
- 事件 payload 不放真实作者敏感字段、审核备注、举报记录、管理日志等敏感信息。

# 六、事件类型与接入点

| 事件类型 | 目标 | 接入点 | 前端处理 |
| --- | --- | --- | --- |
| `post.created` | 动态 | 动态发布成功后 | 动态列表提示或刷新 |
| `post.updated` | 动态 | 动态隐藏、删除、置顶状态变化后 | 动态列表/详情刷新 |
| `comment.created` | 动态评论 | 动态评论或回复创建成功后 | 动态详情评论区刷新，动态列表评论数刷新 |
| `album.photo.created` | 相册照片 | 照片上传成功后 | 相册详情照片列表刷新 |
| `photo.comment.created` | 照片评论 | 照片评论或回复创建成功后 | 照片详情评论区刷新 |
| `announcement.created` | 公告 | 公告发布成功后 | 公告列表/顶部公告刷新 |
| `activity.updated` | 活动 | 活动状态、报名、投票、接龙变化后 | 活动列表/详情刷新 |
| `notification.created` | 系统通知 | 通知创建成功后 | 未读数和通知中心刷新 |
| `notification.read` | 系统通知 | 标记已读后 | 未读数刷新 |

本阶段优先接入用户反馈最明显的事件：

1. 动态发布。
2. 动态评论/回复。
3. 相册照片上传。
4. 照片评论/回复。
5. 系统通知创建和已读。

公告、活动、管理端内容状态变化可以在基础设施稳定后继续补齐。

# 七、前端方案

## 实时事件客户端

新增前端模块，例如：

```text
frontend/src/api/events.ts
frontend/src/composables/useRealtimeEvents.ts
```

主要职责：

- 登录且用户已审核后建立 SSE 连接。
- 记录 `lastEventId`。
- 收到事件后分发给页面或全局 store。
- 连接断开时自动重连。
- `document.visibilitychange` 从后台回到前台时调用 `since` 接口补拉事件。
- 如果 SSE 连接持续失败，降级为低频补拉。

## 页面刷新策略

| 页面 | 收到事件后的处理 |
| --- | --- |
| 动态列表页 | `post.created` / `post.updated` / `comment.created` 后刷新当前页或提示有新内容 |
| 动态详情页 | 当前动态相关的 `comment.created` / `post.updated` 后刷新详情和评论 |
| 相册详情页 | 当前相册相关的 `album.photo.created` 后刷新照片列表 |
| 照片详情页 | 当前照片相关的 `photo.comment.created` 后刷新评论 |
| 通知中心 | `notification.created` / `notification.read` 后刷新列表 |
| 顶部导航 | `notification.created` / `notification.read` 后刷新未读数 |

为了避免用户正在输入评论时被打断，评论区可以优先刷新列表数据，不清空当前输入框；动态列表可以优先显示“有新内容，点击刷新”，后续再按体验需要改为自动刷新。

# 八、移动端策略

手机端可以做到“前台实时刷新”，但不承诺锁屏后台持续实时。

| 场景 | 策略 |
| --- | --- |
| 手机浏览器前台打开页面 | SSE 正常接收事件，页面实时刷新 |
| 用户切到其他 App | 浏览器可能暂停 JS 或断开连接，不依赖后台 SSE |
| 用户切回页面 | `visibilitychange` 触发补拉，刷新当前页面 |
| 网络短暂断开 | EventSource 自动重连，重连后用 cursor 补拉缺失事件 |
| 锁屏后系统通知 | 本方案不做，需要后续 Web Push / 原生推送 |

这套设计也兼容未来原生移动端：App 前台可以复用 `/events/stream/`，App 回到前台可以复用 `/events/since/`，后台提醒则后续接入系统推送。

# 九、部署与运行要求

## 开发环境

本地调试 SSE 时，后端必须使用 ASGI Server 启动，不建议继续使用 Django 默认 `runserver` 调试长连接。推荐命令：

```bash
cd /home/sharpcj/PycharmProjects/Tavern
uv run uvicorn tavern.asgi:application --host 0.0.0.0 --port 8000 --reload
```

前端开启 SSE 调试：

```bash
cd /home/sharpcj/PycharmProjects/Tavern/frontend
npm run dev:sse
```

如果临时使用 Django `runserver`，前端不要开启 `VITE_ENABLE_SSE_STREAM`，使用默认 `npm run dev` 即可；此时前端会自动降级为 3 秒一次的 `/events/since/` 补拉，避免长连接占住本地调试服务器导致提交请求卡住。

手机局域网访问时，后端需要监听 `0.0.0.0:8000`，前端 API 地址不能写死为手机自己的 `localhost`，应使用当前 hostname 拼接后端端口。

## 生产环境

建议生产运行方式切到 ASGI，例如 Uvicorn 或 Daphne。

Nginx 代理 SSE 时需要注意：

```nginx
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

SSE 响应头建议：

```text
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
```

# 十、边界与风险

| 风险 | 处理 |
| --- | --- |
| 与私信边界混淆 | 不提供用户发事件 API，不提供回复、会话、点对点聊天 |
| 事件泄露敏感信息 | payload 只放刷新所需的最小字段，详情走 REST API 权限过滤 |
| 手机后台不稳定 | 明确只保证前台实时，切回前台补拉 |
| 多标签页重复连接 | 第一版可接受；后续可用 BroadcastChannel 合并事件分发 |
| 数据库事件表增长 | 第一版班级规模小可接受，后续加定期清理 |
| SSE 长连接占用 worker | 生产建议 ASGI；若并发增加，再引入 Redis Pub/Sub 优化广播 |
| 接口鉴权问题 | 实时接口沿用 JWT/Session 认证和 `IsApprovedClassmate` 权限 |

# 十一、验收标准

- 已审核用户可以建立 SSE 连接。
- 未登录、待审核、审核拒绝、封禁用户不能访问实时接口。
- 发布动态后，其他在线用户能收到 `post.created` 事件。
- 评论或回复动态后，正在查看该动态详情的用户评论区能刷新。
- 上传相册照片后，正在查看相册详情的用户照片列表能刷新。
- 评论或回复照片后，正在查看照片详情的用户评论区能刷新。
- 系统通知创建或标记已读后，通知未读数能刷新。
- 手机端页面切后台再切回前台后，会补拉缺失事件并刷新当前页面。
- 后端 `check`、迁移检查、测试、OpenAPI 校验通过。
- 前端 `typecheck` 和 `build` 通过。
