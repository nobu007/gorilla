import os
from bfcl_eval.constants.enums import ModelStyle
from openai import OpenAI
from bfcl_eval.model_handler.api_inference.mining import MiningHandler

class DMCitoHandler(MiningHandler):
    def __init__(
        self,
        model_name,
        temperature,
        registry_name,
        is_fc_model,
        **kwargs,
    ) -> None:
        super().__init__(model_name, temperature, registry_name, is_fc_model, **kwargs)
        self.model_style = ModelStyle.OPENAI_COMPLETIONS

    def _build_client_kwargs(self):
        """Override to use DMCito API settings instead of OpenAI."""
        kwargs = {}

        # Use DMCito API key
        api_key = os.getenv("DMCITO_API_KEY")
        if api_key:
            kwargs["api_key"] = api_key

        # Use DMCito base URL
        base_url = os.getenv("DMCITO_BASE_URL")
        if base_url:
            kwargs["base_url"] = base_url

        return kwargs