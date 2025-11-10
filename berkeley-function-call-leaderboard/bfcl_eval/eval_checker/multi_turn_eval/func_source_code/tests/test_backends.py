"""Unit tests for search backends."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_search.backends.duckduckgo import DuckDuckGoBackend
from web_search.backends.serpapi import SerpApiBackend
from web_search.backends.youcom import YouComBackend
from web_search.backends.base import SearchBackend

from tests.test_utils import (
    MockResponse, create_mock_duckduckgo_response, create_mock_serpapi_response,
    create_mock_youcom_response, create_mock_serpapi_response_data, EnvironmentManager, BackendTestData
)


class TestDuckDuckGoBackend(unittest.TestCase):
    """Test cases for DuckDuckGoBackend."""

    def setUp(self):
        """Set up test fixtures."""
        self.backend = DuckDuckGoBackend(show_snippet=True)
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_initialization(self):
        """Test backend initialization."""
        backend = DuckDuckGoBackend()
        self.assertEqual(backend.name, "duckduckgo")
        self.assertTrue(backend.is_available())
        self.assertTrue(backend.show_snippet)

    def test_initialization_with_proxy(self):
        """Test backend initialization with proxy configuration."""
        proxy_config = {
            "host": "test.proxy.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_pass"
        }
        backend = DuckDuckGoBackend(proxy_config=proxy_config, show_snippet=False)
        self.assertFalse(backend.show_snippet)
        self.assertEqual(backend.proxy_config, proxy_config)

    def test_get_proxy_dict_with_credentials(self):
        """Test proxy dictionary generation with credentials."""
        proxy_config = {
            "host": "test.proxy.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_pass"
        }
        backend = DuckDuckGoBackend(proxy_config=proxy_config)
        proxy_dict = backend._get_proxy_dict()

        expected_url = "http://test_user:test_pass@test.proxy.com:8080"
        self.assertEqual(proxy_dict["http"], expected_url)
        self.assertEqual(proxy_dict["https"], expected_url)

    def test_get_proxy_dict_without_credentials(self):
        """Test proxy dictionary generation without credentials."""
        proxy_config = {
            "host": "test.proxy.com",
            "port": 8080,
            "username": "",
            "password": ""
        }
        backend = DuckDuckGoBackend(proxy_config=proxy_config)
        proxy_dict = backend._get_proxy_dict()
        self.assertIsNone(proxy_dict)

    @patch('requests.get')
    def test_search_success(self, mock_get):
        """Test successful search."""
        mock_response = Mock()
        mock_response.text = create_mock_duckduckgo_response().text
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.backend.search("test query", 3, "wt-wt")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIn("title", result[0])
        self.assertIn("href", result[0])
        self.assertIn("body", result[0])

    @patch('requests.get')
    def test_search_no_snippet(self, mock_get):
        """Test search without snippets."""
        mock_response = Mock()
        mock_response.text = create_mock_duckduckgo_response().text
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        backend = DuckDuckGoBackend(show_snippet=False)
        result = backend.search("test query", 3, "wt-wt")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIn("title", result[0])
        self.assertIn("href", result[0])
        self.assertNotIn("body", result[0])

    @patch('requests.get')
    def test_search_with_proxy(self, mock_get):
        """Test search with proxy."""
        proxy_config = {
            "host": "test.proxy.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_pass"
        }
        backend = DuckDuckGoBackend(proxy_config=proxy_config)

        mock_response = Mock()
        mock_response.text = create_mock_duckduckgo_response().text
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        backend.search("test query", 3, "wt-wt", use_proxy=True)

        # Verify proxy was used
        expected_proxy = {"http": "http://test_user:test_pass@test.proxy.com:8080", "https": "http://test_user:test_pass@test.proxy.com:8080"}
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs['proxies'], expected_proxy)

    @patch('requests.get')
    def test_search_request_exception(self, mock_get):
        """Test search with request exception."""
        mock_get.side_effect = Exception("Network error")

        result = self.backend.search("test query", 3, "wt-wt")

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Network error", result["error"])

    def test_invalid_parameters(self):
        """Test search with invalid parameters."""
        # Test with None keywords - should handle gracefully
        result = self.backend.search(None, 3, "wt-wt")

        # Should return either error dict or list, but not crash
        self.assertTrue(isinstance(result, dict) or isinstance(result, list))

        if isinstance(result, dict):
            self.assertIn("error", result)  # Should contain error information


class TestSerpApiBackend(unittest.TestCase):
    """Test cases for SerpApiBackend."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_initialization_with_api_key(self):
        """Test backend initialization with API key."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")
        backend = SerpApiBackend()
        self.assertEqual(backend.name, "serpapi")
        self.assertTrue(backend.is_available())
        self.assertEqual(backend.api_key, "test_key")

    def test_initialization_without_api_key(self):
        """Test backend initialization without API key."""
        self.env_manager.unset("SERPAPI_API_KEY")
        backend = SerpApiBackend()
        self.assertEqual(backend.name, "serpapi")
        self.assertFalse(backend.is_available())
        self.assertIsNone(backend.api_key)

    @patch('web_search.backends.serpapi.GoogleSearch')
    def test_search_success(self, mock_search):
        """Test successful search."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")

        # Mock SerpAPI response
        mock_instance = Mock()
        serpapi_data = create_mock_serpapi_response_data()
        mock_instance.get_dict.return_value = serpapi_data
        mock_search.return_value = mock_instance

        backend = SerpApiBackend()
        result = backend.search("test query", 3, "wt-wt")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIn("title", result[0])
        self.assertIn("href", result[0])
        self.assertIn("body", result[0])

    def test_search_no_api_key(self):
        """Test search without API key."""
        self.env_manager.unset("SERPAPI_API_KEY")
        backend = SerpApiBackend()
        result = backend.search("test query", 3, "wt-wt")

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("not configured", result["error"])

    @patch('web_search.backends.serpapi.GoogleSearch')
    def test_search_with_exception(self, mock_search):
        """Test search with SerpAPI exception."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")
        mock_search.side_effect = Exception("SerpAPI error")

        backend = SerpApiBackend()
        result = backend.search("test query", 3, "wt-wt")

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)


class TestYouComBackend(unittest.TestCase):
    """Test cases for YouComBackend."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_initialization_with_api_key(self):
        """Test backend initialization with API key."""
        self.env_manager.set("YDC_API_KEY", "test_key")
        backend = YouComBackend()
        self.assertEqual(backend.name, "youcom")
        self.assertTrue(backend.is_available())
        self.assertEqual(backend.api_key, "test_key")

    def test_initialization_without_api_key(self):
        """Test backend initialization without API key."""
        self.env_manager.unset("YDC_API_KEY")
        backend = YouComBackend()
        self.assertEqual(backend.name, "youcom")
        self.assertFalse(backend.is_available())
        self.assertIsNone(backend.api_key)

    @patch('requests.get')
    def test_search_success(self, mock_get):
        """Test successful search."""
        self.env_manager.set("YDC_API_KEY", "test_key")
        mock_get.return_value = create_mock_youcom_response()

        backend = YouComBackend()
        result = backend.search("test query", 5, "wt-wt")

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("title", result[0])
        self.assertIn("href", result[0])
        self.assertIn("body", result[0])

    def test_search_no_api_key(self):
        """Test search without API key."""
        self.env_manager.unset("YDC_API_KEY")
        backend = YouComBackend()
        result = backend.search("test query", 5, "wt-wt")

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("not configured", result["error"])

    @patch('requests.get')
    def test_search_combined_web_news_results(self, mock_get):
        """Test search with combined web and news results."""
        self.env_manager.set("YDC_API_KEY", "test_key")
        mock_get.return_value = create_mock_youcom_response()

        backend = YouComBackend()
        result = backend.search("test query", 10, "wt-wt")

        self.assertIsInstance(result, list)
        # Should have both web and news results combined
        self.assertGreater(len(result), 0)

    @patch('requests.post')
    def test_get_content_success(self, mock_post):
        """Test content retrieval success."""
        self.env_manager.set("YDC_API_KEY", "test_key")
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"results": [{"url": "content"}]}
        mock_post.return_value = mock_response

        backend = YouComBackend()
        result = backend.get_content(["https://example.com"])

        self.assertIsInstance(result, dict)
        self.assertIn("results", result)
        mock_post.assert_called_once()

    def test_get_content_no_api_key(self):
        """Test content retrieval without API key."""
        self.env_manager.unset("YDC_API_KEY")
        backend = YouComBackend()
        result = backend.get_content(["https://example.com"])

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)


class TestBackendBase(unittest.TestCase):
    """Test cases for backend base class."""

    def test_search_backend_is_abstract(self):
        """Test that SearchBackend cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            SearchBackend()


class TestBackendData(unittest.TestCase):
    """Test cases for backend test data."""

    def test_test_queries(self):
        """Test query generation."""
        queries = BackendTestData.get_test_queries()
        self.assertIsInstance(queries, list)
        self.assertGreater(len(queries), 0)
        self.assertIn("python programming", queries)

    def test_test_regions(self):
        """Test region generation."""
        regions = BackendTestData.get_test_regions()
        self.assertIsInstance(regions, list)
        self.assertGreater(len(regions), 0)
        self.assertIn("wt-wt", regions)
        self.assertIn("us-en", regions)

    def test_invalid_queries(self):
        """Test invalid query generation."""
        invalid_queries = BackendTestData.get_invalid_queries()
        self.assertIsInstance(invalid_queries, list)
        self.assertIn("", invalid_queries)
        self.assertIn(None, invalid_queries)


if __name__ == '__main__':
    unittest.main()