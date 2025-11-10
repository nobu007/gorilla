"""Performance and stress tests for Web Search API."""

import unittest
import time
import threading
import concurrent.futures
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_search.api import WebSearchAPI
from web_search.backends.duckduckgo import DuckDuckGoBackend
from web_search.config import SearchConfig

from tests.test_utils import EnvironmentManager, MockResponse


class TestPerformance(unittest.TestCase):
    """Performance and stress tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    @patch('requests.get')
    def test_search_response_time(self, mock_get):
        """Test search response time is within acceptable limits."""
        mock_response = Mock()
        mock_response.text = """
        <div class="result">
            <a class="result__a" href="https://example.com">Test Result</a>
            <a class="result__snippet">Test snippet</a>
        </div>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        backend = DuckDuckGoBackend()

        start_time = time.time()
        result = backend.search("test query", 10, "wt-wt")
        end_time = time.time()

        response_time = end_time - start_time

        # Response should be under 1 second for mocked response
        self.assertLess(response_time, 1.0, f"Search took {response_time:.2f} seconds, should be under 1.0")
        self.assertIsInstance(result, list)

    def test_multiple_sequential_searches(self):
        """Test multiple sequential searches."""
        search_count = 10

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <div class="result">
                <a class="result__a" href="https://example.com">Test Result</a>
                <a class="result__snippet">Test snippet</a>
            </div>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            backend = DuckDuckGoBackend()
            start_time = time.time()

            results = []
            for i in range(search_count):
                result = backend.search(f"query {i}", 5, "wt-wt")
                results.append(result)

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / search_count

            # Average time per search should be reasonable
            self.assertLess(avg_time, 0.1, f"Average search time {avg_time:.3f}s is too high")
            self.assertEqual(len(results), search_count)

    def test_concurrent_searches(self):
        """Test concurrent search performance."""
        search_count = 20
        thread_count = 5

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <div class="result">
                <a class="result__a" href="https://example.com">Test Result</a>
                <a class="result__snippet">Test snippet</a>
            </div>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            backend = DuckDuckGoBackend()
            results = []
            errors = []

            def search_worker(query_id):
                try:
                    result = backend.search(f"concurrent query {query_id}", 3, "wt-wt")
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(search_worker, i) for i in range(search_count)]
                concurrent.futures.wait(futures, timeout=10)

            end_time = time.time()
            total_time = end_time - start_time

            # Should complete within reasonable time
            self.assertLess(total_time, 5.0, f"Concurrent searches took {total_time:.2f}s")
            self.assertEqual(len(results), search_count)
            self.assertEqual(len(errors), 0)

    def test_memory_usage_large_number_of_backends(self):
        """Test memory usage with large number of backend instances."""
        backend_count = 100

        backends = []
        start_time = time.time()

        for i in range(backend_count):
            backend = DuckDuckGoBackend(show_snippet=(i % 2 == 0))
            backends.append(backend)

        end_time = time.time()
        creation_time = end_time - start_time

        # Backend creation should be fast
        self.assertLess(creation_time, 0.1, f"Creating {backend_count} backends took {creation_time:.3f}s")
        self.assertEqual(len(backends), backend_count)

        # Test that backends are properly garbage collected
        del backends

    def test_config_creation_performance(self):
        """Test configuration creation performance."""
        config_count = 100

        configs = []
        start_time = time.time()

        for i in range(config_count):
            config = SearchConfig({
                "show_snippet": (i % 2 == 0),
                "preferred_backend": "duckduckgo" if (i % 3 == 0) else None,
                "proxy_config": {
                    "host": f"proxy{i % 5}.com",
                    "port": 8000 + (i % 10)
                }
            })
            configs.append(config)

        end_time = time.time()
        creation_time = end_time - start_time

        self.assertLess(creation_time, 0.1, f"Creating {config_count} configs took {creation_time:.3f}s")
        self.assertEqual(len(configs), config_count)

    def test_api_initialization_performance(self):
        """Test API initialization performance."""
        api_count = 50

        apis = []
        start_time = time.time()

        for i in range(api_count):
            api = WebSearchAPI({
                "show_snippet": (i % 2 == 0),
                "enable_fallback": (i % 3 != 0)
            })
            apis.append(api)

        end_time = time.time()
        creation_time = end_time - start_time

        self.assertLess(creation_time, 0.5, f"Creating {api_count} APIs took {creation_time:.3f}s")
        self.assertEqual(len(apis), api_count)

    @patch('requests.get')
    def test_large_response_parsing_performance(self, mock_get):
        """Test performance of parsing large HTML responses."""
        # Create a large HTML response with many results
        large_html = ""
        for i in range(1000):  # 1000 results
            large_html += f"""
            <div class="result">
                <a class="result__a" href="https://example{i}.com">Title {i}</a>
                <a class="result__snippet">Description {i}</a>
            </div>
            """

        mock_response = Mock()
        mock_response.text = large_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        backend = DuckDuckGoBackend()

        start_time = time.time()
        result = backend.search("test query", 1000, "wt-wt")
        end_time = time.time()
        parse_time = end_time - start_time

        self.assertLess(parse_time, 1.0, f"Parsing large response took {parse_time:.3f}s")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1000)

    def test_search_with_different_result_counts(self):
        """Test performance with different result counts."""
        result_counts = [1, 10, 50, 100, 500]

        with patch('requests.get') as mock_get:
            # Create HTML with matching number of results
            def create_response(count):
                html = ""
                for i in range(count):
                    html += f"""
                    <div class="result">
                        <a class="result__a" href="https://example{i}.com">Title {i}</a>
                        <a class="result__snippet">Description {i}</a>
                    </div>
                    """
                return html

            mock_response = Mock()
            mock_response.raise_for_status.return_value = None

            backend = DuckDuckGoBackend()

            performance_data = []

            for count in result_counts:
                mock_response.text = create_response(count)
                mock_get.return_value = mock_response

                start_time = time.time()
                result = backend.search("test query", count, "wt-wt")
                end_time = time.time()

                parse_time = end_time - start_time
                performance_data.append((count, parse_time))

                self.assertIsInstance(result, list)
                self.assertEqual(len(result), count)

            # Performance should scale reasonably
            for count, parse_time in performance_data:
                self.assertLess(parse_time, 0.5, f"Parsing {count} results took {parse_time:.3f}s")

    def test_backend_selection_performance(self):
        """Test backend selection performance."""
        self.env_manager.set("SERPAPI_API_KEY", "test_key")
        self.env_manager.set("YDC_API_KEY", "test_key")

        api = WebSearchAPI()
        selection_count = 1000

        start_time = time.time()
        for i in range(selection_count):
            backend = api._select_backend(None)  # Auto selection
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / selection_count

        self.assertLess(avg_time, 0.001, f"Backend selection took {avg_time:.6f}s per call")

    def test_error_handling_performance(self):
        """Test that error handling doesn't significantly impact performance."""
        backend = DuckDuckGoBackend()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "invalid html"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            error_count = 100
            start_time = time.time()

            results = []
            for i in range(error_count):
                result = backend.search("test query", 5, "wt-wt")
                results.append(result)

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / error_count

            self.assertLess(avg_time, 0.01, f"Error handling took {avg_time:.4f}s per call")
            self.assertEqual(len(results), error_count)

    def test_fallback_performance(self):
        """Test fallback mechanism performance."""
        self.env_manager.set("YDC_API_KEY", "test_key")

        api = WebSearchAPI()

        # Mock backends that simulate fallback scenarios
        from unittest.mock import Mock
        from web_search.backends import YouComBackend

        ddg_backend = Mock(spec=DuckDuckGoBackend)
        ddg_backend.name = "duckduckgo"
        ddg_backend.is_available.return_value = True
        ddg_backend.search.return_value = [{"title": "DDG Result", "href": "https://ddg.com"}]

        youcom_backend = Mock(spec=YouComBackend)
        youcom_backend.name = "youcom"
        youcom_backend.is_available.return_value = False  # Will trigger fallback
        youcom_backend.search.return_value = {"error": "You.com unavailable"}

        api.backends = {
            "duckduckgo": ddg_backend,
            "youcom": youcom_backend
        }

        start_time = time.time()
        result = api.search_engine_query("test query")
        end_time = time.time()

        fallback_time = end_time - start_time

        self.assertLess(fallback_time, 0.1, f"Fallback took {fallback_time:.3f}s")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "DDG Result")


