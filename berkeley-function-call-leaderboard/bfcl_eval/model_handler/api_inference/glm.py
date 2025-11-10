import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from bfcl_eval.constants.enums import ModelStyle
from openai import OpenAI
import httpx


class GLMAPIHandler(OpenAICompletionsHandler):
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
        """Override to use GLM API settings instead of OpenAI."""
        kwargs = {}

        # Use GLM API key
        api_key = self._get_api_key()
        if api_key:
            kwargs["api_key"] = api_key

        # Use GLM base URL
        base_url = self._get_base_url()
        if base_url:
            kwargs["base_url"] = base_url

        # Set custom timeout
        kwargs["timeout"] = httpx.Timeout(timeout=300.0, connect=8.0)

        return kwargs

    def _get_api_key(self):
        """Use GLM API key instead of OpenAI API key."""
        return os.getenv("GLM_API_KEY")

    def _get_base_url(self):
        """Use GLM base URL instead of OpenAI base URL."""
        return "https://api.z.ai/api/coding/paas/v4/"
