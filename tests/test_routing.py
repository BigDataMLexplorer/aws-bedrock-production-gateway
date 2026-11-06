from app.models import InferenceRequest, TaskType
from app.routing import ModelRouter, TenantPolicy


def test_simple_chat_uses_economy():
    r=ModelRouter("fast","strong").route(InferenceRequest(tenant_id="t",prompt="hi"),TenantPolicy())
    assert r.primary_model=="fast"


def test_structured_uses_capable():
    r=ModelRouter("fast","strong").route(InferenceRequest(tenant_id="t",prompt="x",task_type=TaskType.structured),TenantPolicy())
    assert r.primary_model=="strong"


def test_allowlist_can_force_other_model():
    r=ModelRouter("fast","strong").route(InferenceRequest(tenant_id="t",prompt="hi"),TenantPolicy(allowed_models=frozenset({"strong"})))
    assert r.primary_model=="strong"
