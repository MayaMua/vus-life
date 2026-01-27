"""
Disk cache decorator utilities.

Provides a decorator that caches function results to disk, with the ability
to skip caching None values (useful for API calls that fail).
"""

from functools import wraps
from pathlib import Path
from diskcache import Cache
from typing import Optional, Callable, Any


def disk_cache_skip_none(cache_dir: str, tag: Optional[str] = None):
    """
    Decorator that caches function results to disk, but skips caching None values.
    
    This is useful for API calls where None indicates a failure - we want to
    retry failures on subsequent runs rather than returning cached None.
    
    Args:
        cache_dir: Directory path for the cache storage
        tag: Optional tag to namespace the cache keys (uses function module + name by default)
    
    Returns:
        Decorator function
    
    Example:
        @disk_cache_skip_none("data_local/.cache/my_api")
        def fetch_data(key):
            result = api_call(key)
            return result  # If None, won't be cached
    
    Usage:
        # First call - calls function and caches result (if not None)
        result = fetch_data("key1")
        
        # Second call - returns cached result if available
        result = fetch_data("key1")  # Instant!
        
        # If first call returned None, second call will retry the function
    """
    # Ensure cache directory exists
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize cache
    cache = Cache(str(cache_path))
    
    def decorator(func: Callable) -> Callable:
        # Create cache key prefix using tag or function name
        cache_tag = tag or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function arguments
            # Use both args and kwargs to create a unique key
            cache_key = (cache_tag, args, tuple(sorted(kwargs.items())))
            
            # Check if result is in cache
            if cache_key in cache:
                return cache[cache_key]
            
            # Not in cache, call the function
            result = func(*args, **kwargs)
            
            # Only cache non-None results
            if result is not None:
                cache[cache_key] = result
            
            return result
        
        # Attach cache instance to wrapper for inspection/management
        wrapper._cache = cache
        wrapper._cache_dir = cache_dir
        
        return wrapper
    
    return decorator


def clear_function_cache(func: Callable) -> tuple[bool, str]:
    """
    Clear the cache for a specific decorated function.
    
    Args:
        func: The decorated function
    
    Returns:
        Tuple of (success, message)
    
    Example:
        @disk_cache_skip_none("data/.cache/api")
        def fetch_data(key):
            return api_call(key)
        
        # Clear this function's cache
        success, msg = clear_function_cache(fetch_data)
    """
    if not hasattr(func, '_cache'):
        return False, "Function is not decorated with disk_cache_skip_none"
    
    try:
        cache = func._cache
        initial_size = len(cache)
        cache.clear()
        return True, f"Cleared {initial_size} items from cache"
    except Exception as e:
        return False, f"Error clearing cache: {e}"


def get_cache_stats(func: Callable) -> dict:
    """
    Get statistics about a function's cache.
    
    Args:
        func: The decorated function
    
    Returns:
        Dictionary with cache statistics
    
    Example:
        @disk_cache_skip_none("data/.cache/api")
        def fetch_data(key):
            return api_call(key)
        
        stats = get_cache_stats(fetch_data)
        print(f"Cache has {stats['size']} entries")
    """
    if not hasattr(func, '_cache'):
        return {'error': 'Function is not decorated with disk_cache_skip_none'}
    
    try:
        cache = func._cache
        cache_dir = func._cache_dir
        
        return {
            'location': cache_dir,
            'size': len(cache),
            'disk_usage_mb': cache.volume() / (1024 * 1024),
        }
    except Exception as e:
        return {'error': str(e)}


# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Example: API function that sometimes fails
    @disk_cache_skip_none("data_local/.cache/test_api")
    def mock_api_call(key: str) -> Optional[str]:
        """Simulates an API call that might fail."""
        print(f"  [API CALL] Fetching data for key: {key}")
        time.sleep(0.1)  # Simulate network delay
        
        # Simulate failures for certain keys
        if key.startswith("fail_"):
            print(f"  [API CALL] Failed for key: {key}")
            return None
        
        return f"data_for_{key}"
    
    print("Disk Cache Decorator Test")
    print("=" * 60)
    
    # Test 1: Successful call (should be cached)
    print("\n1. First call (success) - should hit API and cache:")
    result1 = mock_api_call("test_key")
    print(f"   Result: {result1}")
    
    print("\n2. Second call (success) - should use cache:")
    result2 = mock_api_call("test_key")
    print(f"   Result: {result2}")
    
    # Test 2: Failed call (should NOT be cached)
    print("\n3. First call (failure) - should hit API, NOT cache:")
    result3 = mock_api_call("fail_key")
    print(f"   Result: {result3}")
    
    print("\n4. Second call (failure) - should retry API:")
    result4 = mock_api_call("fail_key")
    print(f"   Result: {result4}")
    
    # Test 3: Cache stats
    print("\n5. Cache statistics:")
    stats = get_cache_stats(mock_api_call)
    print(f"   Location: {stats['location']}")
    print(f"   Entries: {stats['size']}")
    print(f"   Disk usage: {stats['disk_usage_mb']:.4f} MB")
    
    # Test 4: Clear cache
    print("\n6. Clearing cache:")
    success, message = clear_function_cache(mock_api_call)
    print(f"   {message}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
