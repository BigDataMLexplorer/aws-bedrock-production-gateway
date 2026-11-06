from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    chat = "chat"
    structured = "structured"
    agent = "agent"


class InferenceRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=40_000)
    task_type: TaskType = TaskType.chat
    max_output_tokens: int = Field(default=512, ge=16, le=4096)
    budget_usd: float | None = Field(default=None, gt=0)
    tool_config: dict[str, Any] | None = None


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ProviderResult(BaseModel):
    text: str
    model_id: str
    usage: Usage = Field(default_factory=Usage)
    latency_ms: int = 0
    stop_reason: str = "end_turn"


class GatewayResponse(BaseModel):
    text: str
    model_id: str
    route_reason: str
    attempts: int
    fallback_used: bool
    circuit_opened: bool = False
    usage: Usage
    latency_ms: int
    estimated_cost_usd: float
    structured_valid: bool | None = None


class TriageOutput(BaseModel):
    category: str
    priority: int = Field(ge=1, le=5)
    summary: str
