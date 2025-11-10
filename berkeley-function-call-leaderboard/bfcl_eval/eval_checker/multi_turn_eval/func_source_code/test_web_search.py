#!/usr/bin/env python3
"""
Test script for the refactored WebSearchAPI functionality.
Tests both backend selection and actual search functionality.
"""

import os
import sys
import time
from typing import Dict, Any

# Import the new web search functionality
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from web_search import WebSearchAPI, SearchConfig, DuckDuckGoBackend, SerpApiBackend, YouComBackend
    NEW_STRUCTURE_AVAILABLE = True
except ImportError:
    # Fallback to old structure if new structure is not available
    try:
        from web_search import WebSearchAPI, DuckDuckGoBackend, SerpApiBackend
        YouComBackend = None  # Not available in old structure
        NEW_STRUCTURE_AVAILABLE = False
    except ImportError:
        # If even old structure doesn't work, exit
        print("Error: Cannot import web_search functionality")
        sys.exit(1)


def test_backend_initialization():
    """Test basic backend initialization and availability."""
    print("🧪 Testing Backend Initialization")
    print("=" * 50)

    # Create API instance
    api = WebSearchAPI()

    # Check backend status
    api.print_backend_status()

    # Check available backends
    available = api.get_available_backends()
    print(f"\n✅ Available backends: {available}")
    print(f"✅ Total backends: {len(api.backends)}")

    assert len(available) > 0


def test_basic_duckduckgo_search():
    """Test basic DuckDuckGo search functionality."""
    print("\n🦆 Testing DuckDuckGo Search")
    print("=" * 50)

    try:
        # Create backend instance
        backend = DuckDuckGoBackend()

        # Perform a simple search
        print("Searching for 'Python programming'...")
        result = backend.search(
            keywords="Python programming",
            max_results=3,
            region="wt-wt",
            use_proxy=False  # No proxy for basic test
        )

        if isinstance(result, dict) and "error" in result:
            print(f"❌ Search failed: {result['error']}")
            assert False

        if isinstance(result, list):
            print(f"✅ Search successful! Found {len(result)} results:")
            for i, item in enumerate(result, 1):
                print(f"  {i}. {item.get('title', 'No title')}")
                print(f"     URL: {item.get('href', 'No URL')}")
                if 'body' in item:
                    snippet = item['body'][:100] + "..." if len(item['body']) > 100 else item['body']
                    print(f"     Snippet: {snippet}")
                print()

        assert True

    except Exception as e:
        print(f"❌ DuckDuckGo test failed with exception: {e}")
        assert False


def test_auto_selection():
    """Test automatic backend selection logic."""
    print("🤖 Testing Auto Backend Selection")
    print("=" * 50)

    try:
        api = WebSearchAPI()

        # Test auto selection
        print("Testing auto selection for query 'machine learning'...")
        result = api.search_engine_query(
            keywords="machine learning",
            max_results=2
        )

        if isinstance(result, dict) and "error" in result:
            print(f"❌ Auto selection failed: {result['error']}")
            assert False

        if isinstance(result, list):
            print(f"✅ Auto selection successful! Found {len(result)} results:")
            for i, item in enumerate(result, 1):
                print(f"  {i}. {item.get('title', 'No title')}")

        assert True

    except Exception as e:
        print(f"❌ Auto selection test failed: {e}")
        assert False


def test_explicit_backend_selection():
    """Test explicit backend selection."""
    print("🎯 Testing Explicit Backend Selection")
    print("=" * 50)

    try:
        api = WebSearchAPI()

        # Test explicit DuckDuckGo selection
        print("Testing explicit DuckDuckGo selection...")
        result = api.search_engine_query(
            keywords="artificial intelligence",
            max_results=2,
            backend="duckduckgo",
            use_proxy=False
        )

        if isinstance(result, dict) and "error" in result:
            print(f"❌ DuckDuckGo selection failed: {result['error']}")
            assert False

        if isinstance(result, list):
            print(f"✅ DuckDuckGo selection successful! Found {len(result)} results")
            for i, item in enumerate(result, 1):
                print(f"  {i}. {item.get('title', 'No title')}")

        assert True

    except Exception as e:
        print(f"❌ Explicit selection test failed: {e}")
        assert False


