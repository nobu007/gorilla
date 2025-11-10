"""Integration tests for WebSearchAPI."""

import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_search.api import WebSearchAPI
from web_search.config import SearchConfig
from web_search.backends import DuckDuckGoBackend, SerpApiBackend, YouComBackend

from tests.test_utils import (
    MockResponse, EnvironmentManager, BackendTestData
)


class TestWebSearchAPI(unittest.TestCase):
    """Integration tests for WebSearchAPI."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_initialization_no_config(self):
        """Test API initialization without configuration."""
        api = WebSearchAPI()

        self.assertIsInstance(api.config, SearchConfig)
        self.assertIsInstance(api.backends, dict)
        self.assertIn("duckduckgo", api.backends)
        self.assertIn("youcom", api.backends)

    def test_initialization_with_config(self):
        """Test API initialization with configuration."""
        config = {
            "show_snippet": False,
            "preferred_backend": "duckduckgo",
            "enable_fallback": False
        }

        api = WebSearchAPI(config)

        self.assertFalse(api.show_snippet)
        self.assertEqual(api.config.preferred_backend, "duckduckgo")
        self.assertFalse(api.config.enable_fallback)

    def test_get_available_backends(self):
        """Test getting available backends."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")

        api = WebSearchAPI()
        available = api.get_available_backends()

        self.assertIsInstance(available, list)
        self.assertIn("duckduckgo", available)
        self.assertIn("serpapi", available)

    def test_print_backend_status(self):
        """Test backend status printing."""
        api = WebSearchAPI()

        # This should not raise an exception
        try:
            api.print_backend_status()
        except Exception as e:
            self.fail(f"print_backend_status raised {e}")

    @patch('requests.get')
    def test_search_engine_query_auto_selection_duckduckgo(self, mock_get):
        """Test auto selection falling back to DuckDuckGo."""
        # Ensure no API keys are set
        self.env_manager.unset("SERPAPI_API_KEY")
        self.env_manager.unset("YDC_API_KEY")

        mock_response = Mock()
        mock_response.text = """
        <div class="result">
            <a class="result__a" href="https://example.com">Test Result</a>
            <a class="result__snippet">Test snippet</a>
        </div>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = WebSearchAPI()
        result = api.search_engine_query("test query", 1)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test Result")

    def test_search_engine_query_explicit_backend_unavailable(self):
        """Test explicit backend selection when backend is not available."""
        self.env_manager.unset("SERPAPI_API_KEY")

        api = WebSearchAPI()
        result = api.search_engine_query("test query", backend="serpapi")

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("not available", result["error"])

    @patch('web_search.backends.serpapi.GoogleSearch')
    def test_search_engine_query_explicit_serpapi_success(self, mock_search):
        """Test explicit SerpAPI backend selection success."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")

        # Mock SerpAPI response
        mock_instance = Mock()
        mock_instance.get_dict.return_value = {
            "organic_results": [
                {"title": "Test Result", "link": "https://example.com", "snippet": "Test snippet"}
            ]
        }
        mock_search.return_value = mock_instance

        api = WebSearchAPI()
        result = api.search_engine_query("test query", backend="serpapi")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test Result")

    @patch('requests.get')
    def test_search_engine_query_explicit_youcom_success(self, mock_get):
        """Test explicit You.com backend selection success."""
        self.env_manager.set("YDC_API_KEY", "test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "web": [
                    {"title": "Test Result", "url": "https://example.com", "snippet": "Test snippet"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = WebSearchAPI()
        result = api.search_engine_query("test query", backend="youcom")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test Result")

    def test_search_engine_query_invalid_parameters(self):
        """Test search with invalid parameters."""
        api = WebSearchAPI()

        # Test with None keywords - should handle gracefully
        result = api.search_engine_query(None, 1)
        # Should return either error dict or empty list, but not crash
        self.assertTrue(isinstance(result, dict) or isinstance(result, list))

    @patch('requests.get')
    def test_search_with_fallback_success(self, mock_get):
        """Test search with fallback to multiple backends."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")

        api = WebSearchAPI()

        # Create mock backends for testing
        ddg_backend = Mock(spec=DuckDuckGoBackend)
        ddg_backend.name = "duckduckgo"
        ddg_backend.is_available.return_value = True
        ddg_backend.search.return_value = [{"title": "DuckDuckGo Result", "href": "https://ddg.com"}]

        serpapi_backend = Mock(spec=SerpApiBackend)
        serpapi_backend.name = "serpapi"
        serpapi_backend.is_available.return_value = False  # Simulate failure

        youcom_backend = Mock(spec=YouComBackend)
        youcom_backend.name = "youcom"
        youcom_backend.is_available.return_value = True
        youcom_backend.search.return_value = [{"title": "You.com Result", "href": "https://you.com"}]

        # Replace backends with mocks
        api.backends = {
            "duckduckgo": ddg_backend,
            "serpapi": serpapi_backend,
            "youcom": youcom_backend
        }

        result = api.search_with_fallback(
            "test query",
            backends=["serpapi", "youcom", "duckduckgo"]
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        # Should succeed with youcom (first available)
        self.assertEqual(result[0]["title"], "You.com Result")

    @patch('requests.get')
    def test_search_with_fallback_all_fail(self, mock_get):
        """Test search with fallback when all backends fail."""
        api = WebSearchAPI()

        # Create mock backends that all fail
        ddg_backend = Mock(spec=DuckDuckGoBackend)
        ddg_backend.name = "duckduckgo"
        ddg_backend.is_available.return_value = True
        ddg_backend.search.return_value = {"error": "DuckDuckGo failed"}

        youcom_backend = Mock(spec=YouComBackend)
        youcom_backend.name = "youcom"
        youcom_backend.is_available.return_value = True
        youcom_backend.search.return_value = {"error": "You.com failed"}

        api.backends = {
            "duckduckgo": ddg_backend,
            "youcom": youcom_backend
        }

        result = api.search_with_fallback(
            "test query",
            backends=["duckduckgo", "youcom"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("All backends failed", result["error"])

    def test_load_scenario_legacy_compatibility(self):
        """Test legacy scenario loading for backward compatibility."""
        api = WebSearchAPI()

        scenario_config = {
            "show_snippet": False,
            "proxy_config": {
                "host": "legacy.proxy.com"
            }
        }

        api._load_scenario(scenario_config)

        self.assertFalse(api.show_snippet)
        self.assertEqual(api.config.proxy_config["host"], "legacy.proxy.com")

    @patch('requests.get')
    def test_fetch_url_content_legacy(self, mock_get):
        """Test legacy fetch_url_content method."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = WebSearchAPI()
        result = api.fetch_url_content("https://example.com", mode="raw")

        self.assertIsInstance(result, dict)
        self.assertIn("content", result)
        self.assertIn("Test content", result["content"])

    def test_fake_requests_get_error_msg_legacy(self):
        """Test legacy error message generation."""
        api = WebSearchAPI()
        error_msg = api._fake_requests_get_error_msg("https://example.com")

        self.assertIsInstance(error_msg, str)
        self.assertGreater(len(error_msg), 0)

    @patch('requests.get')
    def test_search_engine_query_proxy_auto_detect(self, mock_get):
        """Test proxy auto-detection in search."""
        # Set up proxy config
        self.env_manager.set("BRIGHTDATA_USERNAME", "test_user")
        self.env_manager.set("BRIGHTDATA_PASSWORD", "test_pass")

        config = {
            "proxy_config": {
                "host": "test.proxy.com",
                "port": 8080
            }
        }

        api = WebSearchAPI(config)

        mock_response = Mock()
        mock_response.text = """
        <div class="result">
            <a class="result__a" href="https://example.com">Test Result</a>
        </div>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test auto proxy detection for DuckDuckGo
        result = api.search_engine_query("test query", backend="duckduckgo")

        # Verify proxy was used
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        self.assertIsNotNone(call_kwargs.get('proxies'))

    def test_backend_priority_selection(self):
        """Test backend selection priority logic."""
        # Set all API keys
        self.env_manager.set("SERPAPI_API_KEY", "serpapi_key")
        self.env_manager.set("YDC_API_KEY", "youcom_key")

        api = WebSearchAPI()

        # Should prefer SerpAPI when no specific backend is requested
        selected = api._select_backend(None)
        self.assertEqual(selected.name, "serpapi")

        # Test explicit selection
        selected = api._select_backend("youcom")
        self.assertEqual(selected.name, "youcom")

        selected = api._select_backend("duckduckgo")
        self.assertEqual(selected.name, "duckduckgo")

    def test_preferred_backend_config(self):
        """Test preferred backend configuration."""
        self.env_manager.set("YDC_API_KEY", "youcom_key")

        config = {"preferred_backend": "youcom"}
        api = WebSearchAPI(config)

        selected = api._select_backend(None)
        self.assertEqual(selected.name, "youcom")

    @patch('requests.get')
    def test_search_engine_query_parameters_validation(self, mock_get):
        """Test parameter validation in search queries."""
        mock_response = Mock()
        mock_response.text = """
        <div class="result">
            <a class="result__a" href="https://example.com">Test Result</a>
            <a class="result__snippet">Test snippet</a>
        </div>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = WebSearchAPI()

        # Test different parameter combinations - explicitly use DuckDuckGo to avoid fallback
        result = api.search_engine_query(
            keywords="test query",
            max_results=5,
            region="us-en",
            use_proxy=False,
            backend="duckduckgo"  # Explicitly specify backend to avoid fallback
        )

        self.assertIsInstance(result, list)
        mock_get.assert_called_once()

        # Verify request parameters
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['q'], "test query")
        self.assertEqual(call_args[1]['timeout'], 15)


if __name__ == '__main__':
    unittest.main()