# Web Search API Package

Backend-abstracted web search API with proxy support and automatic fallback.

## 🏗️ Architecture

```
web_search/
├── __init__.py              # Package entry point and convenience functions
├── __version__.py           # Version information
├── api.py                   # Main WebSearchAPI class
├── config.py                # SearchConfig configuration manager
├── constants.py             # Constants and default values
├── utils.py                 # Utility functions
├── web_search_legacy.py     # Legacy compatibility functions
├── README.md               # This file
└── backends/               # Backend implementations
    ├── __init__.py
    ├── base.py             # SearchBackend abstract class
    ├── duckduckgo.py       # DuckDuckGoBackend implementation
    └── serpapi.py          # SerpApiBackend implementation
```

## 🚀 Quick Start

### Basic Usage
```python
from web_search import WebSearchAPI

# Auto-select backend (preferred)
api = WebSearchAPI()
results = api.search_engine_query("Python machine learning")

# Check available backends
api.print_backend_status()
```

### Quick Search
```python
from web_search import quick_search

# Simple one-liner
results = quick_search("AI tools", max_results=5, backend="duckduckgo")
```

### Backend Selection
```python
from web_search import WebSearchAPI

api = WebSearchAPI()

# Force specific backend
results = api.search_engine_query(
    "machine learning",
    backend="serpapi"
)

results = api.search_engine_query(
    "artificial intelligence",
    backend="youcom"
)

results = api.search_engine_query(
    "deep learning",
    backend="duckduckgo",
    use_proxy=True
)
```

### Configuration
```python
from web_search import WebSearchAPI

config = {
    "preferred_backend": "duckduckgo",
    "enable_fallback": True,
    "proxy_config": {
        "host": "brd.superproxy.io",
        "port": 22225,
        "username": "your_username",
        "password": "your_password"
    }
}

api = WebSearchAPI(config)
```

### Advanced Fallback
```python
from web_search import WebSearchAPI

api = WebSearchAPI()

# Try multiple backends in order
results = api.search_with_fallback(
    "artificial intelligence",
    backends=["serpapi", "duckduckgo"],
    use_proxy=True
)
```

## 🔧 Environment Configuration

### SerpAPI (Optional)
```bash
export SERPAPI_API_KEY="your_serpapi_key"
```

### You.com API (Optional)
```bash
export YDC_API_KEY="your_youcom_api_key"
```

### Brightdata Proxy (Optional)
```bash
export BRIGHTDATA_HOST="brd.superproxy.io"
export BRIGHTDATA_PORT="22225"
export BRIGHTDATA_USERNAME="your_username"
export BRIGHTDATA_PASSWORD="your_password"
```

## 🏛️ Backend System

### Available Backends

1. **DuckDuckGoBackend**
   - Direct web scraping
   - Proxy support
   - Always available
   - No API key required

2. **SerpApiBackend**
   - SerpAPI service wrapper
   - Requires API key
   - Higher reliability
   - Handles rate limiting

3. **YouComBackend**
   - You.com search API integration
   - Requires YDC_API_KEY
   - High-quality web and news results
   - No rate limiting issues
   - Fast response times

### Creating Custom Backends

```python
from web_search.backends.base import SearchBackend
from typing import List, Dict, Union

class CustomBackend(SearchBackend):
    @property
    def name(self) -> str:
        return "custom"

    def is_available(self) -> bool:
        return True

    def search(self, keywords: str, max_results: int, region: str, **kwargs) -> Union[List[Dict[str, str]], Dict[str, str]]:
        # Implement your search logic here
        return [{"title": "Result", "href": "https://example.com", "body": "Description"}]
```

## 🔄 Backward Compatibility

The package maintains full backward compatibility with the original `web_search.py`:

```python
# These imports still work exactly as before
from web_search import WebSearchAPI
from web_search import DuckDuckGoBackend, SerpApiBackend
from web_search import fetch_url_content

# Original usage patterns still work
api = WebSearchAPI()
api._load_scenario({"show_snippet": True})
results = api.search_engine_query("query")
content = api.fetch_url_content("https://example.com")
```

## 🎯 Features

- ✅ **Backend Abstraction**: Clean separation of search implementations
- ✅ **Auto Selection**: Intelligent backend selection based on availability
- ✅ **Fallback Logic**: Automatic fallback when primary backend fails
- ✅ **Proxy Support**: Brightdata residential proxy integration
- ✅ **Configuration Management**: Flexible configuration from multiple sources
- ✅ **Legacy Compatibility**: 100% backward compatible
- ✅ **Extensibility**: Easy to add new backends
- ✅ **Error Handling**: Robust error handling and retry logic
- ✅ **Type Hints**: Full type annotation support

## 📦 Package Information

```python
from web_search import __version__
print(__version__)  # "2.0.0"
```

## 🧪 Testing

```bash
# Run the test suite
python test_web_search.py

# Test specific components
python -c "from web_search import WebSearchAPI; api = WebSearchAPI(); api.print_backend_status()"
```

## 🤝 Contributing

When adding new backends:

1. Create a new file in `web_search/backends/`
2. Inherit from `SearchBackend`
3. Implement required methods
4. Add to `web_search/backends/__init__.py`
5. Update `SearchConfig.create_backends()` if needed
6. Add tests

## 📋 API Reference

### WebSearchAPI

- `__init__(config=None)`: Initialize with configuration
- `search_engine_query(keywords, max_results=10, region="wt-wt", use_proxy=None, backend=None)`: Main search method
- `search_with_fallback(keywords, backends=None, **kwargs)`: Multi-backend fallback search
- `get_available_backends()`: Get list of available backends
- `print_backend_status()`: Display backend availability
- `_load_scenario(config)`: Legacy scenario loading

### SearchConfig

- `__init__(config=None)`: Initialize configuration
- `get_available_backends()`: Get available backend names
- `create_backends()`: Create backend instances

### SearchBackend (Abstract)

- `search(keywords, max_results, region, **kwargs)`: Perform search
- `is_available()`: Check availability
- `name`: Backend name (property)