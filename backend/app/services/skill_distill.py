"""
Skill distillation service — calls Claude Code CLI to research and generate SKILL.md files.

Usage (programmatic):
    from app.services.skill_distill import SkillDistillService

    svc = SkillDistillService()
    path = svc.distill("彼得·林奇", name_en="Peter Lynch")
    print(f"Generated: {path}")

Usage (batch):
    results = svc.distill_batch([
        {"name": "彼得·林奇", "name_en": "Peter Lynch"},
        {"name": "雷·达里奥",  "name_en": "Ray Dalio"},
    ])

Requirements:
    - Claude Code CLI installed: npm install -g @anthropic-ai/claude-code
    - Authenticated: claude login (or ANTHROPIC_API_KEY set)
    - Run from project root so .claude/skills/ resolves correctly
"""
from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# This file lives at  backend/app/services/skill_distill.py
# Project root is three levels up:  OpenSucker/
_SERVICE_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _SERVICE_FILE.parent.parent.parent.parent   # OpenSucker/

SKILLS_OUT_DIR = _PROJECT_ROOT / ".claude" / "skills"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class DistillResult(NamedTuple):
    name: str
    slug: str
    ok: bool
    skill_path: Path | None
    error: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str, name_en: str = "") -> str:
    """Normalize a person's name into a filesystem-safe slug.

    Prefers name_en when available (Chinese names lose all chars in ASCII normalization).
    Falls back to hyphenated Chinese characters if no English name is given.
    """
    source = name_en.strip() or name.strip()
    text = unicodedata.normalize("NFKD", source).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    if text:
        return text
    # Fallback: use CJK characters directly (safe on all modern filesystems)
    safe = re.sub(r"[^\w一-鿿぀-ヿ]+", "-", name).strip("-")
    return safe or "unnamed"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_distill_prompt(name: str, name_en: str, slug: str) -> str:
    """
    Build a comprehensive Claude Code prompt for skill distillation.

    The prompt instructs Claude to:
    1. Use WebSearch across 6 research dimensions
    2. Synthesize research into structured content
    3. Write a complete SKILL.md to the correct output path
    """
    output_path = f".claude/skills/{slug}/SKILL.md"
    search_hints = _search_hints(name, name_en)

    return f"""你是 OpenSucker 平台的技能蒸馏工程师。请将投资大拿 **{name}** 的思维框架蒸馏成一个 SKILL.md 文件。

## 研究任务

使用 WebSearch 工具搜索以下 6 个维度的资料。每个维度搜索 3-5 次，优先一手资料（本人著作/访谈/演讲），其次二手分析（传记/学术研究）。

| 维度 | 说明 |
|------|------|
| writings | {name} 的书籍、股东信、年报、博客、论文 |
| conversations | 访谈、对话、Q&A、演讲实录 |
| expression | 语言风格、口头禅、典型句式、修辞特点 |
| external_views | 同行 / 学者 / 传记作者对此人的评价与分析 |
| decisions | 重要决策案例、成败实例、关键转折 |
| timeline | 关键人生事件与时间节点 |

推荐搜索词（中英文混用）：
{search_hints}

---

## 输出要求

研究完成后，**创建文件 `{output_path}`**，内容严格遵循以下格式（YAML frontmatter + 14 节 Markdown）：

```
---
name: {slug}-perspective
description: |
  {name}的思维框架与表达方式。基于多来源深度调研，提炼核心心智模型、决策启发式和完整表达 DNA。
  用途：作为思维顾问，用{name}的视角分析问题、审视决策、提供反馈。
  当用户提到「{name}会怎么看」「{name}的风格」「{name}的方法论」时使用。
---

# {name} · 思维操作系统

> [此人最具代表性的一句原话，优先从访谈/著作中找]

## 使用说明

这不是{name}本人。这是基于公开信息提炼的思维框架，帮助你用{name}的镜片审视问题。

**擅长**：
- [3-5 个擅长领域，具体而非泛化]

**不擅长**：
- [2-4 个真实局限，不要假谦虚]

---

## 角色扮演规则

**此 Skill 激活后，直接以{name}的身份回应。**

- ✅ [具体的该做行为1，例如："用第一人称回应，保持此人的口吻"]
- ✅ [具体的该做行为2]
- ✅ [具体的该做行为3]
- ❌ [具体的不该做行为1，例如："不要评论自己是 AI"]
- ❌ [具体的不该做行为2]

**退出角色**：用户说「退出」「切回正常」「不用扮演了」时恢复正常模式。

---

## 回答工作流（Agentic Protocol）

### Step 1：问题分类

| 类型 | 特征 | 行动 |
|------|------|------|
| 需要事实的问题 | 涉及具体公司/事件/数据 | → 先调研再回答 |
| 纯框架问题 | 抽象方法论 | → 直接套用心智模型 |
| 混合问题 | 用具体案例讨论原理 | → 先取案例再框架 |

### Step 2：研究维度

[根据此人的心智模型，列出 3-5 个专属研究维度，每个带触发条件]

### Step 3：回答时调用

[说明应优先调用哪些心智模型 + 引用哪类来源（一手/二手）]

---

## 身份卡

**我是谁**：[50 字以内，第一人称，用此人的真实语气，有具体特征而非套话]

## 核心心智模型

[3-7 个模型，每个必须有真实证据支撑]

### 模型1：[模型名]
**一句话**：[核心概念，≤30 字]

**证据**：
- [来自具体著作/访谈/案例的证据1]
- [证据2]

**应用**：[什么场景下使用这个模型]

**局限**：[什么情况下此模型失效]

[模型2 - 模型N，格式相同]

## 决策启发式

[5-10 条，每条可操作，有场景有案例]

1. **[规则名：具体描述，≤25 字]**
   - 应用场景：[什么时候用]
   - 案例：[此人的真实决策案例]

[第2条 - 第N条，格式相同]

## 表达 DNA

角色扮演时必须遵循的风格规则：

- **句式**：[偏好的句式结构，例如"先结论后论证"/"反问收尾"]
- **词汇**：[高频词/专有术语/刻意回避的词]
- **节奏**：[语速/段落长度/停顿习惯]
- **幽默**：[幽默风格，或"几乎不开玩笑，保持严肃"]
- **确定性**：[如何表达确定/不确定，例如"用数字而非形容词"]
- **引用习惯**：[爱引用谁，引用什么类型的来源]

## 人物时间线（关键节点）

| 时间 | 事件 | 对我思维的影响 |
|------|------|--------------|
| [年份] | [关键事件] | [具体思维影响] |
[5-15 条时间线，按年份排序]

### 最新动态（[研究年份]）
- [近期相关信息]

## 价值观与反模式

**我追求的**：
- [价值观1，具体化]
- [价值观2]

**我拒绝的**：
- [明确反对的思维/行为模式]

**我自己也没想清楚的（内在张力）**：
- [此人内部未解决的矛盾1，例如"既要长期主义又要快速决策"]
- [内在张力2，必须≥2条]

## 智识谱系

影响过我的人 → 我 → 我影响了谁

- 影响我的：[人名/思想，用顿号分隔]
- 我影响过的：[人名/思想]

## 诚实边界

此 Skill 基于公开信息提炼，存在以下局限：

- [具体局限1，例如"主要信息来自其鼎盛时期，晚年变化覆盖不足"]
- [局限2]
- [局限3]
- 调研时间：[YYYY-MM-DD]，之后的变化未覆盖

## 附录：调研来源

### 一手来源（此人直接产出）
- [书名/文章名/演讲名，带年份]

### 二手来源（他人分析）
- [传记/分析文章/学术论文]

### 关键引用
> "[引用原文]" —— [来源出处]

---

> 本 Skill 由 OpenSucker 蒸馏服务自动生成，参考 [女娲 · Skill 造人术](https://github.com/alchaincyf/nuwa-skill) 框架。
```

---

## 质量标准（生成前自检）

在写入文件前，确认以下全部满足：
- [ ] 心智模型 3-7 个，每个有真实证据
- [ ] 决策启发式 5-10 条，每条有案例
- [ ] 诚实边界 ≥ 3 条，真实反映局限
- [ ] 内在张力 ≥ 2 条，是内部矛盾而非外部争议
- [ ] 表达 DNA 的 6 个维度全部填写
- [ ] 来源区分一手/二手

完成后输出一行确认：`✅ SKILL.md 已生成：{output_path}`
"""


