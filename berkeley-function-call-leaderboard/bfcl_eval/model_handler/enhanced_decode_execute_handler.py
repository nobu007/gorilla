import json
from typing import Any

from bfcl_eval.model_handler.utils import (
    convert_to_function_call,
    default_decode_execute_prompting,
)
from bfcl_eval.model_handler.base_handler import BaseHandler


class EnhancedDecodeExecuteHandler(BaseHandler):
    """
    Enhanced base handler that provides robust decode_execute functionality
    with JSON parsing and error handling for function calling models.

    This class eliminates code duplication across multiple model handlers
    by providing a standardized decode_execute implementation that handles:
    - None or empty string responses
    - String responses that require JSON parsing
    - Invalid JSON with graceful fallback
    - Proper format conversion using convert_to_function_call utility
    - Optional preprocessing for non-FC models (override _preprocess_non_fc_result)
    """

    def _preprocess_non_fc_result(self, result: Any) -> Any:
        """
        Override this method to perform custom preprocessing on the result
        for non-function-calling models before passing to default_decode_execute_prompting.

        Args:
            result: The raw model response

        Returns:
            Preprocessed result
        """
        return result

    def decode_execute(self, result: Any, has_tool_call_tag: bool):
        """
        Enhanced decode_execute implementation with robust error handling.

        Args:
            result: The model response to decode
            has_tool_call_tag: Whether tool call tags are present

        Returns:
            Decoded function calls ready for execution
        """

        if not self.is_fc_model:
            result = self._preprocess_non_fc_result(result)
            return default_decode_execute_prompting(result, has_tool_call_tag)
        else:
            # Ensure result is in the expected format for convert_to_function_call
            # Handle None or empty responses
            if result is None or (isinstance(result, str) and result.strip() == ""):
                result = []
            elif isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                    # Ensure it's a list or dict
                    if isinstance(parsed_result, dict):
                        result = [parsed_result]
                    elif not isinstance(parsed_result, list):
                        result = [{parsed_result: {}}]
                    else:
                        result = parsed_result
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as simple function name
                    result = [{result: {}}]
            elif isinstance(result, list):
                # Check if this is a list of text responses (not function calls)
                if all(isinstance(item, str) for item in result):
                    # This is likely a text response from an FC model that didn't make function calls
                    # For FC models, text responses usually indicate they chose not to make function calls
                    # Return empty list to indicate no function calls to execute
                    return []

                # For mixed lists, try to extract valid function calls
                # convert_to_function_call will handle the filtering of non-dict items
                pass

            return convert_to_function_call(result)