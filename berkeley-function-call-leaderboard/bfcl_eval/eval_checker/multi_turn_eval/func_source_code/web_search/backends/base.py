"""Base abstract class for search backends."""

from abc import ABC, abstractmethod
from typing import List, Dict, Union


class SearchBackend(ABC):
    """Abstract base class for search backends."""

    @abstractmethod
    def search(self, keywords: str, max_results: int, region: str, **kwargs) -> Union[List[Dict[str, str]], Dict[str, str]]:
        """
        Perform search and return results.

        Args:
            keywords: Search query string
            max_results: Maximum number of results to return
            region: Search region code
            **kwargs: Additional backend-specific parameters

        Returns:
            List of result dicts for success, or dict with 'error' key for failure.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is properly configured and available."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return backend name."""
        pass