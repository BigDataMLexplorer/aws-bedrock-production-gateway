from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from app.costs import Pricing
from app.models import GatewayResponse, InferenceRequest
from app.providers.bedrock import BedrockConverseProvider
from app.providers.fake import DeterministicFakeProvider
from app.resilience import CircuitBreaker
from app.routing import ModelRouter, TenantPolicy
from app.service import GatewayConfig, ResilientGateway

router = APIRouter()

FAST = os.getenv("BEDROCK_PRIMARY_MODEL_ID") or "demo-fast"
STRONG = os.getenv("BEDROCK_FALLBACK_MODEL_ID") or "demo-strong"
provider = BedrockConverseProvider() if os.getenv("AI_PROVIDER") == "bedrock" else DeterministicFakeProvider()
pricing = {
    FAST: Pricing(
        float(os.getenv("BEDROCK_PRIMARY_INPUT_PRICE_PER_MILLION", "0")),
        float(os.getenv("BEDROCK_PRIMARY_OUTPUT_PRICE_PER_MILLION", "0")),
    ),
    STRONG: Pricing(
        float(os.getenv("BEDROCK_FALLBACK_INPUT_PRICE_PER_MILLION", "0")),
        float(os.getenv("BEDROCK_FALLBACK_OUTPUT_PRICE_PER_MILLION", "0")),
    ),
}
gateway = ResilientGateway(
    provider=provider,
    router=ModelRouter(FAST, STRONG),
    circuit=CircuitBreaker(
        failure_threshold=int(os.getenv("GATEWAY_CIRCUIT_FAILURE_THRESHOLD", "3")),
        cooldown_seconds=float(os.getenv("GATEWAY_CIRCUIT_COOLDOWN_SECONDS", "20")),
    ),
    pricing_by_model=pricing,
    config=GatewayConfig(max_attempts=int(os.getenv("GATEWAY_MAX_ATTEMPTS", "3"))),
)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": os.getenv("AI_PROVIDER", "fake")}


@router.post("/v1/inference", response_model=GatewayResponse)
def inference(request: InferenceRequest) -> GatewayResponse:
    try:
        policy = TenantPolicy(allowed_models=frozenset({FAST, STRONG}))
        return gateway.invoke(request, policy)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
