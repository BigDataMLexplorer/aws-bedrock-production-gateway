from __future__ import annotations

import json
import time
from dataclasses import dataclass

from pydantic import ValidationError

from app.costs import Pricing, estimate_cost
from app.exceptions import ProviderError, ProviderMalformed
from app.models import GatewayResponse, InferenceRequest, TaskType, TriageOutput, Usage
from app.observability import tracer
from app.providers.base import InferenceProvider
from app.resilience import CircuitBreaker
from app.routing import ModelRouter, TenantPolicy


@dataclass(frozen=True)
class GatewayConfig:
    max_attempts: int = 3
    backoff_base_seconds: float = 0.01


class ResilientGateway:
    def __init__(
        self,
        provider: InferenceProvider,
        router: ModelRouter,
        circuit: CircuitBreaker,
        pricing_by_model: dict[str, Pricing],
        config: GatewayConfig | None = None,
        sleep_fn=time.sleep,
    ):
        self.provider = provider
        self.router = router
        self.circuit = circuit
        self.pricing_by_model = pricing_by_model
        self.config = config or GatewayConfig()
        self.sleep_fn = sleep_fn

    @staticmethod
    def _validate_structured(request: InferenceRequest, text: str) -> bool:
        if request.task_type != TaskType.structured:
            return True
        try:
            payload = json.loads(text)
            TriageOutput.model_validate(payload)
            return True
        except (json.JSONDecodeError, ValidationError):
            return False

    def _call_with_retries(self, request: InferenceRequest, model_id: str) -> tuple[object, int, bool]:
        attempts = 0
        opened = False
        last_error: Exception | None = None
        for attempt in range(1, self.config.max_attempts + 1):
            attempts = attempt
            try:
                result = self.provider.generate(request, model_id)
                if not self._validate_structured(request, result.text):
                    self.circuit.record_failure(model_id)
                    raise ProviderMalformed("structured output failed schema validation")
                self.circuit.record_success(model_id)
                return result, attempts, opened
            except ProviderError as exc:
                last_error = exc
                opened = self.circuit.record_failure(model_id) or opened
                if not exc.retryable or attempt >= self.config.max_attempts:
                    break
                self.sleep_fn(self.config.backoff_base_seconds * (2 ** (attempt - 1)))
        assert last_error is not None
        setattr(last_error, "attempts", attempts)
        setattr(last_error, "circuit_opened", opened)
        raise last_error

    def invoke(self, request: InferenceRequest, policy: TenantPolicy | None = None) -> GatewayResponse:
        policy = policy or TenantPolicy()
        route = self.router.route(request, policy)
        budget = request.budget_usd
        policy_budget = policy.max_request_budget_usd
        effective_budget = min(x for x in [budget, policy_budget] if x is not None) if any(x is not None for x in [budget, policy_budget]) else None
        if effective_budget is not None:
            approx_input_tokens = max(1, len(request.prompt) // 4)
            candidate_models = {route.primary_model, route.fallback_model}
            worst_case = 0.0
            for candidate in candidate_models:
                price = self.pricing_by_model.get(candidate, Pricing(0, 0))
                projected = estimate_cost(
                    Usage(
                        input_tokens=approx_input_tokens,
                        output_tokens=request.max_output_tokens,
                        total_tokens=approx_input_tokens + request.max_output_tokens,
                    ),
                    price,
                )
                worst_case = max(worst_case, projected)
            if worst_case > effective_budget:
                raise PermissionError("Projected request cost exceeds configured tenant/request budget")

        started = time.perf_counter()
        attempts = 0
        fallback_used = False
        circuit_opened = False

        with tracer.start_as_current_span("ai_gateway.invoke") as span:
            span.set_attribute("tenant.id", request.tenant_id)
            span.set_attribute("task.type", request.task_type.value)
            span.set_attribute("route.primary", route.primary_model)

            primary = route.primary_model
            fallback = route.fallback_model

            if self.circuit.is_open(primary):
                fallback_used = True
                model = fallback
                result, count, opened = self._call_with_retries(request, model)
                attempts += count
                circuit_opened = opened
            else:
                try:
                    result, count, opened = self._call_with_retries(request, primary)
                    attempts += count
                    circuit_opened = opened
                    model = primary
                except ProviderError as exc:
                    attempts += int(getattr(exc, "attempts", 0))
                    circuit_opened = circuit_opened or bool(getattr(exc, "circuit_opened", False))
                    if fallback == primary:
                        raise
                    fallback_used = True
                    result, count, opened = self._call_with_retries(request, fallback)
                    attempts += count
                    circuit_opened = circuit_opened or opened
                    model = fallback

            elapsed_ms = int((time.perf_counter() - started) * 1000)
            pricing = self.pricing_by_model.get(model, Pricing(0, 0))
            cost = estimate_cost(result.usage, pricing)
            span.set_attribute("route.model", model)
            span.set_attribute("route.fallback_used", fallback_used)
            span.set_attribute("provider.attempts", attempts)
            span.set_attribute("usage.input_tokens", result.usage.input_tokens)
            span.set_attribute("usage.output_tokens", result.usage.output_tokens)
            span.set_attribute("estimated_cost_usd", cost)

            return GatewayResponse(
                text=result.text,
                model_id=model,
                route_reason=route.reason,
                attempts=attempts,
                fallback_used=fallback_used,
                circuit_opened=circuit_opened,
                usage=result.usage,
                latency_ms=result.latency_ms or elapsed_ms,
                estimated_cost_usd=cost,
                structured_valid=self._validate_structured(request, result.text)
                if request.task_type == TaskType.structured
                else None,
            )
