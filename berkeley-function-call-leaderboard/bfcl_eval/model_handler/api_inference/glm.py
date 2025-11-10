import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
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
        # Override client with custom timeout
        self.client = OpenAI(
            api_key=self._get_api_key(),
            base_url=self._get_base_url(),
            timeout=httpx.Timeout(timeout=300.0, connect=8.0),
        )

    def _get_api_key(self):
        """Use GLM API key instead of OpenAI API key."""
        return os.getenv("GLM_API_KEY")

    def _get_base_url(self):
        """Use GLM base URL instead of OpenAI base URL."""
        return "https://api.z.ai/api/coding/paas/v4/"
