import os

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import OpenAI


class GoGoAgentHandler(OpenAICompletionsHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.is_fc_model = False

    def _build_client_kwargs(self):
        """Override to use GoGoAgent API settings instead of OpenAI."""
        kwargs = {}

        # Use GoGoAgent API key
        api_key = os.getenv("GOGOAGENT_API_KEY")
        if api_key:
            kwargs["api_key"] = api_key

        # Use GoGoAgent base URL
        kwargs["base_url"] = "https://api.gogoagent.ai"

        return kwargs
