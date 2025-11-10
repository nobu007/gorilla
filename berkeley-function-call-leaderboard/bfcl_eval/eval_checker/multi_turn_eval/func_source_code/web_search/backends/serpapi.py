"""SerpAPI search backend implementation."""

import os
import random
import time
from typing import Dict, Any, Optional, Union, List

from serpapi import GoogleSearch

from .base import SearchBackend
from ..constants import DEFAULT_MAX_RESULTS


class SerpApiBackend(SearchBackend):
    """SerpAPI search backend."""

    def __init__(self, api_key: Optional[str] = None, show_snippet: bool = True):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.show_snippet = show_snippet

    @property
    def name(self) -> str:
        return "serpapi"

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0

    def search(self, keywords: str, max_results: int, region: str, **kwargs) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """
        Perform search using SerpAPI.

        Args:
            keywords: Search query
            max_results: Maximum number of results to return
            region: Search region code
            **kwargs: Additional parameters (ignored for SerpAPI)

        Returns:
            List of search results or error dict
        """
        if not self.is_available():
            return {"error": "SerpAPI key not configured. Set SERPAPI_API_KEY environment variable or provide api_key parameter."}

        backoff = 2
        params = {
            "engine": "duckduckgo",
            "q": keywords,
            "kl": region,
            "api_key": self.api_key,
        }

        while True:
            try:
                search = GoogleSearch(params)
                search_results = search.get_dict()
            except Exception as e:
                if "429" in str(e):
                    wait_time = backoff + random.uniform(0, backoff)
                    error_block = (
                        "*" * 100
                        + f"\n❗️❗️ [SerpApiBackend] Received 429 from SerpAPI. Retrying in {wait_time:.1f} seconds…"
                        + "*" * 100
                    )
                    print(error_block)
                    time.sleep(wait_time)
                    backoff = min(backoff * 2, 120)
                    continue
                else:
                    error_block = (
                        "*" * 100
                        + f"\n❗️❗️ [SerpApiBackend] Error from SerpAPI: {str(e)}."
                        + "*" * 100
                    )
                    print(error_block)
                    return {"error": str(e)}

            if "error" in search_results and "429" in str(search_results["error"]):
                wait_time = backoff + random.uniform(0, backoff)
                error_block = (
                    "*" * 100
                    + f"\n❗️❗️ [SerpApiBackend] Received 429 from SerpAPI. Retrying in {wait_time:.1f} seconds…"
                    + "*" * 100
                )
                print(error_block)
                time.sleep(wait_time)
                backoff = min(backoff * 2, 120)
                continue

            break

        if "organic_results" not in search_results:
            return {"error": "Failed to retrieve the search results from server. Please try again later."}

        search_results = search_results["organic_results"]
        results = []

        for result in search_results[:max_results]:
            result_data = {
                "title": result["title"],
                "href": result["link"],
            }

            if self.show_snippet:
                result_data["body"] = result["snippet"]

            results.append(result_data)

        return results