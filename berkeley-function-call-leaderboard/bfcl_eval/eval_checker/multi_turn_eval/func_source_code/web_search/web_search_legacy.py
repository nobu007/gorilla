"""Legacy WebSearch functions for backward compatibility."""

import html2text
import requests
from bs4 import BeautifulSoup

from .constants import DEFAULT_REQUEST_TIMEOUT


def fetch_url_content(url: str, mode: str = "raw") -> dict:
    """
    This function retrieves content from the provided URL and processes it based on the selected mode.

    Legacy function maintained for backward compatibility.

    Args:
        url (str): The URL to fetch content from. Must start with 'http://' or 'https://'.
        mode (str, optional): The mode to process the fetched content. Defaults to "raw".
            Supported modes are:
                - "raw": Returns the raw HTML content.
                - "markdown": Converts raw HTML content to Markdown format for better readability, using html2text.
                - "truncate": Extracts and cleans text by removing scripts, styles, and extraneous whitespace.

    Returns:
        dict: Dictionary with either 'content' key or 'error' key
    """
    if not url.startswith(("http://", "https://")):
        return {"error": f"Invalid URL: {url}"}

    try:
        # A header that mimics a browser request. This helps avoid 403 Forbidden errors.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
        }
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()

        # Process the response based on the mode
        if mode == "raw":
            return {"content": response.text}

        elif mode == "markdown":
            converter = html2text.HTML2Text()
            markdown = converter.handle(response.text)
            return {"content": markdown}

        elif mode == "truncate":
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            # Extract and clean text
            text = soup.get_text(separator="\n", strip=True)
            return {"content": text}
        else:
            return {"error": f"Unsupported mode: {mode}"}

    except Exception as e:
        return {"error": f"An error occurred while fetching {url}: {str(e)}"}


def _fake_requests_get_error_msg(url: str, rng) -> str:
    """
    Legacy error message generation function.
    Maintained for backward compatibility but deprecated.
    """
    from .utils import generate_fake_error
    return generate_fake_error(url, rng)