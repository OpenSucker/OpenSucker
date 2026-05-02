# Agent Network 接入说明

OpenSucker 把「投资大师 Skill 蒸馏」能力通过 **P2P Service Gateway（`anet svc`）** 暴露到 Agent Network 上。别的 Agent 可以按 `skill-distillation` 标签发现我们，并通过标准 HTTP 调用 `/api/v1/skills/distill`。

本文档随代码演进持续维护，遇到问题先按《排查》一节逐项对。

---

## 一、架构与工作方式

```
  peer Agent ──┐       ┌──── local anet daemon (publisher) ────┐
               │ svc   │                                        │
               │ call  │          ANS + P2P mesh (libp2p)       │
               │       │                                        │
               └──────▶│  daemon B (OpenSucker 所在节点)        │
                       │    ↓ reverse-proxy via registered svc  │
                       │  FastAPI  :8000                        │
                       │   /api/v1/skills/distill               │
                       │   /api/v1/skills/jobs/{id}             │
                       │   /api/v1/skills/jobs/{id}/skill       │
                       └────────────────────────────────────────┘
```

- OpenSucker 侧跑两个进程：`uvicorn app.main:app`（FastAPI）+ `anet daemon`（ANet 守护进程）。
- FastAPI 启动时调用 `SvcClient.register()`，把自身的 `/api/v1/skills`、`/api/v1/health` 注册为一个 ANet P2P 服务。
- 其它节点上的 Agent：`svc.discover(skill="skill-distillation")` → `svc.call(peer_id, "opensucker-skill-distill", "/api/v1/skills/distill", body={"name":"彼得·林奇"})`。
- daemon 作为反向代理，把请求透传到本地 FastAPI，再把 HTTP 响应转回调用方。
- 业务侧**完全复用现有 FastAPI 路由**，不新增专门的 ANet endpoint。

---

## 二、涉及的代码文件

| 文件 | 作用 |
|---|---|
| [`backend/app/core/agentnet.py`](../app/core/agentnet.py) | 对 `anet-sdk` (`SvcClient`) 的薄封装 `AnetClient`。负责 register / unregister / list / discover，连接失败时抛 `AnetUnavailable`。 |
| [`backend/app/services/anet_register.py`](../app/services/anet_register.py) | 调用 `AnetClient` 完成启动注册、关机注销、probe 快照。失败只记 warning，不抛。 |
| [`backend/app/api/v1/endpoints/anet.py`](../app/api/v1/endpoints/anet.py) | 挂 `/api/v1/anet/{status,register,unregister,discover}` 四个管理端点。 |
| [`backend/app/core/events.py`](../app/core/events.py) | FastAPI `startup` / `shutdown` 钩子，根据 `ANET_ENABLED` 决定是否自动 (de)register。 |
| [`backend/app/core/config.py`](../app/core/config.py) | 读取 `ANET_*` 环境变量。 |
| [`backend/scripts/anet_register.py`](../scripts/anet_register.py) | 独立 CLI：register / unregister / status / discover。可脱离 FastAPI 运行。 |
| [`backend/tests/test_services/test_agentnet.py`](../tests/test_services/test_agentnet.py) | 用 Fake `SvcClient` 隔离 daemon，覆盖注册、注销、force 模式、auth 缺失、discover 等路径。 |
| [`backend/.env.example`](../.env.example) | 所有 `ANET_*` 配置的默认值与说明。 |

依赖：`anet-sdk>=1.1.0`（已写入 `requirements.txt`）。

---

## 三、环境变量

全部定义在 [`backend/.env`](../.env.example) 或同级 `.env`。

