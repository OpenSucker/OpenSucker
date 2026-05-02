"""Minimal MatrixAgentService stub.

This file exists so ``app.domains.matrix_agent.__init__`` can import it
without a ModuleNotFoundError. The real Matrix Agent runtime currently
lives in ``backend/agent.py`` (the single-file LangGraph implementation
that runs on port 7860). When the FastAPI ``/api/v1/matrix/chat``
endpoint is wired up in a future PR, replace this stub with a real
service that adapts ``backend/agent.py``'s graph to the v1 API contract.

The stub is intentionally non-functional: it raises ``NotImplementedError``
so accidental usage fails loudly rather than silently producing garbage.
"""

from __future__ import annotations

from .schemas import AgentResponse, ChatRequest


class MatrixAgentService:
    """Placeholder for the layered Matrix Agent service.

    See module docstring for the migration plan.
    """

    def chat(self, request: ChatRequest) -> AgentResponse:  # pragma: no cover
        raise NotImplementedError(
            "MatrixAgentService is not yet implemented in the FastAPI "
            "layer. Use the single-file Agent at backend/agent.py "
            "(POST /api/chat) until the v1 endpoint is wired."
        )


_singleton: MatrixAgentService | None = None


def get_matrix_service() -> MatrixAgentService:
    """Return a process-wide MatrixAgentService instance (lazy)."""
    global _singleton
    if _singleton is None:
        _singleton = MatrixAgentService()
    return _singleton
