"""DuckDuckGo search backend implementation."""

import random
import time
from typing import Dict, Any, Optional, Union, List

import requests
from bs4 import BeautifulSoup

from .base import SearchBackend
from ..constants import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT, DEFAULT_REQUEST_TIMEOUT, DEFAULT_MAX_RETRIES, DEFAULT_RETRY_BACKOFF, MAX_RETRY_BACKOFF


class DuckDuckGoBackend(SearchBackend):
    """DuckDuckGo search backend with proxy support."""

    def __init__(self, proxy_config: Optional[Dict[str, Any]] = None, show_snippet: bool = True):
        self.proxy_config = proxy_config or {}
        self.show_snippet = show_snippet

    @property
    def name(self) -> str:
        return "duckduckgo"

    def is_available(self) -> bool:
        # DuckDuckGo is always available (no API key required)
        return True

    def _get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """Return proxy configuration or None if not configured."""
        if not all([self.proxy_config.get("username"), self.proxy_config.get("password")]):
            return None

        host = self.proxy_config.get("host", DEFAULT_PROXY_HOST)
        port = self.proxy_config.get("port", DEFAULT_PROXY_PORT)
        username = self.proxy_config["username"]
        password = self.proxy_config["password"]

        proxy_url = f"http://{username}:{password}@{host}:{port}"
        return {"http": proxy_url, "https": proxy_url}

    def search(self, keywords: str, max_results: int, region: str, use_proxy: bool = False, **kwargs) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """
        Perform DuckDuckGo search with optional proxy support.

        Args:
            keywords: Search query
            max_results: Maximum number of results to return
            region: Search region code
            use_proxy: Whether to use proxy for requests
            **kwargs: Additional parameters (ignored for DuckDuckGo)

        Returns:
            List of search results or error dict
        """
        url = "https://duckduckgo.com/html/"

        params = {
            "q": keywords,
            "kl": region if region != "wt-wt" else "us-en",
        }

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        proxies = self._get_proxy_dict() if use_proxy else None

        # Handle proxy unavailability
        if use_proxy and proxies is None:
            print("[DuckDuckGoBackend] Proxy requested but not configured. Using direct connection.")
            proxies = None

        backoff = DEFAULT_RETRY_BACKOFF
        max_retries = DEFAULT_MAX_RETRIES

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, params=params, headers=headers,
                    proxies=proxies, timeout=DEFAULT_REQUEST_TIMEOUT, allow_redirects=True
                )
                response.raise_for_status()

                # Parse HTML results
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []

                result_divs = soup.find_all('div', class_='result')

                for i, result_div in enumerate(result_divs[:max_results]):
                    try:
                        title_link = result_div.find('a', class_='result__a')
                        if not title_link:
                            continue

                        title = title_link.get_text(strip=True)
                        href = title_link.get('href', '')

                        snippet_div = result_div.find('a', class_='result__snippet')
                        snippet = snippet_div.get_text(strip=True) if snippet_div else ""

                        result_data = {"title": title, "href": href}

                        if self.show_snippet:
                            result_data["body"] = snippet

                        results.append(result_data)

                    except Exception as e:
                        print(f"Error parsing result {i}: {e}")
                        continue

                return results

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = backoff + random.uniform(0, 1)
                    proxy_status = "with proxy" if use_proxy else "without proxy"
                    print(f"[DuckDuckGoBackend] Request failed (attempt {attempt + 1}/{max_retries}) {proxy_status}: {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    backoff = min(backoff * 2, MAX_RETRY_BACKOFF)
                    continue
                else:
                    return {"error": f"Failed to fetch DuckDuckGo results after {max_retries} attempts: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error while processing DuckDuckGo results: {str(e)}"}

        return []