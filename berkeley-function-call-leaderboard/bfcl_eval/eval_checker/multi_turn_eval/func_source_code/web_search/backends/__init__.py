"""Backend implementations for the Web Search API."""

from .base import SearchBackend
from .duckduckgo import DuckDuckGoBackend
from .serpapi import SerpApiBackend
from .youcom import YouComBackend

__all__ = [
    "SearchBackend",
    "DuckDuckGoBackend",
    "SerpApiBackend",
    "YouComBackend",
]