def test_configuration_system():
    """Test the configuration system."""
    print("\n⚙️ Testing Configuration System")
    print("=" * 50)

    try:
        # Test with custom config
        config = {
            "show_snippet": True,
            "preferred_backend": "duckduckgo",
            "enable_fallback": True,
            "proxy_config": {
                "host": "test.proxy.com",
                "port": 8080,
                "username": "test_user",
                "password": "test_pass"
            }
        }

        api = WebSearchAPI(config)
        print(f"✅ Custom config loaded successfully")
        print(f"✅ Show snippets: {api.config.show_snippet}")
        print(f"✅ Preferred backend: {api.config.preferred_backend}")
        print(f"✅ Fallback enabled: {api.config.enable_fallback}")

        # Test proxy config
        proxy_config = api.config.proxy_config
        print(f"✅ Proxy host: {proxy_config.get('host')}")
        print(f"✅ Proxy port: {proxy_config.get('port')}")

        assert True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        assert False


def test_legacy_compatibility():
    """Test backward compatibility with existing interface."""
    print("\n🔄 Testing Legacy Compatibility")
    print("=" * 50)

    try:
        api = WebSearchAPI()

        # Test legacy scenario loading
        legacy_config = {"show_snippet": False}
        api._load_scenario(legacy_config)

        print(f"✅ Legacy scenario loading successful")
        print(f"✅ Show snippets updated: {api.show_snippet}")

        # Test with legacy-style call
        result = api.search_engine_query(
            keywords="software development",
            max_results=2
        )

        if isinstance(result, dict) and "error" in result:
            print(f"❌ Legacy compatibility test failed: {result['error']}")
            assert False

        if isinstance(result, list):
            print(f"✅ Legacy compatibility successful! Found {len(result)} results")

        assert True

    except Exception as e:
        print(f"❌ Legacy compatibility test failed: {e}")
        assert False


def test_youcom_backend():
    """Test You.com backend initialization and basic functionality."""
    print("\n🔍 Testing You.com Backend")
    print("=" * 50)

    if YouComBackend is None:
        print("⚠️ You.com backend not available in this version")
        assert True

    try:
        # Create backend instance
        backend = YouComBackend()

        # Check availability
        available = backend.is_available()
        print(f"✅ You.com backend created successfully")
        print(f"✅ Available: {available}")

        if available:
            # Try a simple search
            print("Testing search...")
            result = backend.search(
                keywords="artificial intelligence",
                max_results=2,
                region="wt-wt"
            )

            if isinstance(result, dict) and "error" in result:
                print(f"❌ Search failed: {result['error']}")
                assert False

            if isinstance(result, list):
                print(f"✅ Search successful! Found {len(result)} results")
                for i, item in enumerate(result, 1):
                    print(f"  {i}. {item.get('title', 'No title')}")
        else:
            print("⚠️ You.com API key not configured, skipping search test")

        assert True

    except Exception as e:
        print(f"❌ You.com test failed with exception: {e}")
        assert False


def main():
    """Run all tests."""
    print("🚀 Starting Web Search API Tests")
    print("=" * 80)

    tests = [
        ("Backend Initialization", test_backend_initialization),
        ("Basic DuckDuckGo Search", test_basic_duckduckgo_search),
        ("Auto Selection", test_auto_selection),
        ("Explicit Backend Selection", test_explicit_backend_selection),
        ("You.com Backend", test_youcom_backend),
        ("Configuration System", test_configuration_system),
        ("Legacy Compatibility", test_legacy_compatibility),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

        # Small delay between tests
        time.sleep(1)

    print(f"\n{'='*80}")
    print(f"🏁 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())