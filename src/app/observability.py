from opentelemetry import trace

tracer = trace.get_tracer("aws-bedrock-production-gateway")
