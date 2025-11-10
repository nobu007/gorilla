"""Test utilities and fixtures for Web Search API tests."""

import os
import unittest.mock as mock
from typing import Dict, Any, Optional
from unittest.mock import Mock

try:
    import pytest
except ImportError:
    pytest = None


class MockResponse:
    """Mock HTTP response object for testing."""

    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self) -> Dict[str, Any]:
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def create_mock_duckduckgo_response(results_count: int = 3) -> MockResponse:
    """Create a mock DuckDuckGo HTML response."""
    html_content = """
    <html>
    <body>
"""

    for i in range(1, results_count + 1):
        html_content += f"""
        <div class="result">
            <a class="result__a" href="https://example{i}.com">Result {i} Title</a>
            <a class="result__snippet">Result {i} description snippet here</a>
        </div>
"""

    html_content += """
    </body>
    </html>
    """

    return MockResponse({"content": html_content})


def create_mock_serpapi_response(results_count: int = 3) -> MockResponse:
    """Create a mock SerpAPI response."""
    results = []
    for i in range(1, results_count + 1):
        results.append({
            "title": f"Result {i} Title",
            "link": f"https://example{i}.com",
            "snippet": f"Result {i} description snippet here"
        })

    return MockResponse({
        "organic_results": results
    })

def create_mock_serpapi_response_data(results_count: int = 3) -> dict:
    """Create mock SerpAPI response data (not wrapped)."""
    results = []
    for i in range(1, results_count + 1):
        results.append({
            "title": f"Result {i} Title",
            "link": f"https://example{i}.com",
            "snippet": f"Result {i} description snippet here"
        })

    return {"organic_results": results}


def create_mock_youcom_response(results_count: int = 3) -> MockResponse:
    """Create a mock You.com API response."""
    web_results = []
    for i in range(1, results_count + 1):
        web_results.append({
            "title": f"Web Result {i}",
            "url": f"https://webexample{i}.com",
            "snippet": f"Web result {i} description"
        })

    news_results = []
    for i in range(1, min(2, results_count) + 1):
        news_results.append({
            "title": f"News Result {i}",
            "url": f"https://newsexample{i}.com",
            "description": f"News result {i} description"
        })

    return MockResponse({
        "results": {
            "web": web_results,
            "news": news_results
        }
    })


class EnvironmentManager:
    """Manager for environment variable testing."""

    def __init__(self):
        self.original_env = {}

    def set(self, key: str, value: str):
        """Set an environment variable."""
        if key not in self.original_env:
            self.original_env[key] = os.environ.get(key)
        os.environ[key] = value

    def unset(self, key: str):
        """Unset an environment variable."""
        if key not in self.original_env:
            self.original_env[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]

    def restore(self):
        """Restore all original environment variables."""
        for key, value in self.original_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value
        self.original_env = {}


class BackendTestData:
    """Test data generator for backends."""

    @staticmethod
    def get_test_queries() -> list:
        """Get a list of test queries."""
        return [
            "python programming",
            "artificial intelligence",
            "web scraping",
            "machine learning",
            "data science"
        ]

    @staticmethod
    def get_test_regions() -> list:
        """Get a list of test regions."""
        return [
            "wt-wt",  # No region
            "us-en",  # United States English
            "uk-en",  # United Kingdom English
            "jp-jp",  # Japan
            "de-de",  # Germany
        ]

    @staticmethod
    def get_invalid_queries() -> list:
        """Get invalid test queries."""
        return [
            "",
            None,
            "   ",  # Only whitespace
            "a" * 10000,  # Very long query
        ]


def create_search_config_with_backends(
    serpapi_key: Optional[str] = None,
    youcom_key: Optional[str] = None,
    proxy_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a search configuration with specified backend availability."""
    config = {
        "show_snippet": True,
        "enable_fallback": True,
        "preferred_backend": None,
    }

    if proxy_config:
        config["proxy_config"] = proxy_config

    env_manager = EnvironmentManager()

    if serpapi_key:
        env_manager.set("SERPAPI_API_KEY", serpapi_key)
    else:
        env_manager.unset("SERPAPI_API_KEY")

    if youcom_key:
        env_manager.set("YDC_API_KEY", youcom_key)
    else:
        env_manager.unset("YDC_API_KEY")

    return config


# Test fixtures (if pytest is available)
if pytest:
    @pytest.fixture
    def mock_duckduckgo_response():
        """Pytest fixture for mock DuckDuckGo response."""
        return create_mock_duckduckgo_response()

    @pytest.fixture
    def mock_serpapi_response():
        """Pytest fixture for mock SerpAPI response."""
        return create_mock_serpapi_response()

    @pytest.fixture
    def mock_youcom_response():
        """Pytest fixture for mock You.com response."""
        return create_mock_youcom_response()

    @pytest.fixture
    def env_manager():
        """Pytest fixture for environment variable management."""
        manager = EnvironmentManager()
        yield manager
        manager.restore()


# Test constants
TEST_TIMEOUT = 30
MAX_TEST_RESULTS = 10
TEST_RETRY_COUNT = 3