# OpenSucker · Agent Network 上网证明

> 本文档记录 OpenSucker 投资大师 Skill 蒸馏服务在 Agent Network 主网上的**活体注册证据**。每一条都可由评委在其本地 `anet daemon` 上复现验证。
>
> 快照时间：**2026-05-02 15:43 (UTC+8)**
> 本机 daemon uptime：已连续运行 15 分 18 秒

---

## 一、身份

| 字段 | 值 |
|---|---|
| **DID** | `did:key:z6MkfG6MCPAve6hFWmDauYbAGwmzjihrxVGNq3za1aU6Snw9` |
| **Peer ID** | `12D3KooWAdCUMGWCVTUGp9tJraNfCeJqQUUeaJ6W6dSfZHeyRWsh` |
| **Agent URI** | `agent://svc/opensucker-skill-distill-9020fe3d` |
| **Service Name** | `opensucker-skill-distill` |
| **Owner's DID = Registrant's DID** ✅ | 由签名校验 |

---

## 二、网络位置

```
daemon 版本     : 1.1.11
直连 peers      : 8
overlay peers   : 83
隔离模式        : off
本机监听端口    : tcp 4001 · ws 4002 · quic 4001
```

我们是一个**真实参与 libp2p mesh 的节点**，不是只对自己可见。

---

## 三、ANS 注册记录（活体拉取自 `GET /api/ans/records`）

```json
{
  "name": "agent://svc/opensucker-skill-distill-9020fe3d",
  "peer_id": "12D3KooWAdCUMGWCVTUGp9tJraNfCeJqQUUeaJ6W6dSfZHeyRWsh",
  "namespace": "svc",
  "skills": [
    "skill-distillation",
    "investor-perspective",
    "mental-model",
    "svc:opensucker-skill-distill"
  ],
  "description": "OpenSucker 投资大师 Skill 蒸馏：输入人名，输出决策系统 SKILL.md",
  "ttl": 86400,
  "registered_at": "2026-05-02T07:28:49Z",
  "expires_at":   "2026-05-03T07:28:49Z",
  "owner_id": "did:key:z6MkfG6MCPAve6hFWmDauYbAGwmzjihrxVGNq3za1aU6Snw9",
  "seq": 1,
  "signature": "FVwBIU0G8DsZgDKTItXTYktJMiJyFl6V_UFSdfd-XGYRyPTq0Ge1IC7QgndsSX7G5LXtkTJS5YiBW-4T8IuKDA",
  "state": "registered",
  "extensions": {
    "service": "opensucker-skill-distill",
    "transport": "http",
    "modes": ["rr"],
    "paths": [
      {"prefix": "/api/v1/skills"},
      {"prefix": "/api/v1/health"}
    ],
    "health_check": "/api/v1/health",
    "cost_model": {"free": true}
  }
}
```

**`state: registered` + 有效 `signature` + `ttl 86400s` = 合法的、签名过的、24h 有效的链上注册记录。**

---

## 四、Discovery 证据（任意 ANet 节点可复现）

```bash
$ anet discover skill-distillation
🦞 ANS Search  q="skill-distillation"  1 result(s)
  [1] agent://svc/opensucker-skill-distill-9020fe3d
      — OpenSucker 投资大师 Skill 蒸馏：输入人名，输出决策系统 SKILL.md
      [skill-distillation,investor-perspective,mental-model,svc:opensucker-skill-distill]
```

**在我们的 DID 标签组合下，全网我们是唯一命中项。** 这意味着任何 peer 想找「投资大师思维框架蒸馏」能力，会直接指到我们这里。

---

## 五、P2P Service Gateway 活体反代证据

Daemon 每次对外声明 health 都会实际 HTTP 探活我们 FastAPI 的 `/api/v1/health`。当前探活结果：

```
$ curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3998/api/svc/health
[{"name":"opensucker-skill-distill","status":"healthy","code":200,"latency_ms":1}]
```

**`latency_ms: 1–2`** ＝ daemon ↔ FastAPI 端到端响应 <2ms，说明 P2P Service Gateway 到业务后端的反向代理已真实联通。

CLI 视角：

```
$ anet svc list
NAME                      TRANSPORT  MODES  ENDPOINT               COST  TAGS
opensucker-skill-distill  http       rr     http://127.0.0.1:8000  free  skill-distillation,investor-perspective,mental-model

$ anet svc health
NAME                      STATUS   CODE  LATENCY  ERROR
opensucker-skill-distill  healthy  200   2ms
```

---

## 六、可被远程调用（外部 peer 复现脚本）

任意接入 Agent Network 的 peer，在另一台机器上装好 `anet-sdk`、启动本地 daemon，然后执行：

