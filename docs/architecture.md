# Architecture

```mermaid
flowchart LR
    A[FastAPI request] --> B[Tenant policy + model router]
    B --> C[Retry / backoff / circuit breaker]
    C --> D[Bedrock Runtime Converse]
    D --> E[Structured output validation]
    E --> F[Usage + latency normalization]
    F --> G[Cost estimate + OpenTelemetry]
    C -->|primary unavailable| H[Fallback model]
    H --> E
```

The production boundary is intentionally the gateway layer, not the foundation model itself. The gateway decides which model is allowed, limits retries, rejects invalid structured output, normalizes Bedrock usage metadata and records operational telemetry without storing raw prompt text.
