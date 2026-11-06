from __future__ import annotations

from typing import Protocol

from app.models import InferenceRequest, ProviderResult


class InferenceProvider(Protocol):
    def generate(self, request: InferenceRequest, model_id: str) -> ProviderResult: ...
