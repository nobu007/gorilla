"""Utility functions for the Web Search API."""

import random
from urllib.parse import urlparse

from .constants import ERROR_TEMPLATES


def generate_fake_error(url: str, rng: random.Random) -> str:
    """
    Generate a realistic-looking requests/urllib3 error message.

    Args:
        url: The URL that would have caused the error
        rng: Random number generator instance

    Returns:
        Realistic-looking error message
    """
    parsed = urlparse(url)

    context = {
        "url": url,
        "host": parsed.hostname or "unknown",
        "path": parsed.path or "/",
        "id1": rng.randrange(0x10000000, 0xFFFFFFFF),
        "id2": rng.randrange(0x10000000, 0xFFFFFFFF),
    }

    template = rng.choice(ERROR_TEMPLATES)
    return template.format(**context)