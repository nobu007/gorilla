"""
Web Search API - Legacy Compatibility Wrapper

This file provides backward compatibility for the original web_search.py interface.
All functionality is now organized in the web_search/ package.

For new code, prefer importing from the package:
    from web_search import WebSearchAPI

This wrapper maintains compatibility with existing imports:
    from web_search import WebSearchAPI
"""

# Re-export everything from the new package
from web_search import WebSearchAPI, SearchConfig, SearchBackend, DuckDuckGoBackend, SerpApiBackend, fetch_url_content, __version__

# Re-export legacy functions for backward compatibility
from web_search.web_search_legacy import fetch_url_content as _fetch_url_content_legacy

# Keep the original file-level docstring for documentation
__doc__ = web_search.__doc__

# Ensure all original symbols are available
__all__ = [
    'WebSearchAPI',
    'SearchConfig',
    'SearchBackend',
    'DuckDuckGoBackend',
    'SerpApiBackend',
    'fetch_url_content',
    '__version__',
]