from app.costs import Pricing
from app.models import InferenceRequest, TaskType
from app.providers.fake import DeterministicFakeProvider
from app.resilience import CircuitBreaker
from app.routing import ModelRouter, TenantPolicy
from app.service import GatewayConfig, ResilientGateway


def gateway(provider):
    return ResilientGateway(provider,ModelRouter("fast","strong"),CircuitBreaker(3,0),{"fast":Pricing(0,0),"strong":Pricing(0,0)},GatewayConfig(3,0),sleep_fn=lambda _:None)


def test_retry_recovers_throttle():
    p=DeterministicFakeProvider();p.set_plan("t","fast",["throttle","success"])
    r=gateway(p).invoke(InferenceRequest(tenant_id="t",prompt="x"),TenantPolicy())
    assert r.attempts==2 and not r.fallback_used


def test_fallback_after_primary_outage():
    p=DeterministicFakeProvider();p.set_plan("t","fast",["unavailable"]*3);p.set_plan("t","strong",["success"])
    r=gateway(p).invoke(InferenceRequest(tenant_id="t",prompt="x"),TenantPolicy())
    assert r.fallback_used and r.model_id=="strong" and r.attempts==4


def test_malformed_structured_output_uses_fallback():
    p=DeterministicFakeProvider();p.set_plan("t","strong",["malformed"]);p.set_plan("t","fast",["success"])
    r=gateway(p).invoke(InferenceRequest(tenant_id="t",prompt="x",task_type=TaskType.structured),TenantPolicy())
    assert r.fallback_used and r.structured_valid is True
