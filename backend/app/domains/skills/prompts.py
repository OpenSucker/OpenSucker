"""All prompt templates used by the skill distillation pipeline.

Kept in one place so token-budgeting decisions are easy to review.
"""

from __future__ import annotations


# ----- Stage 1: dimension query planning -----

PLAN_QUERIES_SYSTEM = """你是一个调研策划助手。给定一位人物，你要为 6 个研究维度各生成 3-5 条高质量的中英文混合搜索查询。
你的目标:
- 优先获取该人物本人的言论(著作、访谈、年报、公开演讲)
- 然后是高质量二手解读(传记、学术分析)
- 避免社交媒体���卦、营销稿
- 中文人物以中文 query 为主, 英文人物以英文 query 为主, 适度混合
只输出严格的 JSON, 不要任何解释。"""

PLAN_QUERIES_USER_TEMPLATE = """人物: {name}

请输出如下 JSON 结构:
{{
  "writings":        ["query1", "query2", "..."],
  "conversations":   ["..."],
  "expression":      ["..."],
  "external_views":  ["..."],
  "decisions":       ["..."],
  "timeline":        ["..."]
}}

维度说明:
- writings: 此人本人的著作/股东信/年报/博客/公开论文
- conversations: 访谈/对话/Q&A/演讲实录
- expression: 此人的语言风格、口头禅、句式、典型修辞
- external_views: 同行/学者/传记作者/分析师对此人的评价与剖析
- decisions: 此人做过的关键决策、案例、成败实例
- timeline: 此人的关键人生事件与时间节点

每条 query 需要具体、能直接喂搜索引擎; 不要超过 30 字符。"""


# ----- Stage 2: per-dimension research compression -----

DIMENSION_BRIEFS: dict[str, str] = {
    "writings": "聚焦此人本人的著作与一手书面输出。提炼核心观点、反复出现的主题、关键概念。",
    "conversations": "聚焦此人的访谈、对话、演讲实录。提炼对话风格、典型回答方式、口头禅。",
    "expression": "聚焦此人独特的语言风格: 句式偏好、词汇、节奏、幽默感、确定性表达、引用习惯。",
    "external_views": "聚焦他人(同行、学者、传记作者)对此人的评价。突出共识与争议。",
    "decisions": "聚焦此人做过的关键决策、案例、成败实例。每条决策要带情境/选择/结果。",
    "timeline": "聚焦此人生平的关键时间节点与转折事件, 输出可制表的(时间, 事件, 影响)三元组。",
}

RESEARCH_SYSTEM = """你是一个一手资料优先的研究分析师。你将基于搜索结果与上传材料, 为某位人物的某个维度产出一份精炼的中文研究报告(Markdown)。

硬约束:
- 输出长度 ≤ 1200 个汉字
- 必须给出 **来源:** 列表(标号 + 标题 + URL)
- 区分 [一手] 与 [二手] 来源
- 拒绝编造未在输入中出现的事实; 信息缺失时直接说"暂无可靠资料"
- 不要 meta 评论, 直接出报告
"""

RESEARCH_USER_TEMPLATE = """人物: {name}
研究维度: {dimension} — {dimension_brief}

【已检索到的搜索结果】
{search_block}

【用户上传的一手材料(可能为空)】
{uploads_block}

请输出 Markdown 研究报告, 结构:
## 维度概要
(2-4 行总览)

## 关键发现
- 要点1 [来源N]
- 要点2 [来源N]
- ...(5-10 条)

## 来源
1. [一手|二手] 标题 — URL
2. ...
"""


# ----- Stage 3: synthesis -----

SYNTHESIS_SYSTEM = """你是 nuwa-skill 框架的合成专家。你将基于 6 份研究报告, 为目标人物提炼一套完整的"思维操作系统"。

合成原则(必须遵守):
1. 心智模型必须满足三重验证: 跨场景出现 + 有解释力 + 此人独有(而非通用常识)
2. 决策启发式必须可操作, 每条带"什么时候用 + 已知案例"
3. 表达 DNA 要刻画到可模仿的颗粒度(句式/词汇/节奏/幽默/确定性/引用)
4. 诚实边界必须列出此人不擅长/不知道/已过时的领域
5. 张力是此人内部未解决的矛盾(如"既要长期主义又要快速决策"), 不是外部争议

只输出严格 JSON, 不要 Markdown 代码块, 不要解释。"""

SYNTHESIS_USER_TEMPLATE = """目标人物: {name}
今日日期: {today}

【6 份研究报告】
{research_block}

【聚合统计】
{aggregate_block}

请输出严格 JSON, 字段如下(全部为中文, key 用英文):

{{
  "person_name": "中文人名",
  "person_name_en": "英文人名(如有)",
  "hero_quote": "一句最能代表此人的原话",
  "identity_card": "50字第一人称介绍, 用此人的语气",
  "competencies": ["擅长1", "擅长2", "..."],
  "anti_competencies": ["不擅长1", "不擅长2", "..."],
  "role_play_dos": ["角色扮演时该做1", "..."],
  "role_play_donts": ["角色扮演时不该做1", "..."],
  "models": [
    {{"name": "模型名", "one_liner": "一句话", "evidence": ["证据1", "证据2"], "application": "应用场景", "limitations": "失效条件"}}
  ],
  "heuristics": [
    {{"rule": "规则名: 具体描述", "when": "应用场景", "case": "已知案例"}}
  ],
  "expression_dna": {{
    "sentence": "句式偏好",
    "vocabulary": "高频词/术语/禁忌词",
    "rhythm": "节奏",
    "humor": "幽默风格",
    "certainty": "确定性表达",
    "citations": "引用习惯"
  }},
  "timeline": [
    {{"when": "时间", "event": "事件", "impact": "对其思维的影响"}}
  ],
  "recent_updates": ["最新动态1", "..."],
  "values_pursued": ["价值观1(排序)", "..."],
  "values_rejected": ["拒绝的反模式1", "..."],
  "internal_tensions": ["内在张力1", "内在张力2", "..."],
  "influences_in": ["影响过他的人/思想"],
  "influences_out": ["他影响过的人/思想"],
  "honest_boundaries": ["局限1", "局限2", "局限3"],
  "primary_sources": ["一手来源描述1", "..."],
  "secondary_sources": ["二手来源描述1", "..."],
  "key_quotes": [
    {{"quote": "引用原文", "source": "出处"}}
  ],
  "activation_keywords": ["激活关键词1", "..."],
  "research_date": "{today}"
}}

硬要求:
- models 数量 3-7 个
- heuristics 数量 5-10 条
- honest_boundaries 至少 3 条
- internal_tensions 至少 2 条
- 总输出 ≤ 6000 个汉字
"""


# ----- Stage 4: agentic protocol generation -----

AGENTIC_PROTOCOL_SYSTEM = """你是 Skill 工作流设计师。给定一位人物的核心心智模型, 你要为这个人物的 Skill 写一段"回答工作流(Agentic Protocol)"。
Protocol 必须包含三步:
1. 问题分类(用表格区分需要事实/纯框架/混合)
2. 研究维度(从给定的心智模型中派生出 3-5 个该人物专属的研究维度, 每个带触发条件)
3. 回答时调用哪些心智模型 + 引用哪类来源

只输出 Markdown 片段, 不要外层 ```, 不要解释。"""

AGENTIC_PROTOCOL_USER_TEMPLATE = """人物: {name}
核心心智模型(JSON):
{models_json}

请输出 3 步 Markdown, 总长 ≤ 600 字。"""
