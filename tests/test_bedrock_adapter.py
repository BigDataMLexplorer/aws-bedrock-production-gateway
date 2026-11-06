from app.models import InferenceRequest
from app.providers.bedrock import BedrockConverseProvider


class StubClient:
    def __init__(self): self.kwargs=None
    def converse(self, **kwargs):
        self.kwargs=kwargs
        return {
            "output":{"message":{"role":"assistant","content":[{"text":"hello"}]}},
            "stopReason":"end_turn",
            "usage":{"inputTokens":12,"outputTokens":4,"totalTokens":16},
            "metrics":{"latencyMs":321},
        }


def test_bedrock_converse_adapter_normalizes_usage_and_tool_config():
    provider=object.__new__(BedrockConverseProvider)
    provider.client=StubClient()
    req=InferenceRequest(
        tenant_id="t",prompt="hello",
        tool_config={"tools":[{"toolSpec":{"name":"status","inputSchema":{"json":{"type":"object"}}}}]},
    )
    result=provider.generate(req,"model-x")
    assert result.text=="hello"
    assert result.usage.total_tokens==16
    assert result.latency_ms==321
    assert provider.client.kwargs["modelId"]=="model-x"
    assert "toolConfig" in provider.client.kwargs
