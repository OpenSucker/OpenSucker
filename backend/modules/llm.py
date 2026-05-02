"""
语言模型模块 v3 — Sucker Smart Trading Edition
基于 OpenAI 官方 SDK 构建，确保最佳的 API 兼容性与稳定性。
"""
import json
import os
import time
from typing import Dict, List, Optional, Any
from openai import OpenAI


class LanguageModel:
    def __init__(self, model_path: str = None, lora_path: str = None, api_config: Dict = None):
        self.mode = "mock"  # mock / local / api
        self.api_config = api_config
        self.client: Optional[OpenAI] = None
        self.model_loaded = False

        # === 1. 检查 API 模式 (优先级最高，因为用户使用的是 API) ===
        if api_config and api_config.get("api_key"):
            try:
                base_url = api_config.get("base_url", "")
                if base_url and not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
                    base_url = base_url.rstrip("/") + "/v1"
                
                self.client = OpenAI(
                    api_key=api_config["api_key"],
                    base_url=base_url
                )
                self.mode = "api"
                self.model_loaded = True
                print(f"✅ 语言模型就绪（官方 SDK 模式: {api_config.get('model', 'unknown')}）")
            except Exception as e:
                print(f"❌ 初始化 OpenAI 客户端失败: {e}")

        # === 2. 兜底模拟模式 ===
        if self.mode == "mock":
            print("⚠️ 语言模型使用模拟模式")

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        tool_choice: str = "auto",
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> Dict:
        """
        使用官方 SDK 进行工具调用 (Function Calling)
        """
        if self.mode != "api" or not self.client:
            return {"content": "API 模式未就绪", "tool_calls": [], "finish_reason": "error"}

        try:
            response = self.client.chat.completions.create(
                model=self.api_config["model"],
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 鲁棒性检查：确保返回的是对象
            if isinstance(response, str):
                return {"content": "", "tool_calls": [], "finish_reason": "error", "error": f"API 返回了字符串而非对象: {response[:100]}"}

            msg = response.choices[0].message
            return {
                "content": msg.content or "",
                "tool_calls": msg.tool_calls or [],
                "finish_reason": response.choices[0].finish_reason,
                "raw": response
            }
        except Exception as e:
            return {"content": "", "tool_calls": [], "finish_reason": "error", "error": str(e)}

    def generate(self, messages: List[Dict], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        普通文本生成
        """
        if self.mode != "api" or not self.client:
            return "API 模式未就绪"

        try:
            response = self.client.chat.completions.create(
                model=self.api_config["model"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            if isinstance(response, str):
                return f"API 异常返回: {response}"
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"API 调用失败: {e}"

    def _build_system_prompt(self, session, mode: str) -> str:
        """构建金融分析师 system prompt"""
        return """你是一位专业的金融交易分析师，专注于 Sucker 智能交易矩阵。
你擅长通过情绪、技术面、策略、宏观和博弈五个维度为用户提供决策支持。
要求：专业、理性、客观，多引用凯利公式等量化工具。"""
