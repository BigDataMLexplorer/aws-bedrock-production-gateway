# Evaluation results

## Scope

This is a deterministic fault-injection benchmark of the application gateway. It does not call a live foundation model and does not measure Amazon Bedrock availability, model accuracy or real cloud latency.

## Dataset

120 synthetic requests:

- 80 clean
- 15 first-attempt throttles
- 10 first-attempt timeouts
- 10 primary-model outage cases
- 5 malformed structured-output cases

## Results

| Metric | Result |
| --- | ---: |
| Naive one-shot valid response rate | 66.67% |
| Resilient gateway valid response rate | 100% |
| Naive malformed structured outputs returned | 5 |
| Resilient malformed structured outputs returned | 0 |
| Retryable fault cases recovered | 35 / 35 |
| Fallback rate | 12.5% |
| Mean provider attempts | 1.50 |

## Interpretation

A single LLM API call is not a production reliability strategy. Bounded retry behavior recovers transient throttles/timeouts; fallback routing recovers primary-model outages; schema validation prevents malformed structured output from escaping into downstream application logic. The trade-off is additional provider calls, which is why token/cost measurement and explicit retry limits belong in the same gateway.
