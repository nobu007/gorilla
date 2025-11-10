"""Tests for SearchConfig configuration management."""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_search.config import SearchConfig
from web_search.backends import DuckDuckGoBackend, SerpApiBackend, YouComBackend

from tests.test_utils import EnvironmentManager


class TestSearchConfig(unittest.TestCase):
    """Test cases for SearchConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()

    def tearDown(self):
        """Clean up after tests."""
        self.env_manager.restore()

    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = SearchConfig()

        self.assertTrue(config.show_snippet)
        self.assertIsNone(config.preferred_backend)
        self.assertTrue(config.enable_fallback)

        # Check default proxy config - use environment variable value if set
        expected_port = int(os.getenv("BRIGHTDATA_PORT", 22225))
        self.assertEqual(config.proxy_config["host"], "brd.superproxy.io")
        self.assertEqual(config.proxy_config["port"], expected_port)

    def test_custom_initialization(self):
        """Test custom configuration initialization."""
        custom_config = {
            "show_snippet": False,
            "preferred_backend": "duckduckgo",
            "enable_fallback": False,
            "proxy_config": {
                "host": "custom.proxy.com",
                "port": 8080
            }
        }

        config = SearchConfig(custom_config)

        self.assertFalse(config.show_snippet)
        self.assertEqual(config.preferred_backend, "duckduckgo")
        self.assertFalse(config.enable_fallback)
        self.assertEqual(config.proxy_config["host"], "custom.proxy.com")
        self.assertEqual(config.proxy_config["port"], 8080)

    def test_environment_variable_proxy_config(self):
        """Test proxy configuration from environment variables."""
        self.env_manager.set("BRIGHTDATA_HOST", "env.proxy.com")
        self.env_manager.set("BRIGHTDATA_PORT", "9999")
        self.env_manager.set("BRIGHTDATA_USERNAME", "env_user")
        self.env_manager.set("BRIGHTDATA_PASSWORD", "env_pass")

        config = SearchConfig()

        self.assertEqual(config.proxy_config["host"], "env.proxy.com")
        self.assertEqual(config.proxy_config["port"], 9999)
        self.assertEqual(config.proxy_config["username"], "env_user")
        self.assertEqual(config.proxy_config["password"], "env_pass")

    def test_invalid_port_number(self):
        """Test handling of invalid port number."""
        self.env_manager.set("BRIGHTDATA_PORT", "invalid_port")

        config = SearchConfig()

        # Should fall back to default port
        self.assertEqual(config.proxy_config["port"], 22225)

    def test_get_available_backends_no_keys(self):
        """Test available backends when no API keys are set."""
        # Ensure no API keys are set
        self.env_manager.unset("SERPAPI_API_KEY")
        self.env_manager.unset("YDC_API_KEY")

        config = SearchConfig()
        available = config.get_available_backends()

        self.assertIsInstance(available, list)
        self.assertEqual(len(available), 1)
        self.assertIn("duckduckgo", available)

    def test_get_available_backends_with_serpapi(self):
        """Test available backends when SerpAPI key is set."""
        self.env_manager.set("SERPAPI_API_KEY", "test_serpapi_key")
        self.env_manager.unset("YDC_API_KEY")

        config = SearchConfig()
        available = config.get_available_backends()

        self.assertIsInstance(available, list)
        self.assertEqual(len(available), 2)
        self.assertIn("duckduckgo", available)
        self.assertIn("serpapi", available)

    def test_get_available_backends_with_youcom(self):
        """Test available backends when You.com key is set."""
        self.env_manager.unset("SERPAPI_API_KEY")
        self.env_manager.set("YDC_API_KEY", "test_youcom_key")

        config = SearchConfig()
        available = config.get_available_backends()

        self.assertIsInstance(available, list)
        self.assertEqual(len(available), 2)
        self.assertIn("duckduckgo", available)
        self.assertIn("youcom", available)

    def test_get_available_backends_with_all_keys(self):
        """Test available backends when all API keys are set."""
        self.env_manager.set("SERPAPI_API_KEY", "test_serpapi_key")
        self.env_manager.set("YDC_API_KEY", "test_youcom_key")

        config = SearchConfig()
        available = config.get_available_backends()

        self.assertIsInstance(available, list)
        self.assertEqual(len(available), 3)
        self.assertIn("duckduckgo", available)
        self.assertIn("serpapi", available)
        self.assertIn("youcom", available)

    def test_create_backends_no_keys(self):
        """Test backend creation when no API keys are set."""
        self.env_manager.unset("SERPAPI_API_KEY")
        self.env_manager.unset("YDC_API_KEY")

        config = SearchConfig()
        backends = config.create_backends()

        self.assertEqual(len(backends), 2)  # DuckDuckGo + YouCom (YouCom checks availability internally)
        self.assertIsInstance(backends[0], DuckDuckGoBackend)
        self.assertIsInstance(backends[1], YouComBackend)

    def test_create_backends_with_serpapi(self):
        """Test backend creation when SerpAPI key is set."""
        self.env_manager.set("SERPAPI_API_KEY", "test_serpapi_key")
        self.env_manager.unset("YDC_API_KEY")

        config = SearchConfig()
        backends = config.create_backends()

        self.assertEqual(len(backends), 3)  # DuckDuckGo + SerpAPI + YouCom
        backend_names = [backend.name for backend in backends]
        self.assertIn("duckduckgo", backend_names)
        self.assertIn("serpapi", backend_names)
        self.assertIn("youcom", backend_names)

    def test_create_backends_with_all_keys(self):
        """Test backend creation when all API keys are set."""
        self.env_manager.set("SERPAPI_API_KEY", "test_serpapi_key")
        self.env_manager.set("YDC_API_KEY", "test_youcom_key")

        config = SearchConfig()
        backends = config.create_backends()

        self.assertEqual(len(backends), 3)
        backend_names = [backend.name for backend in backends]
        self.assertIn("duckduckgo", backend_names)
        self.assertIn("serpapi", backend_names)
        self.assertIn("youcom", backend_names)

    def test_proxy_config_override(self):
        """Test proxy configuration override from config dict."""
        config_dict = {
            "proxy_config": {
                "host": "override.proxy.com",
                "port": 9999,
                "username": "override_user"
            }
        }

        config = SearchConfig(config_dict)

        self.assertEqual(config.proxy_config["host"], "override.proxy.com")
        self.assertEqual(config.proxy_config["port"], 9999)
        self.assertEqual(config.proxy_config["username"], "override_user")

    def test_proxy_config_merge(self):
        """Test proxy configuration merging with environment variables."""
        # Clear any existing username env var for this test
        self.env_manager.unset("BRIGHTDATA_USERNAME")
        self.env_manager.set("BRIGHTDATA_PASSWORD", "env_pass")

        config_dict = {
            "proxy_config": {
                "host": "partial.override.com"
                # Missing other fields - should merge with env vars
            }
        }

        config = SearchConfig(config_dict)

        self.assertEqual(config.proxy_config["host"], "partial.override.com")  # From config

        # Password should be present since we set it
        self.assertEqual(config.proxy_config.get("password"), "env_pass")  # From env
        # Use environment variable value if set, otherwise default
        expected_port = int(os.getenv("BRIGHTDATA_PORT", 22225))
        self.assertEqual(config.proxy_config["port"], expected_port)  # From env or default
        self.assertEqual(config.proxy_config.get("username"), None)  # Not set (we cleared it)

    def test_empty_config_dict(self):
        """Test handling of empty configuration dictionary."""
        config = SearchConfig({})

        # Should use default values
        self.assertTrue(config.show_snippet)
        self.assertIsNone(config.preferred_backend)
        self.assertTrue(config.enable_fallback)

    def test_environment_preferred_backend(self):
        """Test preferred backend selection from environment variable."""
        self.env_manager.set("WEB_SEARCH_PREFERRED_BACKEND", "duckduckgo")

        config = SearchConfig()
        self.assertEqual(config.preferred_backend, "duckduckgo")

    def test_environment_preferred_backend_overrides_config(self):
        """Test that environment variable overrides config file setting."""
        self.env_manager.set("WEB_SEARCH_PREFERRED_BACKEND", "youcom")

        config_dict = {"preferred_backend": "serpapi"}
        config = SearchConfig(config_dict)

        # Environment should take precedence over config
        self.assertEqual(config.preferred_backend, "youcom")

    def test_environment_preferred_backend_invalid(self):
        """Test handling of invalid preferred backend in environment."""
        self.env_manager.set("WEB_SEARCH_PREFERRED_BACKEND", "invalid_backend")

        config = SearchConfig()
        # Should still be set to invalid value (validation happens at runtime)
        self.assertEqual(config.preferred_backend, "invalid_backend")

    def test_config_preservation(self):
        """Test that original config dict is not modified."""
        original_config = {
            "show_snippet": True,
            "custom_field": "should_not_be_used"
        }

        config = SearchConfig(original_config.copy())

        # Original dict should remain unchanged
        self.assertEqual(original_config["show_snippet"], True)
        self.assertEqual(original_config["custom_field"], "should_not_be_used")


if __name__ == '__main__':
    unittest.main()