"""Main WebSearchAPI implementation."""

import random
from typing import Dict, Any, List, Optional, Union

from .backends import SearchBackend
from .config import SearchConfig
from .constants import DEFAULT_MAX_RESULTS, DEFAULT_REGION
from .utils import generate_fake_error
from .web_search_legacy import fetch_url_content, _fake_requests_get_error_msg  # Legacy functions


class WebSearchAPI:
    """
    Main Web Search API with backend abstraction and automatic fallback.

    This class provides a unified interface for multiple search backends
    with automatic selection and fallback capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize WebSearchAPI with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self._api_description = "This tool belongs to the Web Search API category. It provides functions to search the web and browse search results."

        # Configuration and backends
        self.config = SearchConfig(config)
        self.backends = {backend.name: backend for backend in self.config.create_backends()}

        # Legacy compatibility
        self.show_snippet = self.config.show_snippet

        # Random generators for error simulation (not currently used)
        self._random = random.Random(337)
        self._rng = random.Random(1053)

    def _load_scenario(self, initial_config: dict, long_context: bool = False):
        """
        Load scenario configuration for backward compatibility.

        Args:
            initial_config: Configuration dictionary
            long_context: Unused parameter for compatibility
        """
        # Update config with scenario data
        self.config = SearchConfig(initial_config)
        self.backends = {backend.name: backend for backend in self.config.create_backends()}
        self.show_snippet = self.config.show_snippet

    def _select_backend(self, backend_name: Optional[str] = None) -> SearchBackend:
        """
        Select the appropriate backend with fallback logic.

        Args:
            backend_name: Explicit backend name to use

        Returns:
            Selected SearchBackend instance

        Raises:
            RuntimeError: If no backends are available
        """
        # Explicit backend selection
        if backend_name and backend_name in self.backends:
            return self.backends[backend_name]

        # Preferred backend from config
        if self.config.preferred_backend and self.config.preferred_backend in self.backends:
            return self.backends[self.config.preferred_backend]

        # Smart fallback: prefer SerpAPI > You.com > DuckDuckGo
        if "serpapi" in self.backends and self.backends["serpapi"].is_available():
            print("[WebSearchAPI] Using SerpAPI backend (auto-detected)")
            return self.backends["serpapi"]

        if "youcom" in self.backends and self.backends["youcom"].is_available():
            print("[WebSearchAPI] Using You.com backend (auto-detected)")
            return self.backends["youcom"]

        # Default to DuckDuckGo
        if "duckduckgo" in self.backends:
            print("[WebSearchAPI] Using DuckDuckGo backend with proxy")
            return self.backends["duckduckgo"]

        raise RuntimeError("No search backends available")

    def get_available_backends(self) -> List[str]:
        """
        Get list of available backend names.

        Returns:
            List of available backend names
        """
        return [name for name, backend in self.backends.items() if backend.is_available()]

    def print_backend_status(self):
        """Print status of all backends."""
        print("[WebSearchAPI] Backend Status:")
        for name, backend in self.backends.items():
            status = "✅ Available" if backend.is_available() else "❌ Not Available"
            print(f"  - {name}: {status}")

        print(f"[WebSearchAPI] Preferred backend: {self.config.preferred_backend or 'Auto'}")
        print(f"[WebSearchAPI] Fallback enabled: {self.config.enable_fallback}")

    def search_engine_query(
        self,
        keywords: str,
        max_results: Optional[int] = DEFAULT_MAX_RESULTS,
        region: Optional[str] = DEFAULT_REGION,
        use_proxy: Optional[bool] = None,
        backend: Optional[str] = None,
    ) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """
        This function queries the search engine for the provided keywords and region.

        Args:
            keywords (str): The keywords to search for.
            max_results (int, optional): The maximum number of search results to return. Defaults to 10.
            region (str, optional): The region to search in. Defaults to "wt-wt". See documentation for region codes.
            use_proxy (bool, optional): Whether to use proxy for requests.
                - If None (default): Auto-detect (True for DuckDuckGo, False for SerpAPI)
                - For DuckDuckGo: Enables Brightdata residential proxy
                - For SerpAPI: Ignored (SerpAPI handles its own routing)
            backend (str, optional): The search backend to use.
                - None (default): Auto-select (SerpAPI > You.com > DuckDuckGo priority)
                - "serpapi": Force SerpAPI (will fail if API key not available)
                - "youcom": Force You.com (requires YDC_API_KEY)
                - "duckduckgo": Force DuckDuckGo (with optional proxy support)

        Returns:
            List of result dicts for success, or dict with 'error' key for failure.
            Each result dict contains:
            - 'title' (str): The title of the search result
            - 'href' (str): The URL of the search result
            - 'body' (str): A brief description or snippet (if show_snippet=True)

        Examples:
            # Auto-select backend (preferred approach)
            api = WebSearchAPI()
            results = api.search_engine_query("Python machine learning")

            # Force specific backend
            results = api.search_engine_query("Python ML", backend="duckduckgo", use_proxy=True)
            results = api.search_engine_query("Python ML", backend="serpapi")

            # Check available backends
            api.print_backend_status()
        """
        try:
            # Check if explicitly requested backend is available
            if backend:
                # Explicit backend requested
                if backend not in self.backends:
                    return {"error": f"Backend '{backend}' is not available. Check configuration."}
                selected_backend = self.backends[backend]
                if not selected_backend.is_available():
                    return {"error": f"Backend '{backend}' is not available. Check API key configuration."}
            else:
                # Auto-selection logic for when no specific backend is requested
                selected_backend = self._select_backend(backend)

            # Prepare search parameters
            search_params = {
                "keywords": keywords,
                "max_results": max_results,
                "region": region,
            }

            # Handle proxy parameter
            if use_proxy is None:
                # Auto-detect proxy usage
                if selected_backend.name == "duckduckgo":
                    # Use proxy for DuckDuckGo if configured
                    proxy_configured = bool(self.config.proxy_config.get("username"))
                    search_params["use_proxy"] = proxy_configured
                    if proxy_configured:
                        print(f"[WebSearchAPI] Using configured proxy for {selected_backend.name}")
                else:
                    search_params["use_proxy"] = False
            else:
                search_params["use_proxy"] = use_proxy

            # Execute search
            result = selected_backend.search(**search_params)

            # Handle fallback logic only when no specific backend was requested
            if "error" in result and self.config.enable_fallback and backend is None:
                # Try the next available backend
                available_backends = [b for b in self.backends.values() if b.is_available() and b != selected_backend]

                if available_backends:
                    fallback_backend = available_backends[0]
                    print(f"[WebSearchAPI] {selected_backend.name} failed. Falling back to {fallback_backend.name}")

                    # Adjust proxy settings for fallback
                    if fallback_backend.name == "duckduckgo":
                        search_params["use_proxy"] = bool(self.config.proxy_config.get("username"))
                    else:
                        search_params["use_proxy"] = False

                    result = fallback_backend.search(**search_params)

            return result

        except Exception as e:
            return {"error": f"Search execution failed: {str(e)}"}

    def search_with_fallback(
        self,
        keywords: str,
        max_results: Optional[int] = DEFAULT_MAX_RESULTS,
        region: Optional[str] = DEFAULT_REGION,
        backends: Optional[List[str]] = None,
        **kwargs
    ) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """
        Search with explicit fallback to multiple backends.

        Args:
            keywords: Search query
            max_results: Maximum number of results
            region: Search region
            backends: List of backend names to try in order. If None, uses auto-detection.
            **kwargs: Additional parameters passed to backends

        Returns:
            Search results or error information
        """
        if backends is None:
            backends = self.get_available_backends()

        last_error = None

        for backend_name in backends:
            if backend_name not in self.backends:
                continue

            backend = self.backends[backend_name]
            if not backend.is_available():
                continue

            print(f"[WebSearchAPI] Trying backend: {backend_name}")

            try:
                result = backend.search(
                    keywords=keywords,
                    max_results=max_results,
                    region=region,
                    **kwargs
                )

                if "error" not in result:
                    print(f"[WebSearchAPI] Success with {backend_name}")
                    return result
                else:
                    last_error = result["error"]
                    print(f"[WebSearchAPI] {backend_name} failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                print(f"[WebSearchAPI] {backend_name} error: {last_error}")
                continue

        return {"error": f"All backends failed. Last error: {last_error}"}

    # Legacy method for backward compatibility
    def fetch_url_content(self, url: str, mode: str = "raw") -> Union[Dict[str, str], Dict[str, Any]]:
        """
        This function retrieves content from the provided URL and processes it based on the selected mode.

        Legacy method maintained for backward compatibility.

        Args:
            url (str): The URL to fetch content from. Must start with 'http://' or 'https://'.
            mode (str, optional): The mode to process the fetched content. Defaults to "raw".
                Supported modes are:
                    - "raw": Returns the raw HTML content.
                    - "markdown": Converts raw HTML content to Markdown format for better readability, using html2text.
                    - "truncate": Extracts and cleans text by removing scripts, styles, and extraneous whitespace.
        """
        return fetch_url_content(url, mode)

    # Legacy method for backward compatibility
    def _fake_requests_get_error_msg(self, url: str) -> str:
        """
        Return a realistic‑looking requests/urllib3 error message.

        Legacy method maintained for backward compatibility.
        """
        return generate_fake_error(url, self._rng)