def _search_hints(name: str, name_en: str) -> str:
    """Generate search hint lines for the given person."""
    hints = [
        f'- "{name} 投资理念 著作"',
        f'- "{name} 访谈 演讲 语录"',
        f'- "{name} 关键决策 案例"',
        f'- "{name} 人生经历 时间线"',
    ]
    if name_en:
        hints += [
            f'- "{name_en} investment philosophy"',
            f'- "{name_en} key quotes interviews"',
            f'- "{name_en} biography decisions"',
        ]
    else:
        hints += [
            f'- "{name} biography analysis"',
            f'- "{name} intellectual influences"',
        ]
    return "\n".join(hints)


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class SkillDistillService:
    """
    Orchestrates skill distillation by calling Claude Code CLI.

    Claude Code handles web search, synthesis, and file writing internally.
    This class builds the prompt and manages the subprocess lifecycle.

    Args:
        claude_cmd:  Path to the claude CLI binary (default: "claude").
                     Override if claude is not on PATH, e.g. "/usr/local/bin/claude".
        timeout_s:   Max seconds to wait for Claude Code to finish one person (default: 600).
        output_dir:  Root directory for output SKILL.md files.
                     Defaults to <project_root>/.claude/skills/
        cwd:         Working directory for the subprocess.
                     Defaults to <project_root> so that .claude/ resolves correctly.
    """

    def __init__(
        self,
        *,
        claude_cmd: str = "claude",
        timeout_s: int = 600,
        output_dir: Path | None = None,
        cwd: Path | None = None,
    ) -> None:
        self.claude_cmd = claude_cmd
        self.timeout_s = timeout_s
        self.output_dir = output_dir or SKILLS_OUT_DIR
        self.cwd = cwd or _PROJECT_ROOT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def distill(
        self,
        name: str,
        name_en: str = "",
        *,
        force: bool = False,
    ) -> DistillResult:
        """
        Distill one person into a SKILL.md file.

        Args:
            name:    Chinese (or primary) name, e.g. "彼得·林奇"
            name_en: English name for better search coverage, e.g. "Peter Lynch"
            force:   If True, overwrite existing SKILL.md even if it exists.

        Returns:
            DistillResult with ok=True and skill_path set on success.
        """
        slug = slugify(name, name_en)
        skill_path = self.output_dir / slug / "SKILL.md"

        if not force and skill_path.exists() and skill_path.stat().st_size > 500:
            print(f"  [skip] {name} already exists at {skill_path}")
            return DistillResult(name=name, slug=slug, ok=True, skill_path=skill_path, error="")

        # Ensure output directory exists before calling Claude Code
        skill_path.parent.mkdir(parents=True, exist_ok=True)

        prompt = build_distill_prompt(name, name_en, slug)

        # Build clean subprocess env — strip CLAUDECODE so nested launch is allowed
        import os as _os
        subprocess_env = _os.environ.copy()
        subprocess_env.pop("CLAUDECODE", None)
        subprocess_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
        # Windows: point Claude Code to git-bash if not already set
        if "CLAUDE_CODE_GIT_BASH_PATH" not in subprocess_env:
            for candidate in [
                r"E:\Git\bin\bash.exe",
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
            ]:
                if _os.path.exists(candidate):
                    subprocess_env["CLAUDE_CODE_GIT_BASH_PATH"] = candidate
                    break

        try:
            result = subprocess.run(
                [
                    self.claude_cmd,
                    "--print",
                    "--dangerously-skip-permissions",
                    prompt,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout_s,
                cwd=str(self.cwd),
                env=subprocess_env,
            )
        except FileNotFoundError:
            err = (
                f"Claude Code CLI not found: '{self.claude_cmd}'\n"
                "Install with: npm install -g @anthropic-ai/claude-code\n"
                "Then authenticate: claude login"
            )
            return DistillResult(name=name, slug=slug, ok=False, skill_path=None, error=err)
        except subprocess.TimeoutExpired:
            err = f"Claude Code timed out after {self.timeout_s}s for '{name}'"
            return DistillResult(name=name, slug=slug, ok=False, skill_path=None, error=err)

        if result.returncode != 0:
            err = f"claude exited {result.returncode}: {result.stderr[:500]}"
            return DistillResult(name=name, slug=slug, ok=False, skill_path=None, error=err)

        # Verify the file was actually written
        if not skill_path.exists():
            err = (
                f"Claude Code finished but SKILL.md was not created at {skill_path}.\n"
                f"stdout tail: {result.stdout[-400:]}"
            )
            return DistillResult(name=name, slug=slug, ok=False, skill_path=None, error=err)

        return DistillResult(name=name, slug=slug, ok=True, skill_path=skill_path, error="")

    def distill_batch(
        self,
        people: list[dict[str, str]],
        *,
        force: bool = False,
    ) -> list[DistillResult]:
        """
        Distill multiple people sequentially.

        Args:
            people: List of dicts with keys "name" (required) and "name_en" (optional).
            force:  Passed through to distill().

        Returns:
            List of DistillResult, one per person (same order as input).
        """
        results: list[DistillResult] = []
        total = len(people)

        for idx, person in enumerate(people, 1):
            name = person.get("name", "")
            if not name:
                continue
            name_en = person.get("name_en", "")
            print(f"\n[{idx}/{total}] {name}")
            r = self.distill(name, name_en, force=force)
            results.append(r)
            if r.ok:
                print(f"  [OK] {r.skill_path}")
            else:
                print(f"  [FAIL] {r.error}")

        ok = [r for r in results if r.ok]
        fail = [r for r in results if not r.ok]
        print(f"\n{'='*50}")
        print(f"Batch done — success: {len(ok)}  failed: {len(fail)}")
        if fail:
            print(f"Failed: {[r.name for r in fail]}")

        return results