| 变量 | 默认 | 说明 |
|---|---|---|
| `ANET_ENABLED` | `false` | 总开关。为 `true` 时，FastAPI 启动自动 register，关机自动 unregister。 |
| `ANET_DAEMON_URL` | `http://127.0.0.1:3998` | 本地 daemon REST 地址。 |
| `ANET_API_TOKEN` | 空 | Bearer token。留空则 SDK 自动读取 `~/.anet/api_token`（daemon 首次启动会生成）。 |
| `ANET_SERVICE_NAME` | `opensucker-skill-distill` | 注册到 daemon 的 service 名；同一 daemon 上唯一。 |
| `ANET_SERVICE_ENDPOINT` | `http://127.0.0.1:8000` | daemon 反向代理到我们 FastAPI 的 URL。docker 场景需要改为 `host.docker.internal:8000` 之类。 |
| `ANET_SERVICE_TAGS` | `skill-distillation,investor-perspective,mental-model` | 逗号分隔，用于被 peer 的 `svc.discover(skill=...)` 命中。 |
| `ANET_SERVICE_DESCRIPTION` | *自动中文描述* | 展示在 discovery 结果里。 |

**安全提示**：`ANET_API_TOKEN` 属于 daemon 本地凭据，不要写入 git。生产环境建议留空依赖 `~/.anet/api_token` 并收敛文件权限到 0600。

---

## 四、上手步骤

### 1. 装 daemon 与 SDK

```powershell
# Python SDK（已写入 requirements.txt）
pip install anet-sdk

# CLI / daemon 二进制按官方指南：
# https://docs.agentnetwork.org.cn/docs/zh/getting-started/install/
anet --version         # 确认 CLI 可用
anet daemon            # 首次启动会生成 ~/.anet/api_token
```

### 2. 打开 ANet 接入

编辑 `backend/.env`：
```env
ANET_ENABLED=true
ANET_SERVICE_ENDPOINT=http://127.0.0.1:8000
```

### 3. 启动后端

```powershell
cd e:\hackathon\Nankesong\OpenSucker\backend
uvicorn app.main:app --reload
```

启动日志会包含一行：
```
ANet ready: name=opensucker-skill-distill ans.published=True meta.attempted=False
```

### 4. 验证注册

