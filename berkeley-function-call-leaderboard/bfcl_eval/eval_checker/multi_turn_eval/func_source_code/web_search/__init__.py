"""
Web Search API Package

Backend-abstracted web search API with proxy support and automatic fallback.

This package provides:
- Abstract backend interface for search engines
- DuckDuckGo and SerpAPI implementations
- Automatic backend selection and fallback
- Proxy support for web scraping
- Configuration management
- Legacy compatibility

Example usage:
    from web_search import WebSearchAPI

    # Auto-select backend (preferred)
    api = WebSearchAPI()
    results = api.search_engine_query("Python machine learning")

    # Explicit backend selection
    results = api.search_engine_query("query", backend="duckduckgo", use_proxy=True)
"""

from .api import WebSearchAPI
from .config import SearchConfig
from .backends import SearchBackend, DuckDuckGoBackend, SerpApiBackend
from .__version__ import __version__

# Legacy imports for backward compatibility
from .web_search_legacy import fetch_url_content

__all__ = [
    # Main API
    "WebSearchAPI",
    "SearchConfig",
    # Backends
    "SearchBackend",
    "DuckDuckGoBackend",
    "SerpApiBackend",
    # Legacy
    "fetch_url_content",
    # Package info
    "__version__",
]

# Package-level convenience function for quick usage
def quick_search(keywords: str, max_results: int = 10, backend: str = None, use_proxy: bool = None) -> list:
    """
    Quick search function for simple use cases.

    Args:
        keywords: Search query
        max_results: Maximum number of results
        backend: Backend to use (None for auto-selection)
        use_proxy: Whether to use proxy (None for auto-detect)

    Returns:
        Search results list or error dict
    """
    api = WebSearchAPI()
    return api.search_engine_query(
        keywords=keywords,
        max_results=max_results,
        backend=backend,
        use_proxy=use_proxy
    )