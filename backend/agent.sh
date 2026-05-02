#!/bin/bash
# ============================================================
#  HairSync AI Agent — 本地启动脚本
#  用法: cd backend && bash agent.sh
# ============================================================

set -e
cd "$(dirname "$0")"

# ---- 自动激活 venv ----
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# ---- 本地模型（可选，没有就留空）----
# export MODEL_PATH="/path/to/Qwen2.5-1.5B-Instruct"
# export LORA_PATH="/path/to/lora_adapters"

# ============================================================
#  LLM API —— 硅基流动 SiliconFlow · Kimi K2.5
# ============================================================
# 👇 在这里填你的硅基流动 API Key（https://cloud.siliconflow.cn/account/ak）
#    ⚠️ 必须纯 ASCII，不要从聊天软件粘贴，手动敲防止混入中文引号/全角空格
export LLM_API_KEY="sk-"
# ⚠️ base_url 不带 /v1，代码会自动拼接
export LLM_API_BASE="https://api.siliconflow.cn"
# ⚠️ 默认改成 Kimi K2 Instruct (非 reasoning 版,比 K2.5 快 3-5 倍)
# K2.5 / K2-Thinking 是 reasoning models,首 token 延迟 30-90 秒,经常超时
# 想换 K2.5 (更智能但慢):  export LLM_API_MODEL="Pro/moonshotai/Kimi-K2.5"
# 想换 DeepSeek-V3 (中速): export LLM_API_MODEL="Pro/deepseek-ai/DeepSeek-V3"
# 想换 Qwen 7B (最快):     export LLM_API_MODEL="Qwen/Qwen2.5-7B-Instruct"
export LLM_API_MODEL="Pro/moonshotai/Kimi-K2.5"

# ============================================================
#  范式开关
# ============================================================
# USE_FUNCTION_CALLING=0 → state machine 范式 (硬编码 if-else 调工具, 快, xy_prompts 角色生效)
# USE_FUNCTION_CALLING=1 → function calling 范式 (LLM 自主决策调工具, 慢但灵活)
# 两种模式都支持 20 格 xy_prompts 角色人设
export USE_FUNCTION_CALLING=1

# ============================================================
#  外部工具地址 (4 个)
#  - 留空或注释 → 该工具走降级（空结果/LLM 兜底/报 not_connected）
#  - 填真实地址 → 前端一次调 /api/chat 会整合所有工具输出到一个返回里
# ============================================================

# 工具1: 脸型识别（留空 → 用户可手动说脸型，或后续接入真实服务）
# export FACE_API_URL="http://your-face-api/analyze"

# 工具2: 发型推荐（留空 → 走本地 SQL 推荐器，数据库已有 2655 条发型）
# export RECOMMEND_API_URL=""

# 工具3: 生图 → ComfyUI 官方协议
export COMFYUI_URL="https://comfyui.geekpie.tech"

# 工具4: 理发师步骤
# export STYLIST_API_URL="http://your-host/stylist/steps"

# ============================================================
#  启动参数
# ============================================================
export PORT="${PORT:-7860}"

# ---- API Key sanity check（防 latin-1 崩溃）----
python3 -c "
import os, sys
k = os.environ.get('LLM_API_KEY', '')
if not k or k == 'sk-':
    print('❌ LLM_API_KEY 未填写，请编辑 agent.sh 第 20 行')
    sys.exit(1)
if not k.isascii():
    print('❌ LLM_API_KEY 含非 ASCII 字符（中文/全角/零宽字符）')
    print('   请在 agent.sh 里手动重新敲一遍，不要复制粘贴')
    sys.exit(1)
print(f'✅ API Key 校验通过 (长度 {len(k)})')
print(f'   BASE   = {os.environ.get(\"LLM_API_BASE\")}')
print(f'   MODEL  = {os.environ.get(\"LLM_API_MODEL\")}')
fc = os.environ.get('USE_FUNCTION_CALLING', '1')
print(f'   范式   = {\"function calling (LLM 自主调工具,慢)\" if fc == \"1\" else \"state machine (硬编码 if-else,快)\"}')
" || exit 1

echo "============================================================"
echo "  HairSync AI Agent"
echo "  Time:   $(date)"
echo "  Port:   ${PORT}"
echo "  前端:   http://localhost:${PORT}"
echo "  API:    http://localhost:${PORT}/docs"
echo "============================================================"

python3 agent.py
