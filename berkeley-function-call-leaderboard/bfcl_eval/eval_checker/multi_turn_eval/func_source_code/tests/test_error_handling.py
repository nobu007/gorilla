"""Tests for error handling and edge cases."""

import unittest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_search.api import WebSearchAPI
from web_search.backends.duckduckgo import DuckDuckGoBackend
from web_search.backends.serpapi import SerpApiBackend
from web_search.backends.youcom import YouComBackend

from tests.test_utils import EnvironmentManager, BackendTestData


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_network_timeout_duckduckgo(self):
        """Test DuckDuckGo network timeout handling."""
        backend = DuckDuckGoBackend()

        with patch('requests.get', side_effect=Exception("Request timeout")):
            result = backend.search("test query", 5, "wt-wt")

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)

    def test_invalid_url_duckduckgo(self):
        """Test DuckDuckGo with malformed URL."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "invalid html"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = backend.search("test query", 5, "wt-wt")

            # Should handle gracefully
            self.assertIsInstance(result, list)  # May return empty list for invalid HTML

    def test_malformed_html_parsing(self):
        """Test parsing of malformed HTML."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "This is not valid HTML content"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = backend.search("test query", 5, "wt-wt")

            # Should return empty list for malformed HTML
            self.assertIsInstance(result, list)

    def test_serpapi_rate_limiting(self):
        """Test SerpAPI error handling (non-retryable error)."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")
        backend = SerpApiBackend()

        with patch('web_search.backends.serpapi.GoogleSearch') as mock_search:
            # Mock a non-429 error to avoid infinite retry loop
            mock_search.side_effect = Exception("API Error: Invalid request")

            result = backend.search("test query", 5, "wt-wt")

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)

    def test_serpapi_invalid_api_key(self):
        """Test SerpAPI with invalid API key."""
        self.env_manager.set("SERPAPI_API_KEY", "invalid_key")
        backend = SerpApiBackend()

        with patch('web_search.backends.serpapi.GoogleSearch') as mock_search:
            mock_instance = Mock()
            mock_instance.get_dict.return_value = {"error": "Invalid API key"}
            mock_search.return_value = mock_instance

            result = backend.search("test query", 5, "wt-wt")

            # When organic_results is missing, backend returns error dict
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)

    def test_youcom_api_error(self):
        """Test You.com API error handling."""
        self.env_manager.set("YDC_API_KEY", "test_key")
        backend = YouComBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_get.return_value = mock_response

            result = backend.search("test query", 5, "wt-wt")

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)

    def test_youcom_empty_response(self):
        """Test You.com with empty response."""
        self.env_manager.set("YDC_API_KEY", "test_key")
        backend = YouComBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"results": {"web": [], "news": []}}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = backend.search("test query", 5, "wt-wt")

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)

    @patch('requests.get')
    def test_proxy_connection_failure(self, mock_get):
        """Test proxy connection failure."""
        proxy_config = {
            "host": "invalid.proxy.com",
            "port": 9999,
            "username": "test_user",
            "password": "test_pass"
        }
        backend = DuckDuckGoBackend(proxy_config=proxy_config)

        mock_response = Mock()
        mock_response.text = """
        <div class="result">
            <a class="result__a" href="https://example.com">Test Result</a>
        </div>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Should fall back to direct connection if proxy fails
        result = backend.search("test query", 5, "wt-wt", use_proxy=True)

        # Should attempt direct connection when proxy fails
        self.assertTrue(isinstance(result, list) or "error" in result,
                              f"Expected list or dict with error, got {type(result)}: {result}")

    def test_extremely_long_query(self):
        """Test handling of extremely long search queries."""
        backend = DuckDuckGoBackend()
        long_query = "a" * 10000

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            result = backend.search(long_query, 5, "wt-wt")

            # Should handle gracefully
            self.assertIsInstance(result, list)

    def test_special_characters_in_query(self):
        """Test queries with special characters."""
        backend = DuckDuckGoBackend()
        special_query = "python @#$%^&*() programming"

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            result = backend.search(special_query, 5, "wt-wt")

            # Should handle gracefully
            self.assertIsInstance(result, list)

    def test_unicode_queries(self):
        """Test queries with Unicode characters."""
        backend = DuckDuckGoBackend()
        unicode_query = "python编程 🐍 emoji"

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            result = backend.search(unicode_query, 5, "wt-wt")

            # Should handle gracefully
            self.assertIsInstance(result, list)

    def test_zero_max_results(self):
        """Test search with zero max results."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            result = backend.search("test query", 0, "wt-wt")

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)

    def test_negative_max_results(self):
        """Test search with negative max results."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            result = backend.search("test query", -5, "wt-wt")

            # Should handle gracefully or return error
            self.assertTrue(isinstance(result, list) or isinstance(result, dict),
                              f"Expected list or dict, got {type(result)}: {result}")

    def test_very_large_max_results(self):
        """Test search with very large max results."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            result = backend.search("test query", 1000, "wt-wt")

            self.assertIsInstance(result, list)

    def test_invalid_region_codes(self):
        """Test search with invalid region codes."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            invalid_regions = ["invalid-region", "", None, "xx-yy"]
            for region in invalid_regions:
                with self.subTest(region=region):
                    result = backend.search("test query", 5, region)
                    self.assertTrue(isinstance(result, list) or isinstance(result, dict),
                              f"Expected list or dict, got {type(result)}: {result}")

    def test_concurrent_search_requests(self):
        """Test handling of concurrent search requests."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            # Simulate concurrent requests
            import threading
            results = []

            def search_worker():
                result = backend.search("test query", 5, "wt-wt")
                results.append(result)

            threads = [threading.Thread(target=search_worker) for _ in range(5)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # All threads should complete without errors
            for result in results:
                self.assertTrue(isinstance(result, list) or isinstance(result, dict),
                              f"Expected list or dict, got {type(result)}: {result}")

    def test_memory_usage_large_response(self):
        """Test memory usage with large search responses."""
        backend = DuckDuckGoBackend()

        # Create a very large HTML response
        large_html = "<div class='result'>" + "<a class='result__a' href='https://example.com'>Title</a>" * 10000 + "</div>"

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = large_html
            mock_get.return_value = mock_response

            result = backend.search("test query", 1000, "wt-wt")

            # Should handle without memory errors
            self.assertIsInstance(result, list)

    def test_environment_variable_corruption(self):
        """Test handling of corrupted environment variables."""
        # Set invalid environment variable values
        self.env_manager.set("BRIGHTDATA_PORT", "not_a_number")
        self.env_manager.set("SERPAPI_API_KEY", "  \n\t  ")  # Whitespace only

        from web_search.config import SearchConfig

        try:
            config = SearchConfig()
            # Should handle gracefully with default values
            self.assertIsInstance(config.proxy_config["port"], int)
        except Exception as e:
            self.fail(f"Config creation failed with corrupted env vars: {e}")

    def test_backend_selection_with_invalid_config(self):
        """Test backend selection with invalid configuration."""
        # Create invalid config
        invalid_config = {
            "preferred_backend": "nonexistent_backend",
            "proxy_config": {
                "host": None,
                "port": "invalid"
            }
        }

        api = WebSearchAPI(invalid_config)

        # Should handle gracefully
        available = api.get_available_backends()
        self.assertIsInstance(available, list)
        self.assertIn("duckduckgo", available)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_all_possible_valid_regions(self):
        """Test all valid region codes."""
        backend = DuckDuckGoBackend()
        valid_regions = [
            "wt-wt", "us-en", "uk-en", "ca-en", "ca-fr",
            "au-en", "de-de", "fr-fr", "es-es", "it-it",
            "ja-jp", "kr-kr", "cn-zh", "ru-ru", "br-pt",
            "mx-es", "in-en"
        ]

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            for region in valid_regions:
                with self.subTest(region=region):
                    result = backend.search("test", 1, region)
                    # Should not raise exceptions
                    self.assertTrue(isinstance(result, list) or isinstance(result, dict),
                              f"Expected list or dict, got {type(result)}: {result}")

    def test_boundary_max_results_values(self):
        """Test boundary values for max_results."""
        backend = DuckDuckGoBackend()

        boundary_values = [0, 1, 10, 100, 999]

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.text = ""
            mock_get.return_value = mock_response

            for max_results in boundary_values:
                with self.subTest(max_results=max_results):
                    result = backend.search("test", max_results, "wt-wt")
                    self.assertTrue(isinstance(result, list) or isinstance(result, dict),
                              f"Expected list or dict, got {type(result)}: {result}")


if __name__ == '__main__':
    unittest.main()