```python
from anet.svc import SvcClient

with SvcClient() as svc:
    # 1) 发现我们
    peers = svc.discover(skill="skill-distillation")
    assert peers, "no peers found"
    target = next(p for p in peers
                  if p["peer_id"] == "12D3KooWAdCUMGWCVTUGp9tJraNfCeJqQUUeaJ6W6dSfZHeyRWsh")

    # 2) 发起蒸馏
    resp = svc.call(
        target["peer_id"],
        "opensucker-skill-distill",
        "/api/v1/skills/distill",
        method="POST",
        body={"name": "彼得·林奇", "locale": "zh-CN"},
    )
    print("HTTP", resp["status"], "→", resp["body"])
    # 期望：HTTP 202 + {"job_id": "...", "slug": "bi-de-lin-qi", "status": "queued"}

    job_id = resp["body"]["job_id"]

    # 3) 轮询
    import time
    while True:
        st = svc.call(target["peer_id"], "opensucker-skill-distill",
                      f"/api/v1/skills/jobs/{job_id}", method="GET")
        print(st["body"]["status"], st["body"].get("current_stage"))
        if st["body"]["status"] in ("done", "failed"):
            break
        time.sleep(5)

    # 4) 下载 SKILL.md
    skill = svc.call(target["peer_id"], "opensucker-skill-distill",
                     f"/api/v1/skills/jobs/{job_id}/skill", method="GET")
    print(skill["body"][:500])
```

**每一步的 HTTP 都是 P2P gateway 跨节点转发的，不走公网 IP，不靠反向代理中心，只靠 libp2p + ANS 寻址。**

---

## 七、关于 hackathon.html 不显示我们的说明

`https://agentnetwork.org.cn/hackathon.html` 是**构建时生成的静态页面**，不是实时查询网络的浏览器入口。其 JS bundle 里硬编码了一份快照：

```js
const s = be;               // 打包进 JS 的数据
s.generated_at = "2026-05-02 14:17"    // 北京时间
s.totalRecords = 89
// 渲染时还会过滤 curated=true
```

OpenSucker 的注册时间是 **2026-05-02 15:28 北京时间**，晚于快照生成时间 **14:17**，因此没进入本轮 bundle。即便进了，该页面只展示主办方标注 `curated: true` 的条目，属于策展性质。

**本项目的可发现性不依赖该页面**。活体证据链是：
1. 我们的 ANS 注册条目在 `/api/ans/records` 里真实存在、签名合法、未过期
2. `anet discover skill-distillation` 全网可命中
3. 远端 peer 可通过 `svc.call(peer_id, name, path, body)` 跨节点请求我们
4. daemon ↔ FastAPI 反代活跃，`health=200, latency=1-2ms`

---

## 八、复现命令（评委自验）

前置：在任意 Linux/macOS/Windows 上装好 `anet` CLI 并 `anet daemon` 成功启动。

```bash
# 1. 看我们是否在 ANS 上
anet discover skill-distillation

# 2. 精确解析我们的 Agent URI
anet resolve agent://svc/opensucker-skill-distill-9020fe3d

# 3. 如果已和我们 peer 直连（mDNS / bootstrap），可直接调用：
# (用你自己的 Python SDK 按 §六 脚本执行)

# 4. 读 ANS raw record
TOKEN=$(cat ~/.anet/api_token)   # Windows: %USERPROFILE%\.anet\api_token
curl -s -H "Authorization: Bearer $TOKEN" \
     http://127.0.0.1:3998/api/ans/records \
  | jq '.records[] | select(.name|contains("opensucker"))'
```

---

## 九、本地开发者侧也可直接验证

OpenSucker 后端自己暴露了诊断端点：

```bash
curl http://127.0.0.1:8000/api/v1/anet/status       # 我们看到的 daemon + 注册状态
curl http://127.0.0.1:8000/api/v1/anet/discover?skill=skill-distillation
```

或 CLI：

```bash
cd backend
python -m scripts.anet_register status    # JSON 形式的全貌
```

---

## 附：技术栈对齐

- **Agent Network 版本**：CLI 1.1.11 · daemon 1.1.11
- **SDK**：`anet-sdk 1.1.0`（Python）
- **业务后端**：FastAPI / Uvicorn · Python 3.12.2
- **注册入口**：`backend/app/services/anet_register.py:register_on_startup()`
- **适配器**：`backend/app/core/agentnet.py:AnetClient.register_skill_distill()`
- **配置项**：`backend/.env` 中 `ANET_ENABLED=true` + `ANET_*` 系列
- **协议契合**：`GET /api/v1/skills/*`、`POST /api/v1/skills/distill` 全部走标准 HTTP rr 模式，兼容 SDK `svc.call()`

---

<p align="center"><i>Proof of Liveness · 2026-05-02</i></p>
