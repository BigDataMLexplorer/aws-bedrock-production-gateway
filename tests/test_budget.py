import pytest
from app.costs import Pricing
from app.models import InferenceRequest
from app.providers.fake import DeterministicFakeProvider
from app.resilience import CircuitBreaker
from app.routing import ModelRouter, TenantPolicy
from app.service import GatewayConfig, ResilientGateway


def test_preflight_budget_blocks_expensive_request_before_provider_call():
    p=DeterministicFakeProvider()
    g=ResilientGateway(
        p, ModelRouter("fast","strong"), CircuitBreaker(),
        {"fast":Pricing(10,20),"strong":Pricing(20,40)},
        GatewayConfig(max_attempts=1), sleep_fn=lambda _:None,
    )
    req=InferenceRequest(tenant_id="budget",prompt="x"*4000,max_output_tokens=4096,budget_usd=0.01)
    with pytest.raises(PermissionError,match="Projected request cost"):
        g.invoke(req,TenantPolicy())
    assert sum(p.calls.values())==0
