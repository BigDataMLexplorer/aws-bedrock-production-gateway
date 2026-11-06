from __future__ import annotations

import json
from pathlib import Path

from app.costs import Pricing
from app.exceptions import ProviderError
from app.models import InferenceRequest, TaskType, TriageOutput
from app.providers.fake import DeterministicFakeProvider
from app.resilience import CircuitBreaker
from app.routing import ModelRouter, TenantPolicy
from app.service import GatewayConfig, ResilientGateway

ROOT = Path(__file__).resolve().parents[1]
FAST = "demo-fast"
STRONG = "demo-strong"


def make_cases() -> list[dict]:
    cases=[]
    specs=[
        ("clean",80),
        ("throttle_once",15),
        ("timeout_once",10),
        ("primary_unavailable",10),
        ("malformed_structured",5),
    ]
    i=0
    for kind,count in specs:
        for _ in range(count):
            cases.append({"id":f"case-{i:03d}","kind":kind})
            i+=1
    return cases


def configure(provider: DeterministicFakeProvider, case: dict) -> InferenceRequest:
    case_id=case["id"]
    kind=case["kind"]
    task=TaskType.structured if kind=="malformed_structured" else TaskType.chat
    if kind=="throttle_once":
        provider.set_plan(case_id,FAST,["throttle","success"])
    elif kind=="timeout_once":
        provider.set_plan(case_id,FAST,["timeout","success"])
    elif kind=="primary_unavailable":
        provider.set_plan(case_id,FAST,["unavailable","unavailable","unavailable"])
        provider.set_plan(case_id,STRONG,["success"])
    elif kind=="malformed_structured":
        provider.set_plan(case_id,STRONG,["malformed"])
        provider.set_plan(case_id,FAST,["success"])
    return InferenceRequest(tenant_id=case_id,prompt="Synthetic benchmark request",task_type=task)


def naive_call(provider: DeterministicFakeProvider, request: InferenceRequest, model: str) -> tuple[bool,bool]:
    try:
        result=provider.generate(request,model)
        if request.task_type==TaskType.structured:
            try:
                TriageOutput.model_validate_json(result.text)
            except Exception:
                return False, True
        return True, False
    except ProviderError:
        return False, False


def main() -> None:
    cases=make_cases()
    rows=[]
    naive_success=0
    naive_malformed=0
    resilient_success=0
    resilient_attempts=0
    fallback_count=0
    recovered_retryable=0

    for case in cases:
        naive_provider=DeterministicFakeProvider()
        req=configure(naive_provider,case)
        naive_model=STRONG if req.task_type==TaskType.structured else FAST
        ok,malformed=naive_call(naive_provider,req,naive_model)
        naive_success+=int(ok)
        naive_malformed+=int(malformed)

        provider=DeterministicFakeProvider()
        req=configure(provider,case)
        gateway=ResilientGateway(
            provider=provider,
            router=ModelRouter(FAST,STRONG),
            circuit=CircuitBreaker(failure_threshold=3,cooldown_seconds=0),
            pricing_by_model={FAST:Pricing(0,0),STRONG:Pricing(0,0)},
            config=GatewayConfig(max_attempts=3,backoff_base_seconds=0),
            sleep_fn=lambda _:None,
        )
        try:
            response=gateway.invoke(req,TenantPolicy(allowed_models=frozenset({FAST,STRONG})))
            success=True
            resilient_success+=1
            resilient_attempts+=response.attempts
            fallback_count+=int(response.fallback_used)
            recovered_retryable+=int(case["kind"] in {"throttle_once","timeout_once","primary_unavailable"})
        except Exception:
            response=None
            success=False
        rows.append({
            **case,
            "naive_success":ok,
            "naive_malformed":malformed,
            "resilient_success":success,
            "resilient_attempts":response.attempts if response else None,
            "fallback_used":response.fallback_used if response else None,
            "model_id":response.model_id if response else None,
        })

    summary={
        "cases":len(cases),
        "naive_valid_success_rate":round(naive_success/len(cases),4),
        "resilient_valid_success_rate":round(resilient_success/len(cases),4),
        "naive_malformed_structured_outputs":naive_malformed,
        "resilient_malformed_structured_outputs":sum(
            1 for r in rows
            if r["resilient_success"]
            and r["kind"]=="malformed_structured"
            and r["model_id"]==STRONG
        ),
        "fallback_rate":round(fallback_count/len(cases),4),
        "mean_provider_attempts":round(resilient_attempts/len(cases),3),
        "retryable_faults_recovered":recovered_retryable,
        "retryable_fault_cases":35,
    }
    out=ROOT/"artifacts"/"fault_benchmark.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary":summary,"cases":rows},indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