浏览器访问 [http://127.0.0.1:8000/api/v1/anet/status](http://127.0.0.1:8000/api/v1/anet/status)，或：
```powershell
python -m scripts.anet_register status
```
返回：
```json
{
  "available": true,
  "daemon_url": "http://127.0.0.1:3998",
  "service_name": "opensucker-skill-distill",
  "registered": true,
  "registration": {...},
  "health": {"name": "...", "status": "healthy", "code": 200}
}
```

### 5. 跨节点调用（评审 demo）

在第二个 daemon 上（可以用另一个 `ANET_HOME` 环境变量隔离）：
```python
from anet.svc import SvcClient

with SvcClient() as svc:
    peers = svc.discover(skill="skill-distillation")
    p = peers[0]
    resp = svc.call(
        p["peer_id"], "opensucker-skill-distill",
        "/api/v1/skills/distill",
        method="POST",
        body={"name": "彼得·林奇", "locale": "zh-CN"},
    )
    job_id = resp["body"]["job_id"]
    # 轮询
    while True:
        st = svc.call(p["peer_id"], "opensucker-skill-distill",
                      f"/api/v1/skills/jobs/{job_id}", method="GET")
        if st["body"]["status"] in ("done", "failed"): break
    # 取 SKILL.md
    skill = svc.call(p["peer_id"], "opensucker-skill-distill",
                     f"/api/v1/skills/jobs/{job_id}/skill", method="GET")
    print(skill["body"])
```

---

## 五、管理端点

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/api/v1/anet/status` | 是否启用、daemon 是否可达、是否已注册、health。 |
| `POST` | `/api/v1/anet/register` | 强制（重新）注册。`force=True` 幂等。 |
| `POST` | `/api/v1/anet/unregister` | 注销本 service。 |
| `GET` | `/api/v1/anet/discover?skill=X&limit=10` | 按 skill tag 查 peer。 |

当 `ANET_ENABLED=false`：`/status` 返回 `{"enabled": false}`；其余三个返回 503。

---

## 六、CLI 快捷用法

`backend/scripts/anet_register.py` 是个独立脚本，不依赖 FastAPI 进程，适合用在 PowerShell / CI 里：

```powershell
cd backend

# 注册（幂等，会先 unregister 再 register）
python -m scripts.anet_register register

# 看 daemon 状态和我们的注册情况
python -m scripts.anet_register status

# 查找其他 peer
python -m scripts.anet_register discover skill-distillation

# 注销
python -m scripts.anet_register unregister
```

---

## 七、测试

```powershell
cd backend
pytest tests/test_services/test_agentnet.py -v
```

测试用 `monkeypatch` 替换 `anet.svc.SvcClient` 为 `FakeSvcClient`，覆盖：

- 默认参数注册：路径、tags、endpoint、health_check 都来自 settings
- `force=True/False` 语义：前者先 unregister 再 register，后者直接 register
- unregister 路径
- `discover` 返回 peer 列表
- `AuthMissingError` → `AnetUnavailable`
- `ANET_ENABLED=false` 时 `probe()` 不抛

没有真实 daemon 时：

- 全套后端 pytest（13 个）通过
- `python -m scripts.anet_register status` 返回 `{"available": false, "error": "no ANet API token: ..."}`
- FastAPI 正常启动，日志提示 "ANet integration disabled" 或 "ANet unavailable at startup"

---

## 八、排查

### 启动时日志出现 `ANet unavailable at startup: ...`
- 先看 daemon 是否在跑：`anet status`。
- 看 token：`type %USERPROFILE%\.anet\api_token`（Windows）或 `cat ~/.anet/api_token`。
- 确认 `ANET_DAEMON_URL` 指向的端口和 `anet daemon` 启动时的端口一致。

### `status` 返回 `"registered": false`
- 手工触发：`POST /api/v1/anet/register` 或 `python -m scripts.anet_register register`。
- 看 daemon 日志：`anet logs`。

### peer 调用返回 502 / `endpoint unreachable`
- daemon 把请求反代到 `ANET_SERVICE_ENDPOINT`。确认 FastAPI 正在监听这个 URL，且 daemon 所在宿主机能访问。
- Docker 环境下把 `ANET_SERVICE_ENDPOINT` 改成 `http://host.docker.internal:8000`，并在 daemon 配置里把宿主机加入 `svc_remote_allowlist`。

### 想临时下线
- 设 `ANET_ENABLED=false` 重启，或直接 `POST /api/v1/anet/unregister`。

### SDK 升级
- 新版 `anet-sdk` 如果改了 `SvcClient.register` 的参数名，改 `backend/app/core/agentnet.py` 一个文件即可。业务代码不依赖 SDK 细节。

---

## 九、后续扩展（留给之后）

- **Task + bundle 路径**：作为 svc 的补充，实现 worker sidecar，接 `anet task board` 上 tag=`skill-distillation` 的任务，用 `Lifecycle` 五动词交付。能从 publisher/worker/evidence/accept 侧讲更完整的故事，对接 credits / reputation。参考 [`anet.lifecycle.Lifecycle`](https://docs.agentnetwork.org.cn/docs/zh/reference/sdk-api/)。
- **Knowledge 发布**：`AgentNetwork.knowledge_publish()` 把 `SKILL.md` 作为知识条目广播，供其它 Agent 搜索复用。
- **SSE stream 模式**：`svc.stream()` 把 Job 进度实时推给调用方，不再轮询。
- **svc 计费**：`register(free=False, per_call=..., deposit=...)` 把蒸馏按次计价，打通 ANet 经济模型。

---

## 参考

- [Agent Network 愿景](https://docs.agentnetwork.org.cn/docs/zh/wiki/agent-network-vision/)
- [P2P Service Gateway SDK（SvcClient 源码）](https://docs.agentnetwork.org.cn/docs/zh/sdks/overview/)
- [SDK API 参考](https://docs.agentnetwork.org.cn/docs/zh/reference/sdk-api/)
- [CLI 参考](https://docs.agentnetwork.org.cn/docs/zh/reference/cli-reference/)
- [5 分钟上手](https://docs.agentnetwork.org.cn/docs/zh/getting-started/quickstart-5-min/)
- [南客松 hackathon 赛道](https://agentnetwork.org.cn/hackathon.html)
