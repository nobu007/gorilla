import os
import logging

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler
from openai import PermissionDeniedError
import httpx


class OpenRouterHandler(OpenAICompletionsHandler):
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
        """Override to use OpenRouter API settings instead of OpenAI."""
        kwargs = {}

        # Use OpenRouter API key
        api_key = self._get_api_key()
        if api_key:
            kwargs["api_key"] = api_key

        # Use OpenRouter base URL
        base_url = self._get_base_url()
        if base_url:
            kwargs["base_url"] = base_url

        # Set custom timeout
        kwargs["timeout"] = httpx.Timeout(timeout=300.0, connect=8.0)

        return kwargs

    def _get_api_key(self):
        """Use OpenRouter API key instead of OpenAI API key."""
        return os.getenv("OPENROUTER_API_KEY")

    def _get_base_url(self):
        """Use OpenRouter base URL instead of OpenAI base URL."""
        return "https://openrouter.ai/api/v1"

    def generate_with_backoff(self, **kwargs):
        """Override to handle moderation errors without retry."""
        try:
            return super().generate_with_backoff(**kwargs)
        except PermissionDeniedError as e:
            error_message = str(e)
            if "moderation" in error_message.lower():
                # Don't retry moderation errors - they will continue to fail
                logging.error(f"Moderation error for {self.model_name}: {error_message}")
                # For moderation errors, create a new exception with enhanced message
                # but preserve the original response and body
                enhanced_message = (
                    f"Model {self.model_name} blocked the input due to moderation. "
                    f"This is a limitation of certain models (especially Meta's free-tier). "
                    f"Consider using a different model or upgrading to a paid tier. "
                    f"Original error: {error_message}"
                )
                # Re-raise using the original exception but with a custom message
                # We need to preserve the original response and body
                raise type(e)(
                    message=enhanced_message,
                    response=e.response,
                    body=e.body
                ) from e
            # For other permission errors, let the base class handle them
            raise

    def _query_FC(self, inference_data: dict):
        """Override to handle moderation errors for Meta models."""
        try:
            return super()._query_FC(inference_data)
        except PermissionDeniedError as e:
            self._handle_moderation_error(e)

    def _query_prompting(self, inference_data: dict):
        """Override to handle moderation errors for regular prompting."""
        try:
            return super()._query_prompting(inference_data)
        except PermissionDeniedError as e:
            self._handle_moderation_error(e)

    def _handle_moderation_error(self, error: PermissionDeniedError):
        """Helper method to handle moderation errors consistently."""
        error_message = str(error)
        is_meta_model = "meta-llama" in self.model_name.lower()
        is_moderation_error = "moderation" in error_message.lower()

        if is_moderation_error:
            logging.warning(f"Moderation block detected for {self.model_name}: {error_message}")

            # Create enhanced error message
            if is_meta_model and "misc" in error_message.lower():
                enhanced_message = (
                    f"Meta model {self.model_name} blocked the input due to moderation filtering. "
                    f"This is a known limitation of Meta's free-tier models which can be overly strict. "
                    f"Recommendations: 1) Try rephrasing your input, 2) Use a different model, "
                    f"3) Upgrade to a paid tier for less restrictive moderation. "
                    f"Original error: {error_message}"
                )
            else:
                enhanced_message = (
                    f"Model {self.model_name} blocked the input due to moderation. "
                    f"Consider using a different model or rephrasing your input. "
                    f"Original error: {error_message}"
                )

            # Re-raise using the original exception type but with enhanced message
            # Preserve the original response and body to maintain exception structure
            raise type(error)(
                message=enhanced_message,
                response=error.response,
                body=error.body
            ) from error
        else:
            # Re-raise non-moderation permission errors as-is
            raise

    def decode_execute(self, result, has_tool_call_tag: bool):
        """Override decode_execute to handle Meta model JSON parsing issues."""
        from bfcl_eval.model_handler.utils import default_decode_execute_prompting
        from bfcl_eval.model_handler.enhanced_decode_execute_handler import EnhancedDecodeExecuteHandler

        # Check if this is a Meta model and if the result contains problematic JSON fragments
        is_meta_model = "meta-llama" in self.model_name.lower()

        if is_meta_model and isinstance(result, list):
            # Check if any items in the list contain JSON fragments that look like our error cases
            has_json_fragments = False
            for item in result:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, str) and (
                            (value.startswith("function") and "..." in value) or
                            (value.startswith("core_memory") and "..." in value) or
                            value.endswith("...")
                        ):
                            has_json_fragments = True
                            break
                    if has_json_fragments:
                        break

            if has_json_fragments:
                logging.warning(f"Meta model {self.model_name} returned JSON fragments. Attempting to clean up...")

                # Clean up the result by replacing problematic values with empty dicts
                cleaned_result = []
                for item in result:
                    if isinstance(item, dict):
                        cleaned_item = {}
                        for key, value in item.items():
                            if isinstance(value, str) and (
                                (value.startswith("function") and "..." in value) or
                                (value.startswith("core_memory") and "..." in value) or
                                value.endswith("...")
                            ):
                                # Replace JSON fragments with empty dict
                                cleaned_item[key] = {}
                                logging.debug(f"Cleaned JSON fragment in '{key}': '{value[:50]}...' -> {{}}")
                            else:
                                cleaned_item[key] = value
                        cleaned_result.append(cleaned_item)
                    else:
                        cleaned_result.append(item)

                # Use the enhanced handler's decode_execute with the cleaned result
                handler = EnhancedDecodeExecuteHandler(
                    self.model_name, self.temperature, self.registry_name, self.is_fc_model
                )
                return handler.decode_execute(cleaned_result, has_tool_call_tag)

        # For non-Meta models or when no issues are detected, use the default implementation
        handler = EnhancedDecodeExecuteHandler(
            self.model_name, self.temperature, self.registry_name, self.is_fc_model
        )
        return handler.decode_execute(result, has_tool_call_tag)