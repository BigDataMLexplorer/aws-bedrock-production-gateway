from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass

from app.exceptions import ProviderMalformed, ProviderThrottle, ProviderTimeout, ProviderUnavailable
from app.models import InferenceRequest, ProviderResult, TaskType, Usage


@dataclass(frozen=True)
class Fault:
    kind: str


class DeterministicFakeProvider:
    """Provider for repeatable tests, demo and benchmark without external API calls."""

    def __init__(self):
        self._plans: dict[tuple[str, str], deque[str]] = defaultdict(deque)
        self.calls: dict[tuple[str, str], int] = defaultdict(int)

    def set_plan(self, request_id: str, model_id: str, outcomes: list[str]) -> None:
        self._plans[(request_id, model_id)] = deque(outcomes)

    def _next(self, request_id: str, model_id: str) -> str:
        key = (request_id, model_id)
        self.calls[key] += 1
        return self._plans[key].popleft() if self._plans[key] else "success"

    def generate(self, request: InferenceRequest, model_id: str) -> ProviderResult:
        request_id = request.tenant_id
        outcome = self._next(request_id, model_id)
        if outcome == "throttle":
            raise ProviderThrottle("synthetic throttle")
        if outcome == "timeout":
            raise ProviderTimeout("synthetic timeout")
        if outcome == "unavailable":
            raise ProviderUnavailable("synthetic provider outage")
        if outcome == "malformed":
            return ProviderResult(
                text="{bad-json",
                model_id=model_id,
                usage=Usage(input_tokens=120, output_tokens=35, total_tokens=155),
                latency_ms=140,
            )

        if request.task_type == TaskType.structured:
            text = json.dumps({
                "category": "billing",
                "priority": 2,
                "summary": "Synthetic validated triage result",
            })
        else:
            text = "Synthetic successful response"
        return ProviderResult(
            text=text,
            model_id=model_id,
            usage=Usage(input_tokens=120, output_tokens=45, total_tokens=165),
            latency_ms=120 if "fast" in model_id else 210,
        )