class TestStressTests(unittest.TestCase):
    """Stress tests for Web Search API."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_high_volume_search_requests(self):
        """Test high volume of search requests."""
        request_count = 500

        with patch('requests.get') as mock_get:
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

            start_time = time.time()
            successful_requests = 0
            failed_requests = 0

            for i in range(request_count):
                try:
                    result = api.search_engine_query(f"query {i}", 1, "wt-wt")
                    if isinstance(result, list):
                        successful_requests += 1
                    else:
                        failed_requests += 1
                except Exception:
                    failed_requests += 1

            end_time = time.time()
            total_time = end_time - start_time

            success_rate = successful_requests / request_count
            avg_time_per_request = total_time / request_count

            self.assertGreaterEqual(success_rate, 0.99, f"Success rate {success_rate:.2%} too low")
            self.assertLess(avg_time_per_request, 0.01, f"Average time {avg_time_per_request:.4f}s too high")
            self.assertEqual(failed_requests, 0)

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended usage."""
        import gc
        import psutil
        import os

        # Skip if psutil is not available
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
        except ImportError:
            self.skip("psutil not available for memory leak detection")
            return

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <div class="result">
                <a class="result__a" href="https://example.com">Test Result</a>
                <a class="result__snippet">Test snippet</a>
            </div>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            backend = DuckDuckGoBackend()

            # Perform many searches
            for i in range(1000):
                result = backend.search(f"test query {i}", 5, "wt-wt")
                # Force garbage collection
                if i % 100 == 0:
                    gc.collect()

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)

            # Memory increase should be reasonable (less than 50MB)
            self.assertLess(memory_increase_mb, 50, f"Memory increased by {memory_increase_mb:.1f}MB")


if __name__ == '__main__':
    unittest.main()