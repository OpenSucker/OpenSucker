"""
Skills Manager — OpenSucker 三层技能架构
=========================================
Layer 2: 矩阵专家技能 (skills/X3Y3/SKILL.md)
Layer 3: 智慧顾问技能 (skills/personas/buffett/SKILL.md)

矩阵专家可以主动"召唤"顾问，将其智慧注入 system prompt。
"""
from __future__ import annotations
import os
import re
from typing import Optional, Dict, Tuple

# 技能根目录（相对于 backend/）
SKILLS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "skills"))

# 矩阵格子 → 可召唤的顾问列表
CELL_PERSONA_MAP: Dict[str, list] = {
    "X4Y1": ["buffett"],   # 宏观探索 → 巴菲特择时思想最契合
    "X4Y2": ["buffett"],   # 宏观审计
    "X2Y2": ["buffett"],   # 技术审计 → 护城河/Owner Earnings
    "X3Y3": ["buffett"],   # 战术执行 → 仓位决策价值验证
    "X1Y1": ["buffett"],   # 情绪探索 → 贪婪恐惧逆向逻辑
}


# 基于 Intent 的 Vibe 专业量化库挂载
INTENT_VIBE_SKILLS_MAP: Dict[str, list] = {
    "market_analysis": ["candlestick", "chanlun", "elliott-wave", "harmonic", "ichimoku", "smc", "technical-basic"],
    "stock_scan": ["multi-factor", "factor-research", "quant-statistics", "fundamental-filter"],
    "trade_execution": ["asset-allocation", "hedging-strategy", "risk-analysis", "execution-model"],
    "portfolio_audit": ["valuation-model", "earnings-forecast", "edgar-sec-filings", "social-media-intelligence"],
    "committee": ["global-macro", "macro-analysis", "geopolitical-risk", "sector-rotation", "sentiment-analysis", "behavioral-finance"],
}

def _parse_skill_md(content: str) -> Tuple[Dict, str]:
    """解析 SKILL.md，分离 YAML frontmatter 和 Markdown 正文"""
    meta: Dict = {}
    body = content

    # 检测 YAML frontmatter (--- ... ---)
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if match:
        yaml_block = match.group(1)
        body = match.group(2).strip()
        # 简单解析 key: value
        for line in yaml_block.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()

    return meta, body


def load_skill(skill_path: str) -> Optional[Dict]:
    """加载单个 SKILL.md，返回 {name, description, body}"""
    skill_file = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_file):
        return None
    try:
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()
        meta, body = _parse_skill_md(content)
        return {
            "name": meta.get("name", os.path.basename(skill_path)),
            "description": meta.get("description", ""),
            "body": body,
            "path": skill_path,
        }
    except Exception as e:
        print(f"⚠️ 加载技能失败 {skill_path}: {e}")
        return None


def load_cell_skill(cell_id: str) -> Optional[Dict]:
    """加载矩阵格子的 Layer 2 技能（如 X3Y3）"""
    path = os.path.join(SKILLS_ROOT, cell_id)
    return load_skill(path)


def load_persona_skill(persona_name: str) -> Optional[Dict]:
    """加载 Layer 3 智慧顾问技能（如 buffett）"""
    path = os.path.join(SKILLS_ROOT, "personas", persona_name)
    return load_skill(path)


def load_vibe_skill(skill_name: str) -> Optional[Dict]:
    """加载 Layer 4 Vibe 专业技能 (如 chanlun)"""
    path = os.path.join(SKILLS_ROOT, "vibe_skills", skill_name)
    return load_skill(path)


def build_system_prompt_with_skills(
    base_prompt: str,
    cell_id: str,
    intent_str: str = "chitchat"
) -> Tuple[str, str]:
    """
    将三层技能注入 system_prompt。
    返回 (增强后的 system_prompt, 技能使用摘要)
    """
    parts = [base_prompt]
    skill_labels = []

    # 提取列 ID (X1, X2...)
    col_id = cell_id[:2]

    # Layer 2: 矩阵格子主技能
    cell_skill = load_cell_skill(cell_id)
    if cell_skill:
        parts.append(f"\n\n## 专家核心技能 [{cell_skill['name']}]\n{cell_skill['body']}")
        skill_labels.append(cell_skill["name"])

    # Layer 3: 智慧顾问 (Buffett/Munger)
    personas = CELL_PERSONA_MAP.get(cell_id, [])
    for persona_name in personas:
        persona_skill = load_persona_skill(persona_name)
        if persona_skill:
            summary = persona_skill["body"][:2000]
            parts.append(f"\n\n## 智慧顾问视角 [{persona_skill['name']}]\n{summary}")
            skill_labels.append(persona_skill["name"])

    # Layer 4: Vibe 专业量化技能库 (基于 Intent 和 列 ID 智能路由)
    # 首先根据意图获取候选池，如果未命中则降级使用列 ID 的默认池
    vibe_skill_names = INTENT_VIBE_SKILLS_MAP.get(intent_str, [])
    
    # 为了防止一次性加载太多导致 Token 溢出，我们最多随机/按需加载 3 个
    # 在这里，为了稳定，我们按顺序取前 3 个。如果需要深度研究，可以引入 RAG。
    loaded_count = 0
    for vs_name in vibe_skill_names:
        if loaded_count >= 3: break
        vs = load_vibe_skill(vs_name)
        if vs:
            parts.append(f"\n\n### 补充专业方法论: {vs['name']}\n{vs['body'][:1500]}")
            # 内部静默加载
            loaded_count += 1

    enhanced_prompt = "\n".join(parts)
    skill_summary = " | ".join(skill_labels) if skill_labels else ""

    return enhanced_prompt, skill_summary
