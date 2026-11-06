from __future__ import annotations

import os
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, ConnectTimeoutError, ReadTimeoutError

from app.exceptions import ProviderThrottle, ProviderTimeout, ProviderUnavailable
from app.models import InferenceRequest, ProviderResult, Usage


class BedrockConverseProvider:
    """Thin adapter around Amazon Bedrock Runtime Converse.

    Real credentials are resolved by the standard AWS SDK credential chain.
    """

    def __init__(self, region: str | None = None):
        region = region or os.getenv("AWS_REGION", "eu-central-1")
        config = Config(retries={"mode": "standard", "total_max_attempts": 3})
        self.client = boto3.client("bedrock-runtime", region_name=region, config=config)

    def generate(self, request: InferenceRequest, model_id: str) -> ProviderResult:
        kwargs: dict[str, Any] = {
            "modelId": model_id,
            "messages": [{"role": "user", "content": [{"text": request.prompt}]}],
            "inferenceConfig": {"maxTokens": request.max_output_tokens},
        }
        if request.tool_config:
            kwargs["toolConfig"] = request.tool_config

        guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID")
        guardrail_version = os.getenv("BEDROCK_GUARDRAIL_VERSION")
        if guardrail_id and guardrail_version:
            kwargs["guardrailConfig"] = {
                "guardrailIdentifier": guardrail_id,
                "guardrailVersion": guardrail_version,
                "trace": "enabled",
            }

        try:
            response = self.client.converse(**kwargs)
        except (ReadTimeoutError, ConnectTimeoutError) as exc:
            raise ProviderTimeout(str(exc)) from exc
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"ThrottlingException", "TooManyRequestsException"}:
                raise ProviderThrottle(code) from exc
            if code in {
                "ServiceUnavailableException",
                "InternalServerException",
                "ModelNotReadyException",
                "ModelTimeoutException",
            }:
                raise ProviderUnavailable(code) from exc
            raise
        except BotoCoreError as exc:
            raise ProviderUnavailable(str(exc)) from exc

        content = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(block.get("text", "") for block in content if isinstance(block, dict))
        usage_raw = response.get("usage", {})
        metrics = response.get("metrics", {})
        return ProviderResult(
            text=text,
            model_id=model_id,
            usage=Usage(
                input_tokens=int(usage_raw.get("inputTokens", 0)),
                output_tokens=int(usage_raw.get("outputTokens", 0)),
                total_tokens=int(usage_raw.get("totalTokens", 0)),
            ),
            latency_ms=int(metrics.get("latencyMs", 0)),
            stop_reason=str(response.get("stopReason", "end_turn")),
        )
