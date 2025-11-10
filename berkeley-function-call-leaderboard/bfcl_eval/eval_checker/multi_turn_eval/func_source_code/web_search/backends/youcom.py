"""You.com search backend implementation."""

import os
from typing import Dict, Any, Optional, Union, List

import requests

from .base import SearchBackend
from ..constants import DEFAULT_MAX_RESULTS


class YouComBackend(SearchBackend):
    """You.com search backend using YDC API."""

    def __init__(self, api_key: Optional[str] = None, show_snippet: bool = True):
        self.api_key = api_key or os.getenv("YDC_API_KEY")
        self.show_snippet = show_snippet

    @property
    def name(self) -> str:
        return "youcom"

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0

    def search(self, keywords: str, max_results: int, region: str, **kwargs) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """
        Perform search using You.com API.

        Args:
            keywords: Search query
            max_results: Maximum number of results to return
            region: Search region code (not fully supported by You.com)
            **kwargs: Additional parameters (ignored for You.com)

        Returns:
            List of search results or error dict
        """
        if not self.is_available():
            return {"error": "You.com API key not configured. Set YDC_API_KEY environment variable or provide api_key parameter."}

        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }

            params = {
                "query": keywords,
                "count": min(max_results, 10)  # You.com API limit
            }

            response = requests.get(
                "https://api.ydc-index.io/v1/search",
                headers=headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            # Extract web and news results
            web_results = data.get("results", {}).get("web", [])
            news_results = data.get("results", {}).get("news", [])

            # Combine results, prioritizing web results
            all_results = web_results + news_results

            if not all_results:
                return {"error": "No search results found"}

            # Convert to standard format
            results = []
            for result in all_results[:max_results]:
                result_data = {
                    "title": result.get("title", ""),
                    "href": result.get("url", ""),
                }

                if self.show_snippet:
                    # You.com provides 'snippet' in web results and 'description' in news results
                    snippet = result.get("snippet") or result.get("description", "")
                    result_data["body"] = snippet

                results.append(result_data)

            return results

        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch You.com results: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error while processing You.com results: {str(e)}"}

    def get_content(self, urls: List[str]) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Get content from specific URLs using You.com live crawl API.

        Args:
            urls: List of URLs to crawl

        Returns:
            Dictionary with content or error information
        """
        if not self.is_available():
            return {"error": "You.com API key not configured"}

        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "urls": urls,
                "livecrawl_formats": "html"
            }

            response = requests.post(
                "https://api.ydc-index.io/v1/contents",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            return {"results": response.json()}

        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch content: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error while fetching content: {str(e)}"}