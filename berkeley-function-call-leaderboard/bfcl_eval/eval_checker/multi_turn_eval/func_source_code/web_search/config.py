"""Configuration management for Web Search API."""

import os
from typing import Dict, Any, List, Optional

from .backends import DuckDuckGoBackend, SerpApiBackend, YouComBackend
from .constants import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT


class SearchConfig:
    """Configuration manager for search backends."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._parse_config()

    def _parse_config(self):
        """Parse configuration from various sources."""
        # Base proxy configuration from environment variables
        try:
            port = int(os.getenv("BRIGHTDATA_PORT", str(DEFAULT_PROXY_PORT)))
        except (ValueError, TypeError):
            port = DEFAULT_PROXY_PORT

        env_proxy_config = {
            "host": os.getenv("BRIGHTDATA_HOST", DEFAULT_PROXY_HOST),
            "port": port,
            "username": os.getenv("BRIGHTDATA_USERNAME"),
            "password": os.getenv("BRIGHTDATA_PASSWORD"),
        }

        # Start with environment config
        self.proxy_config = env_proxy_config.copy()

        # Update with any proxy config from config dict (but preserve env vars)
        if "proxy_config" in self.config:
            config_proxy = self.config["proxy_config"]
            # Only update non-None values from config, keeping env vars for missing fields
            for key, value in config_proxy.items():
                if value is not None:
                    self.proxy_config[key] = value

        # Display configuration
        self.show_snippet = self.config.get("show_snippet", True)

        # Backend preferences
        self.preferred_backend = self.config.get("preferred_backend", None)
        self.enable_fallback = self.config.get("enable_fallback", True)

    def get_available_backends(self) -> List[str]:
        """Get list of available backend names."""
        available = []

        # Check SerpAPI
        if os.getenv("SERPAPI_API_KEY"):
            available.append("serpapi")

        # Check You.com API
        if os.getenv("YDC_API_KEY"):
            available.append("youcom")

        # DuckDuckGo is always available
        available.append("duckduckgo")

        return available

    def create_backends(self) -> List["SearchBackend"]:
        """Create instances of available backends."""
        backends = []

        # Always create DuckDuckGo backend
        ddg_backend = DuckDuckGoBackend(
            proxy_config=self.proxy_config,
            show_snippet=self.show_snippet
        )
        backends.append(ddg_backend)

        # Create SerpAPI backend if API key is available
        if os.getenv("SERPAPI_API_KEY"):
            serpapi_backend = SerpApiBackend(
                api_key=os.getenv("SERPAPI_API_KEY"),
                show_snippet=self.show_snippet
            )
            backends.append(serpapi_backend)

        # Always create You.com backend (it will check availability internally)
        youcom_backend = YouComBackend(
            api_key=os.getenv("YDC_API_KEY"),
            show_snippet=self.show_snippet
        )
        backends.append(youcom_backend)

        return backends