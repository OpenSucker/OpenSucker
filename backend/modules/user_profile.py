"""
用户画像与会话管理模块 v3 — Sucker 金融版
管理用户的投资认知等级、风险偏好、持仓历史、交易习惯
"""
import json
import time
import uuid
from typing import Dict, List, Optional


class UserSession:
    """StockSync 智能交易矩阵单人会话"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.updated_at = time.time()

        # 对话历史
        self.history: List[Dict[str, str]] = []

        # 核心金融画像 (Financial Profile)
        self.cognitive_level: int = 1  # Lv.1-Lv.5
        self.risk_preference: str = "moderate"  # conservative, moderate, aggressive
        self.investment_style: str = "growth"   # value, growth, speculative
        self.capital_size: str = "medium"       # small, medium, large
        
        # 持仓与活跃度 (Holdings & Activity)
        self.holdings: List[Dict] = []  # [{"symbol": "NVDA", "qty": 10, "price": 400}]
        self.last_trade: Optional[Dict] = None
        self.watchlist: List[str] = []
        self.historical_lessons: List[str] = [] # 用户历史大坑/大赚复盘 RAG
        
        # 活跃分析与推荐
        self.active_recommendations: List[Dict] = []
        self.selected_symbol: Optional[str] = None
        self.confirmed: bool = False

        # 详细画像字段（用于持久化）
        self.profile: Dict = {
            "risk_tolerance": "moderate",
            "experience_years": 0,
            "preferred_sectors": [],  # 科技, 能源, 消费等
            "forbidden_stocks": [],   # 不碰的黑名单
            "trading_frequency": "weekly", # daily, weekly, monthly
            "knowledge_tags": [],     # 已掌握的知识点
        }

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self.updated_at = time.time()

    def get_context(self, max_turns: int = 8) -> List[Dict[str, str]]:
        """获取最近的对话历史"""
        return self.history[-max_turns * 2:]

    def update_profile_from_message(self, message: str):
        """从用户消息中自动提取金融画像信息 (简单关键词提取)"""
        msg = message.lower()

        # 风险偏好
        if any(w in msg for w in ["保守", "稳健", "怕亏"]):
            self.risk_preference = "conservative"
        elif any(w in msg for w in ["激进", "重仓", "杠杆", "翻倍"]):
            self.risk_preference = "aggressive"

        # 认知层级（初步判定）
        if any(w in msg for w in ["什么是", "小白", "刚开户", "怎么买"]):
            self.cognitive_level = 1
        elif any(w in msg for w in ["k线", "指标", "macd", "rsi"]):
            self.cognitive_level = max(self.cognitive_level, 2)
        elif any(w in msg for w in ["策略", "回测", "因式", "凯利公式"]):
            self.cognitive_level = max(self.cognitive_level, 3)
        elif any(w in msg for w in ["接口", "api", "python", "量化"]):
            self.cognitive_level = max(self.cognitive_level, 5)

        # 行业偏好
        sectors = {"科技": ["ai", "半导体", "科技"], "能源": ["石油", "新能源", "光伏"], "消费": ["白酒", "消费", "买菜"]}
        for cn, keywords in sectors.items():
            if any(k in msg for k in keywords):
                if cn not in self.profile["preferred_sectors"]:
                    self.profile["preferred_sectors"].append(cn)

    def to_dict(self) -> Dict:
        """导出会话状态（给前端展示用）"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "cognitive_level": self.cognitive_level,
            "risk_preference": self.risk_preference,
            "holdings": self.holdings,
            "profile": self.profile,
            "selected_symbol": self.selected_symbol,
            "confirmed": self.confirmed,
            "history_length": len(self.history),
            "history": self.history[-20:],
        }


class SessionManager:
    """会...话管理器"""

    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> UserSession:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        new_id = session_id or str(uuid.uuid4())[:8]
        session = UserSession(new_id)
        self.sessions[new_id] = session
        return session

    def get(self, session_id: str) -> Optional[UserSession]:
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict]:
        return [
            {"session_id": s.session_id, "created_at": s.created_at,
             "cog_level": s.cognitive_level, "history_length": len(s.history)}
            for s in self.sessions.values()
        ]
