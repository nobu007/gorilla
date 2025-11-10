import os
from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import OpenAI


class KimiHandler(OpenAICompletionsHandler):
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
        """Override to use Kimi API settings instead of OpenAI."""
        kwargs = {}

        # Use Kimi API key
        api_key = os.getenv("KIMI_API_KEY")
        if api_key:
            kwargs["api_key"] = api_key

        # Use Kimi base URL
        # If API Key is from US platform, use the above URL
        # If API Key is from China platform, use the below URL
        kwargs["base_url"] = "https://api.moonshot.ai/v1"

        return kwargs

    def _get_api_key(self):
        """Use Kimi API key instead of OpenAI API key."""
        return os.getenv("KIMI_API_KEY")

    def _get_base_url(self):
        """Use Kimi base URL instead of OpenAI base URL."""
        return "https://api.moonshot.ai/v1"
