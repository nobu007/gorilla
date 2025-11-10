import os
from typing import Any

from bfcl_eval.model_handler.api_inference.openai_completion import (
    OpenAICompletionsHandler,
)
from openai import OpenAI
from overrides import override


class GrokHandler(OpenAICompletionsHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)

    def _build_client_kwargs(self):
        """Override to use Grok API settings instead of OpenAI."""
        kwargs = {}

        # Use Grok API key
        api_key = os.getenv("GROK_API_KEY")
        if api_key:
            kwargs["api_key"] = api_key

        # Use Grok base URL
        kwargs["base_url"] = "https://api.x.ai/v1"

        return kwargs

    @override
    def _parse_query_response_prompting(self, api_response: Any) -> dict:
        response_data = super()._parse_query_response_prompting(api_response)
        self._add_reasoning_content_if_available_prompting(api_response, response_data)
        return response_data

    @override
    def _parse_query_response_FC(self, api_response: Any) -> dict:
        response_data = super()._parse_query_response_FC(api_response)
        self._add_reasoning_content_if_available_prompting(api_response, response_data)
        return response_data
