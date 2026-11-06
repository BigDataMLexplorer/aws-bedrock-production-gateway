# AWS Bedrock Production AI Gateway

Independent portfolio project focused on the reliability layer around production LLM applications rather than another chatbot demo.

**FastAPI → policy router → resilient Bedrock Converse adapter → structured output validation → telemetry / cost accounting**

The public demo uses a deterministic fake provider so tests and benchmarks run without AWS credentials or paid inference. The repository also contains a real `boto3` Bedrock Runtime `Converse` adapter that can be enabled with environment variables.

## What this demonstrates

- FastAPI production backend patterns
- Amazon Bedrock Runtime / Converse integration through `boto3`
- model routing by task complexity and tenant policy
- bounded retries with exponential backoff
- fallback model routing
- per-model circuit breaker
- Pydantic structured-output validation
- Bedrock token / latency metadata normalization
- configurable cost estimation from token usage
- optional Bedrock Guardrail configuration
- tool configuration passthrough for Converse tool use
- pre-flight tenant/request cost budgets and model allow-lists
- OpenTelemetry spans without logging raw prompts
- deterministic fault-injection benchmark
- Docker + GitHub Actions CI

## Fault-injection benchmark

The benchmark compares:

1. a naive one-shot provider call
2. the resilient gateway

against deterministic failure scenarios including throttling, timeouts, primary-provider outages and malformed structured output.

The benchmark measures backend resilience only. It does **not** claim Bedrock model quality or production AWS SLA performance.

### Measured result

On 120 deterministic synthetic requests:

| Metric | Naive one-shot | Resilient gateway |
| --- | ---: | ---: |
| Valid response rate | **66.7%** | **100%** |
| Malformed structured outputs returned | **5** | **0** |

Additional gateway measurements:

- retryable fault cases recovered: **35 / 35**
- fallback rate: **12.5%**
- mean provider attempts: **1.50 / request**
- test suite: **13 passing tests**

These figures are deliberately labeled as a synthetic fault-injection benchmark. They show how the gateway behaves when dependencies fail; they are not AWS service availability measurements.

Run it with:

```bash
pip install -e '.[dev]'
pytest -q
PYTHONPATH=src python scripts/run_fault_benchmark.py
PYTHONPATH=src python scripts/plot_benchmark.py
```

## Run the demo

```bash
PYTHONPATH=src uvicorn app.main:app --reload
```

Open `http://localhost:8000/demo`.

## Real Bedrock configuration

Set `AI_PROVIDER=bedrock`, provide AWS credentials using the normal AWS SDK credential chain, and set both model IDs / inference profiles in `.env` or your deployment environment.

No AWS credentials, secrets, model IDs or account-specific configuration are committed to this repository.
