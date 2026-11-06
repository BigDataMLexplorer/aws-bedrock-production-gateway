from __future__ import annotations

from dataclasses import dataclass, field

from app.models import InferenceRequest, TaskType


@dataclass(frozen=True)
class TenantPolicy:
    allowed_models: frozenset[str] = field(default_factory=frozenset)
    force_economy: bool = False
    max_request_budget_usd: float | None = None


@dataclass(frozen=True)
class RouteDecision:
    primary_model: str
    fallback_model: str
    reason: str


class ModelRouter:
    def __init__(self, economy_model: str, capable_model: str):
        self.economy_model = economy_model
        self.capable_model = capable_model

    def route(self, request: InferenceRequest, policy: TenantPolicy) -> RouteDecision:
        complex_task = (
            request.task_type in {TaskType.structured, TaskType.agent}
            or len(request.prompt) > 2500
        )
        primary = self.economy_model if policy.force_economy or not complex_task else self.capable_model
        fallback = self.capable_model if primary == self.economy_model else self.economy_model

        if policy.allowed_models:
            if primary not in policy.allowed_models:
                if fallback in policy.allowed_models:
                    primary, fallback = fallback, primary
                else:
                    raise PermissionError("Tenant policy does not allow either configured model")
            if fallback not in policy.allowed_models:
                fallback = primary

        reason = "economy_route" if primary == self.economy_model else "capability_route"
        return RouteDecision(primary_model=primary, fallback_model=fallback, reason=reason)
