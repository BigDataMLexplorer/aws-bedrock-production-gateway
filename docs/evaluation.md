# Fault-injection evaluation

The benchmark is synthetic and deterministic. It tests gateway behavior, not foundation-model quality and not AWS SLA performance.

120 requests are distributed across:

- 80 clean calls
- 15 calls throttled on the first attempt
- 10 calls timing out on the first attempt
- 10 requests where the primary model is unavailable for all configured attempts
- 5 structured-output requests where the primary returns malformed JSON

The naive baseline performs one provider call and returns whatever it receives. The resilient gateway has bounded retries, model fallback and Pydantic structured-output validation.
