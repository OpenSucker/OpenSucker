"""Sucker Smart Trading Matrix Agent (X×Y).

A 5×4 matrix of role-conditioned LLM agents wired together with LangGraph.
The original implementation lived in a single 400-line file (agent.py); here
it is split into:

- schemas.py        Typed state, request/response models
- intent.py         Persona-override + LLM Router + keyword fallback
- prompts.py        20-cell role prompts and helpers
- runtime.py        LanguageModel + SessionManager + intent api config
- skills_loader.py  Three-layer skill stacking (cell / persona / vibe)
- graph.py          LangGraph nodes & workflow
- service.py        High-level orchestrator that the FastAPI endpoint uses
"""

from .schemas import (
    AgentResponse,
    ChatRequest,
    SuckerState,
    UserEntity,
)
from .service import MatrixAgentService, get_matrix_service

__all__ = [
    "AgentResponse",
    "ChatRequest",
    "MatrixAgentService",
    "SuckerState",
    "UserEntity",
    "get_matrix_service",
]
