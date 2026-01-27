"""HTTP utilities for making API requests with rate limiting and error handling."""

import time
import logging
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logger = logging.getLogger(__name__)

def create_session():
    """Create a requests session with retry mechanism"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Global session
session = create_session()

class RateLimiter:
    """Simple rate limiter to prevent overloading APIs"""
    def __init__(self, calls_per_second: float = 3.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0
        
    def wait(self):
        """Wait if necessary to comply with rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_call_time = time.time()

def make_api_request(url: str, params: Dict[str, Any], limiter: RateLimiter, 
                    headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
    """
    Make an API request with rate limiting, retries and caching
    
    Args:
        url: The URL to request
        params: Query parameters
        limiter: RateLimiter instance
        headers: Optional HTTP headers
        
    Returns:
        Response object or None if failed
    """
    limiter.wait()  # Apply rate limiting
    
    try:
        response = session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        if response.status_code == 429:
            logger.warning("Rate limit exceeded, increasing wait time")
            time.sleep(5)  # Additional wait on rate limit errors
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
    
    return None 