"""Performance optimization utilities

Provides caching and fast parsing utilities for improved application performance.
"""

from datetime import datetime
import pandas as pd

# Configuration caching
_config_cache = {}


def cache_config(path: str, config):
    """Cache parsed config to avoid re-parsing YAML

    Args:
        path: Path to config file
        config: Parsed configuration object

    Returns:
        The config object (for convenience)
    """
    _config_cache[path] = config
    return config


def get_cached_config(path: str):
    """Get cached config or None

    Args:
        path: Path to config file

    Returns:
        Cached config object or None if not cached
    """
    return _config_cache.get(path)


def clear_config_cache():
    """Clear configuration cache"""
    _config_cache.clear()


def parse_datetime_optimized(date_str: str, time_str: str) -> pd.Timestamp:
    """Parse datetime with format hints (faster than errors='coerce')

    Tries common format first, falls back to flexible parsing.

    Args:
        date_str: Date string (e.g., "2025.11.02")
        time_str: Time string (e.g., "06:30:15")

    Returns:
        Parsed timestamp or NaT if parsing fails
    """
    try:
        # Assume common format YYYY.MM.DD HH:MM:SS (fast path)
        return pd.to_datetime(f"{date_str} {time_str}", format='%Y.%m.%d %H:%M:%S')
    except:
        # Fallback to flexible parsing (slower but handles variations)
        try:
            return pd.to_datetime(f"{date_str} {time_str}")
        except:
            return pd.NaT
