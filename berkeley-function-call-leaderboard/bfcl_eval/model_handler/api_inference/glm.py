import os
import time
import random
from typing import Any

import httpx
from openai import RateLimitError

from bfcl_eval.model_handler.api_inference.openai_completion import OpenAICompletionsHandler


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

    def _is_retryable_error(self, error):
        """Check if error is worth retrying based on GLM API behavior."""
        if hasattr(error, 'response') and error.response is not None:
            try:
                error_data = error.response.json()
                error_code = str(error_data.get('error', {}).get('code', ''))
                error_message = error_data.get('error', {}).get('message', '').lower()

                # Error 1210 appears to be a temporary API state/concurrency issue
                # Based on testing, it's not a true parameter validation error
                if error_code == '1210':
                    return True

                # Standard server errors that should be retried
                if error_code in ['500', '502', '503', '504']:
                    return True

                # Rate limit errors
                if error_code in ['429', 'rate_limit_exceeded', '1201', '1202']:
                    return True

                # Server error indicators in message
                if any(indicator in error_message for indicator in ['temporary', 'server error', 'internal error', 'service unavailable']):
                    return True

            except:
                pass

        return isinstance(error, RateLimitError)

    def _generate_with_glm_backoff(self, **kwargs):
        """Retry logic for GLM API to handle Error 1210 and temporary issues."""
        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                api_response = self.client.chat.completions.create(**kwargs)
                end_time = time.time()
                return api_response, end_time - start_time

            except Exception as e:
                if attempt == max_retries:
                    raise

                # Check if this error should be retried
                if self._is_retryable_error(e):
                    # Exponential backoff with jitter
                    base_delay = 0.5
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.3)
                    print(f"GLM API temporarily unavailable (Error 1210). Retrying in {delay:.2f}s... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                else:
                    # Non-retryable error, don't waste time
                    raise

    def _normalize_content(self, content: Any) -> str:
        """Convert OpenAI SDK content formats into plain text strings."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    if "text" in part:
                        parts.append(str(part.get("text", "")))
                    elif part.get("type") == "input_text":
                        parts.append(str(part.get("text", "")))
                else:
                    parts.append(str(part))
            return "\n".join([p for p in parts if p])
        return str(content)

    def _serialize_tool_calls(self, tool_calls: Any):
        serialized_calls = []
        for call in tool_calls:
            if isinstance(call, dict):
                call_id = call.get("id")
                call_type = call.get("type", "function")
                function_data = call.get("function", {})
                function_name = function_data.get("name")
                function_args = function_data.get("arguments", "{}")
            else:
                call_id = getattr(call, "id", None)
                call_type = getattr(call, "type", "function")
                function_obj = getattr(call, "function", None)
                function_name = getattr(function_obj, "name", None) if function_obj else None
                function_args = getattr(function_obj, "arguments", "{}") if function_obj else "{}"

            if not function_name:
                continue

            serialized_calls.append(
                {
                    "id": call_id,
                    "type": call_type,
                    "function": {
                        "name": function_name,
                        "arguments": function_args,
                    },
                }
            )
        return serialized_calls

    def _sanitize_messages(self, message_history: list[Any]) -> list[dict]:
        allowed_roles = {"system", "user", "assistant", "tool"}
        sanitized = []

        for raw_msg in message_history:
            if isinstance(raw_msg, dict):
                role = raw_msg.get("role", "user")
                content = raw_msg.get("content")
                tool_call_id = raw_msg.get("tool_call_id")
                tool_calls = raw_msg.get("tool_calls")
                name = raw_msg.get("name")
            else:
                role = getattr(raw_msg, "role", "user")
                content = getattr(raw_msg, "content", "")
                tool_call_id = getattr(raw_msg, "tool_call_id", None)
                tool_calls = getattr(raw_msg, "tool_calls", None)
                name = getattr(raw_msg, "name", None)

            if role not in allowed_roles:
                role = "user"

            msg_dict = {
                "role": role,
                "content": self._normalize_content(content),
            }

            if name:
                msg_dict["name"] = name

            if role == "tool" and tool_call_id:
                msg_dict["tool_call_id"] = tool_call_id

            if tool_calls:
                serialized_calls = self._serialize_tool_calls(tool_calls)
                if serialized_calls:
                    msg_dict["tool_calls"] = serialized_calls

            sanitized.append(msg_dict)

        return sanitized

    def _query_FC(self, inference_data: dict):
        """Normalize chat history and send OpenAI-compatible payload to GLM."""
        message = inference_data["message"]
        tools = inference_data["tools"]
        inference_data["inference_input_log"] = {
            "message": repr(message),
            "tools": tools,
        }

        normalized_messages = self._sanitize_messages(message)

        kwargs = {
            "messages": normalized_messages,
            "model": self.model_name,
            "temperature": self.temperature,
        }

        if tools:
            kwargs["tools"] = tools

        self._record_inference_snapshot(
            inference_data,
            extra={"request_payload": kwargs, "stage": "glm_payload"},
        )

        return self._generate_with_glm_backoff(**kwargs)
