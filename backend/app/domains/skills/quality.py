"""Quality checks for a generated SKILL.md.

Ported from nuwa-skill scripts/quality_check.py so the pipeline can call it
in-process instead of shelling out. Returns per-rule (passed, detail) tuples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def _check_mental_models(content: str) -> tuple[bool, str]:
    models = re.findall(r"^###\s+(?:模型|Model|心智模型)\s*\d", content, re.MULTILINE)
    count = len(models)
    if count == 0:
        in_section = False
        for line in content.split("\n"):
            if re.match(r"^##\s+.*心智模型|Mental Model", line, re.IGNORECASE):
                in_section = True
                continue
            if in_section and re.match(r"^##\s+", line) and "心智模型" not in line:
                break
            if in_section and re.match(r"^###\s+", line):
                count += 1
    if count == 0:
        return False, "未检测到心智模型 section"
    passed = 3 <= count <= 7
    return passed, f"{count} 个心智模型 {'✅' if passed else '❌ (应为 3-7 个)'}"


def _check_limitations(content: str) -> tuple[bool, str]:
    has = bool(re.search(r"局限|失效|不适用|盲区|limitation|blind spot", content, re.IGNORECASE))
    return has, "有局限性标注 ✅" if has else "❌ 未找到局限性描述"


def _check_expression_dna(content: str) -> tuple[bool, str]:
    section = bool(re.search(r"表达 ?DNA|Expression DNA|表达风格", content, re.IGNORECASE))
    if not section:
        return False, "❌ 未找到表达 DNA section"
    markers = len(re.findall(r"句式|词汇|语气|幽默|节奏|确定性|引用|口头禅", content))
    passed = markers >= 3
    return passed, f"表达 DNA 特征 {markers} 项 {'✅' if passed else '❌ (应≥3)'}"


def _check_honest_boundary(content: str) -> tuple[bool, str]:
    m = re.search(
        r"(?:##\s+[^\n]*?诚实边界|## Honest Boundary)(.*?)(?=\n##\s|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return False, "❌ 未找到诚实边界 section"
    items = re.findall(r"^[-*]\s+", m.group(1), re.MULTILINE)
    count = len(items)
    passed = count >= 3
    return passed, f"诚实边界 {count} 条 {'✅' if passed else '❌ (应≥3)'}"


def _check_tensions(content: str) -> tuple[bool, str]:
    markers = len(re.findall(r"张力|矛盾|tension|paradox|一方面.*另一方面|既.*又", content, re.IGNORECASE))
    passed = markers >= 2
    return passed, f"内在张力 {markers} 处 {'✅' if passed else '❌ (应≥2)'}"


def _check_primary_sources(content: str) -> tuple[bool, str]:
    m = re.search(
        r"(?:##\s+[^\n]*?来源|## Source|## Reference)(.*?)(?=\n##\s|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return True, "未找到来源 section(跳过)"
    text = m.group(1)
    primary = len(re.findall(r"一手|primary|本人著作|原始", text, re.IGNORECASE))
    secondary = len(re.findall(r"二手|secondary|转述|评论", text, re.IGNORECASE))
    total = primary + secondary
    if total == 0:
        return True, "未标记来源类型(跳过)"
    ratio = primary / total
    passed = ratio >= 0.5
    return passed, f"一手来源 {primary}/{total} ({ratio:.0%}) {'✅' if passed else '❌ (应≥50%)'}"


_CHECKS = (
    ("心智模型数量", _check_mental_models),
    ("模型局限性", _check_limitations),
    ("表达 DNA 辨识度", _check_expression_dna),
    ("诚实边界", _check_honest_boundary),
    ("内在张力", _check_tensions),
    ("一手来源占比", _check_primary_sources),
)


def run_checks(content: str) -> list[CheckResult]:
    out: list[CheckResult] = []
    for name, fn in _CHECKS:
        try:
            passed, detail = fn(content)
        except Exception as exc:  # noqa: BLE001
            passed, detail = False, f"check 异常: {exc}"
        out.append(CheckResult(name=name, passed=passed, detail=detail))
    return out


def summarize(results: list[CheckResult]) -> tuple[int, int]:
    passed = sum(1 for r in results if r.passed)
    return passed, len(results)
