from __future__ import annotations

from dataclasses import dataclass

from app.models import Usage


@dataclass(frozen=True)
class Pricing:
    input_per_million: float
    output_per_million: float


def estimate_cost(usage: Usage, pricing: Pricing) -> float:
    return round(
        usage.input_tokens / 1_000_000 * pricing.input_per_million
        + usage.output_tokens / 1_000_000 * pricing.output_per_million,
        8,
    )
